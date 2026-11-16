import csv
import io
import logging
import secrets
import time
import uuid
from typing import Annotated
from fastapi import Body, Depends, FastAPI, HTTPException, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import delete, func, select, text, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.middleware.trustedhost import TrustedHostMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from .config import settings
from .db import get_db
from .domain import calculate
from .models import Movement, Observation, Product, Session as AuthSession, User
from .schemas import ForecastInput, LegacyProduct, Login, MovementInput, ObservationInput, ProductInput, ProductUpdate
from .security import COOKIE, DUMMY_HASH, current_user, passwords, throttle, token_hash

config = settings()
app = FastAPI(
    title="Inventory DSS API", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json", redoc_url=None
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=config.allowed_hosts.split(","))
DB = Annotated[Session, Depends(get_db)]
Account = Annotated[User, Depends(current_user)]
Year = Annotated[int, Query(ge=1900, le=2200)]
Factor = Annotated[float, Query(ge=0.5, le=2, allow_inf_nan=False)]


def error(status, message, request, details=None, headers=None):
    return JSONResponse(
        status_code=status,
        content={
            "error": {"message": message, "details": details, "request_id": getattr(request.state, "request_id", "")}
        },
        headers=headers,
    )


@app.middleware("http")
async def boundary(request: Request, call_next):
    request.state.request_id = str(uuid.uuid4())
    # Same-origin JSON writes + custom header prevent cross-site form/CSRF requests.
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        if request.headers.get("origin") != config.app_origin or request.headers.get("x-csrf-protection") != "1":
            return error(403, "Origine della richiesta non autorizzata", request)
    length = request.headers.get("content-length", "0")
    if not length.isdigit() or int(length) > 1_048_576:
        return error(413, "La richiesta supera il limite di 1 MB", request)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request.state.request_id
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.exception_handler(StarletteHTTPException)
async def http_error(request, exc):
    return error(exc.status_code, str(exc.detail), request, headers=exc.headers)


@app.exception_handler(RequestValidationError)
async def invalid(request, exc):
    # Never echo submitted passwords, tokens or complete input objects.
    details = [{"field": ".".join(map(str, e["loc"])), "message": e["msg"]} for e in exc.errors()]
    return error(422, "Controlla i dati inseriti", request, details)


@app.exception_handler(IntegrityError)
async def conflict(request, exc):
    return error(409, "Dati già presenti o modificati. Aggiorna la pagina e riprova.", request)


@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    logging.error("Database failure: %s request=%s", type(exc).__name__, request.state.request_id)
    return error(503, "Archivio temporaneamente non disponibile", request)


@app.exception_handler(Exception)
async def unexpected(request, exc):
    logging.error("Unhandled failure: %s request=%s", type(exc).__name__, request.state.request_id)
    return error(500, "Errore inatteso. Riprova o contatta l'assistenza.", request)


@app.get("/api/health")
def health(db: DB):
    db.execute(text("SELECT 1"))
    db.execute(select(User.id).limit(1))
    return {"status": "ok"}


@app.post("/api/v1/auth/login")
def login(data: Login, request: Request, response: Response, db: DB):
    email = data.email.strip().lower()
    # The reverse proxy must not expose the API publicly; do not trust arbitrary X-Forwarded-For.
    throttle(db, "ip:" + (request.client.host if request.client else "unknown"), 60)
    throttle(db, "email:" + email, 10)
    user = db.scalar(select(User).where(User.email == email))
    valid = passwords.verify(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid:
        raise HTTPException(401, "Email o password non corrette")
    db.execute(delete(AuthSession).where(AuthSession.expires_at <= time.time()))
    token = secrets.token_urlsafe(48)
    duration = config.session_hours * 3600
    db.add(AuthSession(token_hash=token_hash(token), user_id=user.id, expires_at=time.time() + duration))
    db.commit()
    response.set_cookie(
        COOKIE, token, max_age=duration, httponly=True, secure=config.app_env == "production", samesite="lax", path="/"
    )
    return {"email": user.email}


@app.get("/api/v1/auth/me")
def me(user: Account):
    return {"email": user.email}


@app.post("/api/v1/auth/logout", status_code=204)
def logout(request: Request, response: Response, db: DB):
    db.execute(delete(AuthSession).where(AuthSession.token_hash == token_hash(request.cookies.get(COOKIE, ""))))
    db.commit()
    response.delete_cookie(COOKIE, path="/", secure=config.app_env == "production", httponly=True, samesite="lax")


def owned(db, user, product_id):
    product = db.scalar(select(Product).where(Product.id == product_id, Product.user_id == user.id))
    if product is None:
        raise HTTPException(404, "Articolo non trovato")
    return product


def observation_data(observation):
    fields = ("year", "annual_demand", "order_cost", "holding_cost", "lead_time_days", "safety_stock", "version")
    return {key: getattr(observation, key) for key in fields}


def forecast(observation, factor):
    return calculate(
        observation.annual_demand,
        observation.order_cost,
        observation.holding_cost,
        observation.lead_time_days,
        observation.safety_stock,
        factor,
    ).to_dict()


def product_data(product, observation=None, factor=1):
    data = {key: getattr(product, key) for key in ("id", "sku", "name", "stock", "stock_known", "version", "archived")}
    data["observation"] = observation_data(observation) if observation else None
    data["forecast"] = forecast(observation, factor) if observation else None
    data["needs_reorder"] = bool(
        product.stock_known and data["forecast"] and product.stock <= data["forecast"]["punto_riordino"]
    )
    return data


@app.post("/api/v1/forecasts/preview")
def preview(data: ForecastInput, user: Account, factor: Factor = 1):
    return calculate(**data.model_dump(), seasonality=factor).to_dict()


@app.get("/api/v1/products")
def products(
    db: DB,
    user: Account,
    year: Year,
    factor: Factor = 1,
    q: str = Query("", max_length=100),
    archived: bool = False,
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
):
    filters = [Product.user_id == user.id, Product.archived == archived]
    if q.strip():
        # Escape LIKE wildcards; all values remain bound SQL parameters.
        term = q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        filters.append((Product.sku.ilike(f"%{term}%", escape="\\")) | (Product.name.ilike(f"%{term}%", escape="\\")))
    total = db.scalar(select(func.count()).select_from(Product).where(*filters))
    rows = db.execute(
        select(Product, Observation)
        .outerjoin(Observation, (Observation.product_id == Product.id) & (Observation.year == year))
        .where(*filters)
        .order_by(Product.sku, Product.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return {"items": [product_data(p, o, factor) for p, o in rows], "total": total, "offset": offset, "limit": limit}


@app.post("/api/v1/products", status_code=201)
def create_product(data: ProductInput, db: DB, user: Account):
    product = Product(**data.model_dump(), user_id=user.id)
    db.add(product)
    db.flush()
    db.add(
        Movement(
            product_id=product.id,
            user_id=user.id,
            delta=product.stock,
            resulting_stock=product.stock,
            reason="Giacenza iniziale",
            idempotency_key=str(uuid.uuid4()),
        )
    )
    db.commit()
    return product_data(product)


@app.patch("/api/v1/products/{product_id}")
def edit_product(product_id: str, data: ProductUpdate, db: DB, user: Account):
    owned(db, user, product_id)
    result = db.execute(
        update(Product)
        .where(Product.id == product_id, Product.user_id == user.id, Product.version == data.version)
        .values(name=data.name, archived=data.archived, version=Product.version + 1)
    )
    if not result.rowcount:
        raise HTTPException(409, "Articolo modificato da un'altra sessione. Aggiorna e riprova.")
    db.commit()
    db.expire_all()
    return product_data(owned(db, user, product_id))


@app.get("/api/v1/products/{product_id}/observations")
def observations(product_id: str, db: DB, user: Account):
    owned(db, user, product_id)
    rows = db.scalars(
        select(Observation).where(Observation.product_id == product_id).order_by(Observation.year.desc())
    ).all()
    return [dict(**observation_data(o), forecast=forecast(o, 1)) for o in rows]


@app.put("/api/v1/products/{product_id}/observations/{year}")
def save_observation(product_id: str, year: int, data: ObservationInput, db: DB, user: Account):
    if not 1900 <= year <= 2200:
        raise HTTPException(422, "Anno ammesso da 1900 a 2200")
    product = owned(db, user, product_id)
    if product.archived:
        raise HTTPException(409, "Ripristina l'articolo prima di modificarlo")
    payload = data.model_dump(exclude={"version"})
    if data.version == 0:
        db.add(Observation(product_id=product_id, year=year, **payload))
    else:
        result = db.execute(
            update(Observation)
            .where(Observation.product_id == product_id, Observation.year == year, Observation.version == data.version)
            .values(**payload, version=Observation.version + 1)
        )
        if not result.rowcount:
            raise HTTPException(409, "Rilevazione modificata. Aggiorna e riprova.")
    db.commit()
    db.expire_all()
    observation = db.scalar(select(Observation).where(Observation.product_id == product_id, Observation.year == year))
    return product_data(owned(db, user, product_id), observation)


@app.post("/api/v1/products/{product_id}/movements", status_code=201)
def move(product_id: str, data: MovementInput, db: DB, user: Account):
    product = owned(db, user, product_id)
    previous = db.scalar(
        select(Movement).where(Movement.user_id == user.id, Movement.idempotency_key == data.idempotency_key)
    )
    if previous:
        if previous.product_id != product_id or previous.delta != data.delta or previous.reason != data.reason:
            raise HTTPException(409, "Identificativo movimento già usato per altri dati")
        return {"id": previous.id, "stock": previous.resulting_stock, "replayed": True}
    if product.archived:
        raise HTTPException(409, "Ripristina l'articolo prima di registrare movimenti")
    result = db.execute(
        update(Product)
        .where(
            Product.id == product_id,
            Product.user_id == user.id,
            Product.version == data.version,
            Product.stock + data.delta >= 0,
            Product.stock + data.delta <= 1_000_000_000,
        )
        .values(stock=Product.stock + data.delta, stock_known=True, version=Product.version + 1)
    )
    if not result.rowcount:
        raise HTTPException(409, "Giacenza insufficiente o modificata. Aggiorna e riprova.")
    db.refresh(product)
    movement = Movement(
        product_id=product_id,
        user_id=user.id,
        delta=data.delta,
        resulting_stock=product.stock,
        reason=data.reason,
        idempotency_key=data.idempotency_key,
    )
    db.add(movement)
    db.commit()
    return {"id": movement.id, "stock": product.stock, "replayed": False}


@app.get("/api/v1/products/{product_id}/movements")
def movements(
    product_id: str, db: DB, user: Account, offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=500)
):
    owned(db, user, product_id)
    rows = db.scalars(
        select(Movement)
        .where(Movement.product_id == product_id, Movement.user_id == user.id)
        .order_by(Movement.created_at.desc(), Movement.id)
        .offset(offset)
        .limit(limit)
    ).all()
    return [{key: getattr(m, key) for key in ("id", "delta", "resulting_stock", "reason", "created_at")} for m in rows]


@app.post("/api/v1/import/legacy", status_code=201)
def import_legacy(data: Annotated[dict[str, LegacyProduct], Body()], db: DB, user: Account):
    if not 1 <= len(data) <= 1000 or sum(len(p.Anni) for p in data.values()) > 10000:
        raise HTTPException(422, "Importa da 1 a 1000 articoli, massimo 10000 rilevazioni")
    # Validate the whole archive before any insert. Duplicate SKUs abort the transaction.
    try:
        validated = [(ProductInput(sku=sku, name=p.Nome_Articolo), p) for sku, p in data.items()]
    except ValidationError:
        raise HTTPException(
            422, "Codice articolo non valido: usa lettere, numeri, punti, trattini o underscore"
        ) from None
    count = 0
    for product_input, legacy in validated:
        product = Product(user_id=user.id, sku=product_input.sku, name=product_input.name, stock=0, stock_known=False)
        db.add(product)
        db.flush()
        for year, values in legacy.Anni.items():
            db.add(Observation(product_id=product.id, year=int(year), **values.forecast().model_dump()))
            count += 1
    db.commit()
    return {
        "products": len(data),
        "observations": count,
        "message": "Archivio importato. Inserisci le giacenze: il file originale non le contiene.",
    }


@app.get("/api/v1/export/legacy")
def export_legacy(db: DB, user: Account):
    rows = db.execute(
        select(Product, Observation)
        .join(Observation, Observation.product_id == Product.id)
        .where(Product.user_id == user.id, Product.archived.is_(False))
        .order_by(Product.sku, Observation.year)
    ).all()
    archive = {}
    for p, o in rows:
        entry = archive.setdefault(p.sku, {"Nome_Articolo": p.name, "Anni": {}})
        f = forecast(o, 1)
        entry["Anni"][str(o.year)] = {
            "domanda_annuale": o.annual_demand,
            "costo_ordine": o.order_cost,
            "costo_mantenimento": o.holding_cost,
            "lead_time_giorni": o.lead_time_days,
            **{
                k: f[k]
                for k in ("domanda_media_mese", "domanda_giornaliera", "scorta_sicurezza", "eoq", "punto_riordino")
            },
        }
    return JSONResponse(archive, headers={"Content-Disposition": 'attachment; filename="Dizionario-web.json"'})


def csv_safe(value):
    value = str(value)
    return (
        "'" + value
        if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n"))
        else value
    )


@app.get("/api/v1/export/csv")
def export_csv(db: DB, user: Account, year: Year, factor: Factor = 1):
    rows = db.execute(
        select(Product, Observation)
        .outerjoin(Observation, (Observation.product_id == Product.id) & (Observation.year == year))
        .where(Product.user_id == user.id, Product.archived.is_(False))
        .order_by(Product.sku)
    ).all()
    output = io.StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(["SKU", "Articolo", "Anno", "Giacenza", "EOQ", "ROP", "Da riordinare", "Fattore"])
    for p, o in rows:
        f = forecast(o, factor) if o else None
        writer.writerow(
            [
                csv_safe(p.sku),
                csv_safe(p.name),
                year,
                p.stock if p.stock_known else "Da rilevare",
                f["eoq"] if f else "",
                f["punto_riordino"] if f else "",
                "Sì" if f and p.stock_known and p.stock <= f["punto_riordino"] else "",
                factor,
            ]
        )
    return Response(
        "\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="magazzino-{year}.csv"'},
    )

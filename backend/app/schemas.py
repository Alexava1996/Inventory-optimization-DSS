from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False, str_strip_whitespace=True)


class Login(StrictModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("password", mode="before")
    @classmethod
    def preserve_password(cls, value):
        # Password whitespace is significant; override global string stripping below.
        return value

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class ForecastInput(StrictModel):
    annual_demand: float = Field(ge=0, le=1_000_000_000, strict=True)
    order_cost: float = Field(gt=0, le=100_000_000, strict=True)
    holding_cost: float = Field(gt=0, le=100_000_000, strict=True)
    lead_time_days: int = Field(ge=0, le=3650, strict=True)
    safety_stock: float | None = Field(default=None, ge=0, le=1_000_000_000, strict=True)


class ObservationInput(ForecastInput):
    version: int = Field(default=0, ge=0, strict=True)


class ProductInput(StrictModel):
    sku: str = Field(pattern=r"^[A-Za-z0-9_.-]{1,40}$")
    name: str = Field(min_length=1, max_length=160)
    stock: int = Field(default=0, ge=0, le=1_000_000_000, strict=True)


class ProductUpdate(StrictModel):
    name: str = Field(min_length=1, max_length=160)
    archived: bool = Field(strict=True)
    version: int = Field(ge=1, strict=True)


class MovementInput(StrictModel):
    delta: int = Field(ge=-1_000_000_000, le=1_000_000_000, strict=True)
    reason: str = Field(min_length=3, max_length=240)
    version: int = Field(ge=1, strict=True)
    idempotency_key: str = Field(pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


class LegacyYear(StrictModel):
    domanda_annuale: float = Field(ge=0, le=1_000_000_000)
    costo_ordine: float = Field(gt=0, le=100_000_000)
    costo_mantenimento: float = Field(gt=0, le=100_000_000)
    lead_time_giorni: int = Field(ge=0, le=3650)
    scorta_sicurezza: float | None = Field(default=None, ge=0, le=1_000_000_000)
    domanda_media_mese: float | None = None
    domanda_giornaliera: float | None = None
    eoq: float | None = None
    punto_riordino: float | None = None

    def forecast(self):
        return ForecastInput(
            annual_demand=self.domanda_annuale,
            order_cost=self.costo_ordine,
            holding_cost=self.costo_mantenimento,
            lead_time_days=self.lead_time_giorni,
            safety_stock=self.scorta_sicurezza,
        )


class LegacyProduct(StrictModel):
    Nome_Articolo: str = Field(min_length=1, max_length=160)
    Anni: dict[str, LegacyYear] = Field(min_length=1, max_length=301)

    @field_validator("Anni")
    @classmethod
    def years(cls, value):
        if any(
            not key.isascii() or not key.isdigit() or len(key) != 4 or not 1900 <= int(key) <= 2200 for key in value
        ):
            raise ValueError("Anni ammessi: 1900-2200")
        return value

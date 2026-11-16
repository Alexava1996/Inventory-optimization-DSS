"""Core DSS estratto da LottoEconomicoRop.py, calcola_valori (righe 216-245).

Stesse formule, ordine delle operazioni e arrotondamento Python del desktop.
Il core non importa né GUI, né HTTP, né database. Il file originale resta intatto.
"""

from dataclasses import asdict, dataclass
from math import isfinite, sqrt


@dataclass(frozen=True)
class Forecast:
    domanda_attiva: float
    domanda_media_mese: float
    domanda_giornaliera: float
    scorta_sicurezza: float
    eoq: float
    punto_riordino: float
    numero_ordini: float

    def to_dict(self):
        return asdict(self)


def calculate(
    annual_demand: float,
    order_cost: float,
    holding_cost: float,
    lead_time_days: int,
    safety_stock: float | None = None,
    seasonality: float = 1.0,
) -> Forecast:
    values = (annual_demand, order_cost, holding_cost, lead_time_days, seasonality)
    if not all(isfinite(x) for x in values):
        raise ValueError("I valori devono essere finiti")
    if annual_demand < 0 or order_cost <= 0 or holding_cost <= 0 or lead_time_days < 0:
        raise ValueError("Domanda e tempi non negativi; costi strettamente positivi")
    if not 0.5 <= seasonality <= 2:
        raise ValueError("Stagionalità ammessa da 0.5 a 2")
    if safety_stock is not None and (not isfinite(safety_stock) or safety_stock < 0):
        raise ValueError("Scorta di sicurezza non valida")
    demand = annual_demand * seasonality
    daily = demand / 365
    safety = round(lead_time_days * daily, 0) if safety_stock is None else safety_stock
    eoq = sqrt((2 * demand * order_cost) / holding_cost)
    return Forecast(
        demand,
        round(demand / 12, 2),
        round(daily, 2),
        safety,
        round(eoq, 2),
        round(daily * lead_time_days + safety, 2),
        round(demand / eoq, 2) if eoq else 0,
    )

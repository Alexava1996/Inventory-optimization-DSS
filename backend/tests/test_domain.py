import ast
import json
import math
from pathlib import Path
import pytest
from app.domain import calculate

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = json.loads((ROOT / "Dizionario.txt").read_text())
CASES = [(sku, year, values) for sku, p in ARCHIVE.items() for year, values in p["Anni"].items()]


@pytest.mark.parametrize("sku,year,values", CASES)
def test_matches_every_saved_legacy_record(sku, year, values):
    result = calculate(
        values["domanda_annuale"],
        values["costo_ordine"],
        values["costo_mantenimento"],
        values["lead_time_giorni"],
        values["scorta_sicurezza"],
    ).to_dict()
    for field in ("domanda_media_mese", "domanda_giornaliera", "eoq", "punto_riordino", "scorta_sicurezza"):
        assert result[field] == values[field], (sku, year, field)


@pytest.mark.parametrize(
    "demand,order,holding,lead", [(6100, 200, 210, 30), (6200, 63, 0.6, 15), (365, 7, 2, 1), (500, 10, 3, 12)]
)
def test_matches_actual_legacy_callback_without_loading_tkinter(demand, order, holding, lead):
    tree = ast.parse((ROOT / "LottoEconomicoRop.py").read_text())
    callback = next(
        node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == "calcola_valori"
    )

    class Var:
        def __init__(self, value=""):
            self.value = value

        def get(self):
            return str(self.value)

        def set(self, value):
            self.value = value

    namespace = {"math": math}
    namespace.update(
        {
            key: Var()
            for key in (
                "domanda_mese_var",
                "domanda_giorno_var",
                "scorta_sicurezza_var",
                "eoq_var",
                "num_ordini_var",
                "punto_riordino_var",
            )
        }
    )
    namespace.update(
        domanda_annuale_var=Var(demand),
        costo_ordine_var=Var(order),
        costo_mantenimento_var=Var(holding),
        lead_time_var=Var(lead),
    )
    exec(compile(ast.Module(body=[callback], type_ignores=[]), "<legacy-callback>", "exec"), namespace)
    namespace["calcola_valori"]()
    actual = calculate(demand, order, holding, lead)
    for field, variable in [
        ("eoq", "eoq_var"),
        ("punto_riordino", "punto_riordino_var"),
        ("domanda_giornaliera", "domanda_giorno_var"),
        ("numero_ordini", "num_ordini_var"),
    ]:
        assert getattr(actual, field) == float(namespace[variable].get())


def test_zero_demand_and_seasonal_safety_behavior():
    assert calculate(0, 50, 5, 0).eoq == 0
    assert calculate(3650, 50, 5, 10, seasonality=2).scorta_sicurezza == 200
    assert calculate(3650, 50, 5, 10, 80, 2).scorta_sicurezza == 80


@pytest.mark.parametrize(
    "args",
    [(1, 1, 0, 1), (-1, 1, 1, 1), (1, 1, 1, -1), (float("nan"), 1, 1, 1), (1, 1, 1, 1, -2), (1, 1, 1, 1, None, 3)],
)
def test_rejects_invalid_inputs(args):
    with pytest.raises(ValueError):
        calculate(*args)

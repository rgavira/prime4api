"""
Test rápido de curvas de capacidad para datasheets.
Ejecutar desde la raíz del proyecto:
    python -m tests.test_curves
Se abre el HTML resultante directamente en el navegador.
"""
import os
import webbrowser
import threading
import http.server
import socket
from io import BytesIO

from app.utils.yaml_utils import load_yaml_source
from app.services.datasheet_evaluator_service import DatasheetEvaluatorService
from app.services.capacity_curve_service import CapacityCurveService
from app.utils.plotly_renderer import render_multi_curve_html
from app.utils.time_utils import parse_time_string_to_duration, select_best_time_unit
from app.schemas.datasheet import EvaluateDatasheetRequest

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURACIÓN — cambia estos valores para probar distintos casos
# ─────────────────────────────────────────────────────────────────────────────

DATASHEET_PATH = "http://194.62.96.89/static/datasheets/uploaded/sendgrid-rapidapi-2026/2026-04-19.yaml"
PLAN_NAME      = None         # None → todos los planes
ENDPOINT_PATH  = None   # None → todos los endpoints
ALIAS          = None

TIME_INTERVAL  = "1day"          # e.g. "1h", "1day", "1month"
CURVE_TYPE     = "inflection"   # "accumulated" | "inflection"

CAPACITY_UNIT           = None   # None → todas las dimensiones
CAPACITY_REQUEST_FACTOR = None   # None → worst/avg/best; int → fijo

# ─────────────────────────────────────────────────────────────────────────────

evaluator_service = DatasheetEvaluatorService()
curve_service     = CapacityCurveService()


def _crf_dict(capacity_unit, capacity_request_factor):
    if capacity_unit and capacity_request_factor is not None:
        return {capacity_unit: capacity_request_factor}
    return None


def _time_axis_params(time_interval: str):
    td   = parse_time_string_to_duration(time_interval)
    best = select_best_time_unit(td.to_milliseconds())
    return best.unit.value, best.unit.to_milliseconds()


def _get_curve_points(sc: dict, time_interval: str, curve_type: str):
    rates  = sc["rates"]  or None
    quotas = sc["quotas"] or None
    if curve_type == "accumulated":
        return curve_service.get_accumulated_capacity_curve(time_interval, rates, quotas)
    return curve_service.get_inflection_point_capacity_curve(time_interval, rates, quotas)


def _serve_html(html: str, title: str):
    html_bytes = html.encode("utf-8")

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html_bytes)))
            self.end_headers()
            self.wfile.write(html_bytes)

        def log_message(self, fmt, *args):
            pass  # silence request logs

    with socket.socket() as s:
        s.bind(("", 0))
        port = s.getsockname()[1]

    server = http.server.HTTPServer(("", port), _Handler)
    url = f"http://localhost:{port}"
    print(f"\nServing '{title}' at {url}  (Ctrl+C to stop)")
    webbrowser.open(url)
    server.serve_forever()


def run():
    yaml_data = load_yaml_source(DATASHEET_PATH)

    nav_request = EvaluateDatasheetRequest(
        datasheet_source=DATASHEET_PATH,
        plan_name=PLAN_NAME,
        endpoint_path=ENDPOINT_PATH,
        alias=ALIAS,
        operation="__nav__",
        operation_params={},
    )

    scenarios = evaluator_service.get_curve_scenarios(
        yaml_data,
        nav_request,
        capacity_unit=CAPACITY_UNIT,
        capacity_request_factor=_crf_dict(CAPACITY_UNIT, CAPACITY_REQUEST_FACTOR),
    )

    print(f"Scenarios found: {len(scenarios)}")
    for sc in scenarios:
        print(f"  plan={sc['plan']} endpoint={sc['endpoint']} alias={sc['alias']} "
              f"dimension={sc['dimension']} crf={sc['crf']}")
        print(f"    rates={[(r.value, r.unit) for r in sc['rates']]}")
        print(f"    quotas={[(q.value, q.unit) for q in sc['quotas']]}")

    x_unit_label, x_scale_divisor = _time_axis_params(TIME_INTERVAL)

    series_list = []
    for sc in scenarios:
        try:
            pts = _get_curve_points(sc, TIME_INTERVAL, CURVE_TYPE)
            series_list.append({
                "dimension": sc["dimension"],
                "crf":       sc["crf"],
                "t_ms":      pts.t_ms,
                "capacity":  pts.capacity,
            })
            print(f"  OK: {sc['dimension']} CRF={sc['crf']} → {len(pts.t_ms)} points")
        except Exception as e:
            print(f"  SKIP: {sc['dimension']} CRF={sc['crf']} → {e}")

    if not series_list:
        print("No curves to render.")
        return

    title = f"{CURVE_TYPE.capitalize()} Capacity Curve — {TIME_INTERVAL}"
    html  = render_multi_curve_html(series_list, title, "hv" if CURVE_TYPE == "accumulated" else "linear",
                                    x_unit_label, x_scale_divisor)

    _serve_html(html, title)


if __name__ == "__main__":
    run()

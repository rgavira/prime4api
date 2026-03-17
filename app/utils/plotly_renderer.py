from typing import Literal

import plotly.graph_objects as go

from app.engine.plotters.curve_models import CapacityCurvePoints

LineShape = Literal["hv", "linear"]
# "hv"     → escalón (step function). Usar para accumulated_curve e inflection_point_curve.
# "linear" → línea recta entre puntos. Usar para normalized_inflection_curve.


def render_capacity_curve_html(
    points: CapacityCurvePoints,
    title: str,
    line_shape: LineShape,
    x_unit_label: str,
    x_scale_divisor: float,
) -> str:
    """
    Convierte CapacityCurvePoints en un HTML Plotly autocontenido.

    Parámetros:
      points          : puntos generados por cualquier plotter.
      title           : título del gráfico.
      line_shape      : "hv" para escalón, "linear" para recta.
      x_unit_label    : etiqueta del eje X, e.g. "h", "day", "min".
      x_scale_divisor : divisor para convertir t_ms al eje visual.
                        e.g. si x_unit_label="h", x_scale_divisor=3_600_000.
                        Calculado por el service usando select_best_time_unit().

    Retorna:
      str con HTML completo (full_html=True, plotlyjs via CDN).
      Apto para devolver directamente desde un endpoint FastAPI como text/html.
    """
    xs = [t / x_scale_divisor for t in points.t_ms]
    ys = points.capacity

    # Color de relleno semitransparente (verde)
    fill_color = "rgba(0, 128, 0, 0.2)"
    line_color = "green"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=xs,
        y=ys,
        mode="lines",
        line=dict(color=line_color, shape=line_shape, width=1.5),
        fill="tozeroy",
        fillcolor=fill_color,
        name="Capacity",
    ))

    fig.update_layout(
        title=title,
        xaxis_title=f"Time ({x_unit_label})",
        yaxis_title="Accumulated Capacity",
        legend_title="Curves",
        showlegend=True,
        template="plotly_white",
        width=1000,
        height=600,
    )

    return fig.to_html(full_html=True, include_plotlyjs="cdn")
import re
from typing import List, Optional, Union
import plotly.graph_objects as go
from Pricing4API.basic.bounded_rate import Rate, Quota, BoundedRate
from Pricing4API.ancillary.time_unit import TimeDuration, TimeUnit
from Pricing4API.ancillary.CapacityPlotHelper import CapacityPlotHelper
from matplotlib.colors import to_rgba
from Pricing4API.utils import parse_time_string_to_duration

def compare_rates_capacity(rates: List[Rate], time_interval: Union[str, TimeDuration], return_fig=False):
    """
    Compares the capacity curves of a list of rates, starting with the slowest.

    Args:
        rates (List[Rate]): List of rates to compare.
        time_interval (Union[str, TimeDuration]): The time interval for generating the curves.
        return_fig (bool, optional): Whether to return the figure. Defaults to False.
    """
    if isinstance(time_interval, str):
        time_interval = parse_time_string_to_duration(time_interval)

    # Sort rates by speed (slowest first)
    rates.sort(key=lambda rate: rate.consumption_period.to_milliseconds() / rate.consumption_unit, reverse=False)

    predefined_colors = ["green", "blue", "orange",  "red", "purple", "brown", "pink", "gray", "olive", "cyan"]

    if len(rates) > len(predefined_colors):
        raise ValueError("Not enough colors available for all rates.")

    fig = go.Figure()

    # Añadimos índice i para controlar el fill
    for i, (rate, color) in enumerate(zip(rates, predefined_colors)):
        debug_values = rate.show_capacity(time_interval, debug=True)
        times_ms, capacities = zip(*debug_values)
        original_times = [t / time_interval.unit.to_milliseconds() for t in times_ms]

        rgba_color = (
            f"rgba({','.join(map(str, [int(c * 255) for c in to_rgba(color)[:3]]))},0.2)"
        )

        # Solo se muestra la curva acumulada
        fig.add_trace(go.Scatter(
            x=original_times,
            y=capacities,
            mode='lines',
            line=dict(color=color, shape='hv', width=1.3),
            fill='tozeroy' if i == 0 else 'tonexty',
            fillcolor=rgba_color,
            name=f"Accumulated Rate ({rate.consumption_unit}/{rate.consumption_period})"
        ))

    # Configuración del diseño
    fig.update_layout(
        title="Accumulated Capacity",
        xaxis_title=f"Time ({time_interval.unit.value})",
        yaxis_title="Capacity",
        legend_title="Rates",  # Título de la leyenda
        showlegend=True,       # Aseguramos que la leyenda esté visible
        template="plotly_white",
        width=1000,
        height=600
    )

    if return_fig:
        return fig

    fig.show()


def compare_bounded_rates_capacity_inflection_points(
    bounded_rates: List[BoundedRate],
    time_interval: Union[str, TimeDuration],
    return_fig: bool = False
):
    """
    Compara las curvas de capacidad de una lista de BoundedRate,
    mostrando solo los puntos de inflexión.

    Args:
        bounded_rates: Lista de BoundedRate.
        time_interval: Tiempo total de simulación.
        return_fig: Si se debe devolver la figura.
    """
    if isinstance(time_interval, str):
        time_interval = parse_time_string_to_duration(time_interval)

    # Ordenar las tasas acotadas por velocidad
    #bounded_rates.sort(
    #    key=lambda br: br.rate.consumption_period.to_milliseconds() / br.rate.consumption_unit
    #)

    predefined_colors = ["green", "blue", "orange",  "red", "purple", "brown", "pink", "gray", "olive", "cyan"]

    if len(bounded_rates) > len(predefined_colors):
        raise ValueError("Not enough colors available.")

    fig = go.Figure()
    unit_ms = time_interval.unit.to_milliseconds()

    for i, (br, color) in enumerate(zip(bounded_rates, predefined_colors)):
        # Obtener los puntos de inflexión en modo debug
        inflection_points = br.show_capacity_from_inflection_points(time_interval, debug=True)

        x_vals = [t / unit_ms for t, _ in inflection_points]
        print(x_vals)
        print(unit_ms)
        capacities = [cap for _, cap in inflection_points]

        rgba = f"rgba({','.join(map(str, [int(c * 255) for c in to_rgba(color)[:3]]))},0.2)"
        legend_label = f"{br.rate.consumption_unit}/{br.rate.consumption_period}"

        tooltip_labels = [CapacityPlotHelper.format_time_tooltip((t * unit_ms)/1000) for t in x_vals]

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=capacities,
            customdata=tooltip_labels,
            hovertemplate="Time: %{customdata}<br>Capacity: %{y}<extra></extra>",
            mode='lines',
            line=dict(color=color, shape='linear', width=2),
            fill='tozeroy',
            fillcolor=rgba,
            name=legend_label
        ))

    fig.update_layout(
        title="Capacity Curve (Slopes Only)",
        xaxis_title=f"Time ({time_interval.unit.value})",
        yaxis_title="Accumulated Capacity",
        legend_title="Bounded Rates",
        template="plotly_white",
        width=900,
        height=500
    )

    if return_fig:
        return fig
    fig.show()



def compare_bounded_rates_capacity(
    bounded_rates: List[BoundedRate],
    time_interval: Union[str, TimeDuration],
    return_fig: bool = False
):
    """
    Compara las curvas de capacidad (acumulada vs. instantánea) de una lista de BoundedRate,
    empezando por la más lenta. Si el tiempo de simulación >= la cuota máxima y existen cuotas,
    permite alternar entre vista acumulada e instantánea.
    """
    if isinstance(time_interval, str):
        time_interval = parse_time_string_to_duration(time_interval)

    # ordenar de más lento a más rápido
    #bounded_rates.sort(
    #    key=lambda br: br.rate.consumption_period.to_milliseconds() / br.rate.consumption_unit
    #)

    # Colores predefinidos
    predefined_colors = ["green", "blue", "orange",  "red", "purple", "brown", "pink", "gray", "olive", "cyan"]
    if len(bounded_rates) > len(predefined_colors):
        raise ValueError("Not enough colors available for all bounded rates.")

    fig = go.Figure()
    unit_ms = time_interval.unit.to_milliseconds()
    sim_ms = int(time_interval.to_milliseconds())
    trace_idx = 0

    for br, color in zip(bounded_rates, predefined_colors):
        # Construir la leyenda personalizada
        rate_part = f"{br.rate.consumption_unit}/{br.rate.consumption_period}"
        legend_label = rate_part
        if len(br.limits) > 1:
            q = br.limits[-1]
            legend_label += f" ·{q.consumption_unit}/{q.consumption_period}"
        if getattr(br, "max_active_time", None):
            d = br.max_active_time
            legend_label += f" during {d.value}{d.unit.value}"

        rgba = f"rgba({','.join(map(str, [int(c*255) for c in to_rgba(color)[:3]]))},0.2)"

        # --- acumulada ---
        debug_acc = br.show_available_capacity_curve(time_interval, debug=True)
        times_acc, caps_acc = zip(*debug_acc)
        x_acc = [t / unit_ms for t in times_acc]

        fill_mode = "tozeroy" if trace_idx != 0 else "tonexty"
        fig.add_trace(go.Scatter(
            x=x_acc,
            y=list(caps_acc),
            mode='lines',
            line=dict(color=color, shape='hv', width=1.3),
            fill=fill_mode,
            fillcolor=rgba,
            name=legend_label,
            legendgroup=legend_label,
            showlegend=True,
            visible=True
        ))
        trace_idx += 1

        # --- instantánea (solo si hay cuota y el intervalo supera esa cuota) ---
        max_quota_ms = br.limits[-1].consumption_period.to_milliseconds()
        if len(br.limits) > 1 and sim_ms >= max_quota_ms:
            debug_inst = br.show_instantaneous_capacity_curve(time_interval, debug=True)
            times_inst, caps_inst = zip(*debug_inst)
            x_inst = [t / unit_ms for t in times_inst]

            fill_mode = "tozeroy" if trace_idx == 0 else "tonexty"
            fig.add_trace(go.Scattergl(
                x=x_inst,
                y=list(caps_inst),
                mode='lines',
                line=dict(color=color, shape='hv', width=1.3),
                fill=fill_mode,
                fillcolor=rgba,
                name=legend_label,
                legendgroup=legend_label,
                showlegend=False,
                visible=False
            ))
            trace_idx += 1

    # Botones solo si hay instantáneas
    #n_acc = sum("Accumulated" or True for _ in range(trace_idx))  # no los usamos aquí
    n_inst = sum(1 for tr in fig.data if tr.showlegend==False)

    if n_inst > 0:
        vis_acc = [tr.showlegend or tr.visible for tr in fig.data]
        vis_inst = [not v for v in vis_acc]
        fig.update_layout(
            updatemenus=[dict(
                type="buttons", direction="left",
                x=0.30, y=1.10, xanchor="left", yanchor="top",
                buttons=[
                    dict(
                        label="Accumulated",
                        method="update",
                        args=[{"visible": vis_acc}, {"title": "Accumulated Capacity"}]
                    ),
                    dict(
                        label="Instantaneous",
                        method="update",
                        args=[{"visible": vis_inst}, {"title": "Instantaneous Capacity"}]
                    )
                ]
            )]
        )

    # Layout final
    fig.update_layout(
        title="Capacity Curves",
        xaxis_title=f"Time ({time_interval.unit.value})",
        yaxis_title="Capacity",
        legend_title="Bounded Rates",
        template="plotly_white",
        width=1200,  # Aumentar el ancho
        height=700,  # Aumentar la altura
        margin=dict(l=60, r=60, t=80, b=60),  # Márgenes ajustados
        legend=dict(
            x=1.02,  # Mover la leyenda ligeramente fuera del gráfico
            y=1,
            xanchor="left",
            yanchor="top"
        )
    )

    if return_fig:
        return fig
    fig.show()


def show_line(
    fig: go.Figure,
    *,
    x: Optional[str] = None,           # e.g. "30min", "0.5h", "120s"
    y: Optional[float] = None,         # valor numérico de capacidad
    color: str = "red",                # color de la línea
    dash: str = "dash",                # "solid" | "dash" | "dot" | "dashdot"
    width: int = 1,                    # ancho de la línea
    opacity: float = 1.0,              # 0.0–1.0
    layer: str = "above",              # "above" o "below"
    annotation_text: Optional[str] = None,     # texto de la anotación
    annotation_position: Optional[str] = None,  # "top left", "bottom right", …
    annotation_font: Optional[dict] = None,      # p.ej. {"size":12,"color":"black"}
    annotation_align: Optional[str] = None       # "left" | "center" | "right"
) -> None:
    # 1. extraemos unidad del eje X
    title = fig.layout.xaxis.title.text or ""
    m = re.search(r"\((ms|s|min|h|day|week|month|year)\)", title)
    tgt = TimeUnit(m.group(1)) if m else TimeUnit.SECOND

    # 2. línea vertical
    if x is not None:
        td = parse_time_string_to_duration(x)
        td_conv = td.to_desired_time_unit(tgt)
        fig.add_vline(
            x=td_conv.value,
            line=dict(color=color, dash=dash, width=width),
            opacity=opacity,
            layer=layer,
            annotation_text=annotation_text,
            annotation_position=annotation_position,
            annotation_font=annotation_font,
            annotation_align=annotation_align
        )

    # 3. línea horizontal
    if y is not None:
        fig.add_hline(
            y=y,
            line=dict(color=color, dash=dash, width=width),
            opacity=opacity,
            layer=layer,
            annotation_text=annotation_text,
            annotation_position=annotation_position,
            annotation_font=annotation_font,
            annotation_align=annotation_align
        )
        

def update_legend_names(fig: go.Figure, legend_names: List[str]) -> None:
    """
    Actualiza dinámicamente los nombres de leyenda de un Figure de Plotly
    agrupando trazas de 1 o 2 (acumulada + opcional instantánea) según el
    número de bounded rates y asignando los nombres en el orden de legend_names.

    Args:
        fig (go.Figure): La figura con las trazas ya añadidas.
        legend_names (List[str]): Lista de nombres de leyenda, uno por bounded rate.
    """
    traces = fig.data
    rate_idx = 0
    i = 0

    # Por cada bounded rate esperamos 1 ó 2 trazas: accumulated y opcional instantaneous
    while i < len(traces) and rate_idx < len(legend_names):
        name = legend_names[rate_idx]

        # Si la siguiente traza es instantánea, renombramos el par
        if i + 1 < len(traces) and traces[i+1].name.startswith("Instantaneous"):
            traces[i].name = name
            traces[i].legendgroup = name
            traces[i+1].name = name
            traces[i+1].legendgroup = name
            i += 2
        else:
            # Solo acumulada
            traces[i].name = name
            traces[i].legendgroup = name
            i += 1

        rate_idx += 1
        
def update_legend(fig: go.Figure, legend_title: str) -> None:
    """
    Updates the legend title of the figure.

    Args:
        fig (go.Figure): The Plotly figure to update.
        legend_title (str): The new title for the legend.
    """
    fig.update_layout(legend_title=dict(text=legend_title))


def update_yaxis(fig: go.Figure, yaxis_title: str) -> None:
    """
    Updates the y-axis title of the figure.

    Args:
        fig (go.Figure): The Plotly figure to update.
        yaxis_title (str): The new title for the y-axis.
    """
    fig.update_layout(yaxis_title=yaxis_title)


def update_title(fig: go.Figure, title: str) -> None:
    """
    Updates the title of the figure.

    Args:
        fig (go.Figure): The Plotly figure to update.
        title (str): The new title for the figure.
    """
    fig.update_layout(title=title)
    
if __name__ == "__main__":
    br1 = BoundedRate(Rate(1, "2s"), Quota(1800, "1h"))
    br2 = BoundedRate(
        Rate(1, "2s"),
        [
            Quota(18,   "60s"),
            Quota(48,  "300s"),
            Quota(1800, "1h")
        ]
    )
    
    print(br2.quota_exhaustion_threshold())



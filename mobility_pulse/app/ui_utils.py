"""Utilidades de UI para el dashboard de Streamlit."""

from __future__ import annotations

from pathlib import Path
import pandas as pd
import plotly.graph_objects as go

# Tema Plotly personalizado
PLOTLY_THEME = {
    'layout': {
        'paper_bgcolor': 'rgba(0,0,0,0)',
        'plot_bgcolor': 'rgba(21,28,39,0.5)',
        'font': {'family': 'IBM Plex Sans', 'color': '#eef2f7', 'size': 12},
        'xaxis': {
            'gridcolor': 'rgba(255,255,255,0.08)',
            'linecolor': 'rgba(255,255,255,0.15)',
            'zerolinecolor': 'rgba(255,255,255,0.15)',
        },
        'yaxis': {
            'gridcolor': 'rgba(255,255,255,0.08)',
            'linecolor': 'rgba(255,255,255,0.15)',
            'zerolinecolor': 'rgba(255,255,255,0.15)',
        },
        'hovermode': 'x unified',
        'hoverlabel': {
            'bgcolor': 'rgba(21,28,39,0.95)',
            'font': {'family': 'IBM Plex Sans', 'size': 12},
            'bordercolor': 'rgba(242,100,87,0.5)',
        },
        'title': {
            'font': {'family': 'Space Grotesk', 'size': 16, 'color': '#eef2f7'},
            'x': 0.5,
            'xanchor': 'center',
        },
        'legend': {
            'bgcolor': 'rgba(21,28,39,0.8)',
            'bordercolor': 'rgba(255,255,255,0.08)',
            'borderwidth': 1,
        },
        'margin': dict(l=40, r=40, t=60, b=40),
    }
}

# Paleta de colores
COLOR_PALETTE = [
    '#f26457',  # accent red
    '#4aa3df',  # accent blue
    '#7bd389',  # accent green
    '#ffa726',  # orange
    '#ab47bc',  # purple
    '#26c6da',  # cyan
    '#ff7043',  # deep orange
    '#66bb6a',  # light green
]


def apply_plotly_theme(fig: go.Figure, title: str | None = None, height: int | None = None) -> go.Figure:
    """Aplica el tema customizado a una figura de Plotly.

    Args:
        fig: Figura de Plotly a estilizar.
        title: Título opcional para la gráfica.
        height: Altura opcional en píxeles.

    Returns:
        Figura con tema aplicado.
    """
    fig.update_layout(**PLOTLY_THEME['layout'])

    if title:
        fig.update_layout(title=title)

    if height:
        fig.update_layout(height=height)

    # Actualizar colores de traces
    for i, trace in enumerate(fig.data):
        color_idx = i % len(COLOR_PALETTE)

        # Actualizar markers
        if hasattr(trace, 'marker'):
            if hasattr(trace.marker, 'color'):
                if not isinstance(trace.marker.color, (list, tuple, pd.Series)):
                    trace.marker.color = COLOR_PALETTE[color_idx]

        # Actualizar lines
        if hasattr(trace, 'line'):
            if hasattr(trace.line, 'color'):
                if not isinstance(trace.line.color, (list, tuple, pd.Series)):
                    trace.line.color = COLOR_PALETTE[color_idx]
                    trace.line.width = 3

    return fig


def export_dataframe_to_csv(df: pd.DataFrame) -> bytes:
    """Exporta DataFrame a CSV con formato UTF-8.

    Args:
        df: DataFrame a exportar.

    Returns:
        Bytes del CSV codificado en UTF-8.
    """
    return df.to_csv(index=False).encode('utf-8')


def get_data_freshness_badge(processed_dir: Path) -> tuple[str, str, str]:
    """Calcula la frescura de los datos y devuelve status, color y mensaje.

    Args:
        processed_dir: Directorio con datos procesados.

    Returns:
        Tupla con (badge_text, color_css, tooltip_message).
    """
    incidents_path = processed_dir / "c5_incidents.parquet"

    if not incidents_path.exists():
        return "🔴 No Data", "rgba(239,68,68,0.16)", "No data available. Run 'make data'."

    try:
        incidents = pd.read_parquet(incidents_path)
        if 'timestamp' in incidents.columns:
            latest = pd.to_datetime(incidents['timestamp']).max()
            age_hours = (pd.Timestamp.now() - latest).total_seconds() / 3600

            if age_hours < 24:
                return "🟢 Fresh", "rgba(123,211,137,0.16)", f"Updated {int(age_hours)}h ago"
            elif age_hours < 72:
                return "🟡 Recent", "rgba(255,193,7,0.16)", f"Updated {int(age_hours)}h ago"
            else:
                days = int(age_hours / 24)
                return "🔴 Stale", "rgba(239,68,68,0.16)", f"Updated {days}d ago. Consider running 'make data'."
    except Exception:
        pass

    return "⚪ Unknown", "rgba(158,158,158,0.16)", "Data status unknown"

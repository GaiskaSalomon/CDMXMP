"""Streamlit dashboard for CDMX Mobility Pulse."""

from __future__ import annotations

from pathlib import Path
import time
import html

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import h3
import requests
import streamlit as st

from mobility_pulse.config import ANALYTICS_DIR, CDMX_BBOX, PROCESSED_DIR
from mobility_pulse.app.ui_utils import (
    apply_plotly_theme,
    export_dataframe_to_csv,
)

st.set_page_config(
    page_title="CDMX Mobility Pulse",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/YOUR_USERNAME/CDMXMP',
        'Report a bug': 'https://github.com/YOUR_USERNAME/CDMXMP/issues',
        'About': "# CDMX Mobility Pulse\nUrban mobility intelligence platform\n\nVersion 0.1.0"
    }
)

st.markdown(
    """
    <style>
    :root {
        --bg-0: #0b0f14;
        --bg-1: #111722;
        --panel: #151c27;
        --panel-2: #1b2433;
        --text: #eef2f7;
        --muted: #9aa6b2;
        --accent: #f26457;
        --accent-2: #4aa3df;
        --accent-3: #7bd389;
        --line: rgba(255,255,255,0.08);
    }
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;600;700&family=IBM+Plex+Sans:wght@400;600;700&display=swap');
    .block-container { padding-principales: 0.6rem; padding-left: 2rem; padding-right: 2rem; }
    header { visibility: hidden; height: 0; }
    body, [class*="stApp"] {
        background:
            radial-gradient(900px 600px at 8% 0%, #1b2332 0%, #0b0f14 60%),
            radial-gradient(900px 600px at 90% 0%, #18222f 0%, #0b0f14 60%);
        color: var(--text);
        font-family: "IBM Plex Sans", sans-serif;
    }
    h1, h2, h3, h4 { font-family: "Space Grotesk", sans-serif; letter-spacing: 0.01em; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid var(--line);
        padding-bottom: 0.4rem;
    }
    .stTabs [data-baseweb="tab-list"] button {
        background: transparent;
        border: 1px solid transparent;
        border-radius: 999px;
        padding: 0.35rem 0.9rem;
        font-size: 0.85rem;
        letter-spacing: 0.02em;
        color: var(--muted);
    }
    .stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {
        background: rgba(242,100,87,0.15);
        border: 1px solid rgba(242,100,87,0.45);
        color: #ffd1cc;
    }
    .badge {
        display: inline-block;
        padding: 0.25rem 0.6rem;
        border-radius: 999px;
        font-size: 0.75rem;
        letter-spacing: 0.04em;
        background: rgba(242,100,87,0.16);
        color: #ffc3bc;
        border: 1px solid rgba(242,100,87,0.35);
        margin-right: 0.35rem;
    }
    .hero {
        padding: 1.2rem 1.6rem;
        border-radius: 16px;
        background: linear-gradient(135deg, rgba(21,28,39,0.95), rgba(30,40,56,0.95));
        border: 1px solid var(--line);
        box-shadow: 0 18px 40px rgba(0,0,0,0.35);
        margin-bottom: 0.8rem;
    }
    .hero-title { font-size: 2.2rem; font-weight: 700; letter-spacing: 0.01em; }
    .hero-sub { color: var(--muted); margin-principales: 0.25rem; }
    .section-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 0.2em;
        color: var(--muted);
        margin: 0.6rem 0 0.4rem;
    }
    .kpi-card {
        padding: 1rem 1.35rem;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(20,26,36,0.95), rgba(29,38,52,0.95));
        border: 1px solid var(--line);
        box-shadow: 0 12px 28px rgba(0,0,0,0.28);
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #9aa4b2;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 0.35rem;
        flex-wrap: wrap;
    }
    .kpi-value { font-size: 1.6rem; font-weight: 700; color: #f8fafc; }
    .kpi-delta { font-size: 0.85rem; color: #22c55e; }
    .kpi-delta.neg { color: #ef4444; }
    .panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 0.8rem 1rem;
        margin-bottom: 0.8rem;
    }
    .sidebar .sidebar-content { background: var(--panel); }
    div[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #141b27 0%, #10151f 100%);
        border-right: 1px solid var(--line);
    }
    .stDataFrame { border: 1px solid var(--line); border-radius: 12px; }
    .exec-grid {
        display: grid;
        grid-template-columns: repeat(4, minmax(0, 1fr));
        gap: 0.8rem;
        margin-bottom: 0.8rem;
    }
    .exec-card {
        padding: 0.9rem 1.1rem;
        border-radius: 12px;
        background: linear-gradient(135deg, rgba(19,25,35,0.95), rgba(28,36,50,0.95));
        border: 1px solid var(--line);
        box-shadow: 0 10px 24px rgba(0,0,0,0.25);
    }
    .exec-label {
        font-size: 0.75rem;
        color: var(--muted);
        text-transform: uppercase;
        letter-spacing: 0.1em;
    }
    .exec-value {
        font-size: 1.4rem;
        font-weight: 700;
        color: #f8fafc;
        margin-principales: 0.2rem;
    }
    .exec-icon {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 0.5rem;
        background: rgba(242,100,87,0.9);
    }
    .note-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.7rem; }
    .note {
        background: var(--panel-2);
        border: 1px solid var(--line);
        border-left: 4px solid var(--accent);
        border-radius: 12px;
        padding: 0.7rem 0.85rem;
    }
    .note-high { border-left-color: #f26457; background: rgba(242, 100, 87, 0.12); }
    .note-med { border-left-color: #f0b429; background: rgba(240, 180, 41, 0.12); }
    .note-low { border-left-color: #7bd389; background: rgba(123, 211, 137, 0.12); }
    .note-title {
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.35rem;
        flex-wrap: wrap;
    }
    .note-body { color: var(--text); font-size: 0.9rem; }
    @media (max-width: 1024px) {
        .exec-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    }
    @media (max-width: 640px) {
        .exec-grid { grid-template-columns: 1fr; }
    }
    
    /* Hover effects para cards */
    .kpi-card {
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 16px 40px rgba(0,0,0,0.4);
    }
    
    /* Smooth transitions para tabs */
    .stTabs [data-baseweb="tab-panel"] {
        animation: fadeIn 0.3s ease-in;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    /* Loading spinner elegante */
    @keyframes pulse {
        0%, 100% { opacity: 0.3; }
        50% { opacity: 1; }
    }
    .stSpinner > div {
        animation: pulse 1.5s ease-in-out infinite;
    }
    
    /* Tooltips clicables */
    .tooltip-details {
        display: inline-block;
        position: relative;
    }
    .tooltip-icon {
        opacity: 0.6;
        cursor: pointer;
        font-size: 0.85rem;
        margin-left: 0.3rem;
        transition: opacity 0.2s;
        list-style: none;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 1.1rem;
        height: 1.1rem;
        border-radius: 999px;
        border: 1px solid var(--line);
        background: rgba(255,255,255,0.04);
    }
    .tooltip-icon::-webkit-details-marker {
        display: none;
    }
    .tooltip-icon::marker {
        content: "";
    }
    .tooltip-icon:hover {
        opacity: 1;
    }
    .tooltip-text {
        position: absolute;
        right: 0;
        top: 1.4rem;
        min-width: 220px;
        max-width: 320px;
        background: #121826;
        border: 1px solid var(--line);
        border-radius: 8px;
        padding: 0.6rem 0.7rem;
        font-size: 0.78rem;
        line-height: 1.35;
        color: var(--text);
        box-shadow: 0 14px 30px rgba(0,0,0,0.35);
        z-index: 20;
        display: none;
    }
    .tooltip-details[open] .tooltip-text {
        display: block;
    }
    
    /* Empty state styling */
    .empty-state {
        text-align: center;
        padding: 3rem 1rem;
        opacity: 0.6;
        animation: fadeIn 0.5s ease-in;
    }
    .empty-state-icon {
        font-size: 4rem;
        margin-bottom: 1rem;
        animation: pulse 2s ease-in-out infinite;
    }
    .empty-state-title {
        font-size: 1.2rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
    }
    .empty-state-action {
        margin-principales: 1rem;
        opacity: 0.7;
        font-family: 'Courier New', monospace;
        background: rgba(255,255,255,0.05);
        padding: 0.5rem 1rem;
        border-radius: 8px;
        display: inline-block;
    }
    
    /* Better scrollbars */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: var(--bg-1);
    }
    ::-webkit-scrollbar-thumb {
        background: var(--line);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: var(--accent);
    }
    
    /* Status badge styles */
    .status-badge-fresh {
        background: rgba(123,211,137,0.16);
        border-color: rgba(123,211,137,0.35);
        color: #c3f7cf;
    }
    .status-badge-recent {
        background: rgba(255,193,7,0.16);
        border-color: rgba(255,193,7,0.35);
        color: #fff4d1;
    }
    .status-badge-stale {
        background: rgba(239,68,68,0.16);
        border-color: rgba(239,68,68,0.35);
        color: #ffd1d1;
    }
    .status-badge-historical {
        background: rgba(148,163,184,0.16);
        border-color: rgba(148,163,184,0.35);
        color: #e2e8f0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _empty_state(icon: str, title: str, message: str, action: str | None = None) -> None:
    """Render a professional empty state component."""
    action_html = f'<div class="empty-state-action">{action}</div>' if action else ''
    st.markdown(
        f"""
        <div class="empty-state">
            <div class="empty-state-icon">{icon}</div>
            <div class="empty-state-title">{title}</div>
            <div style="opacity: 0.7;">{message}</div>
            {action_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _data_freshness_badge() -> str:
    """Calculate and return a freshness status badge for the data."""
    incidents_path = PROCESSED_DIR / "c5_incidents.parquet"
    incidents = _load_parquet(incidents_path)
    if incidents is not None and not incidents.empty and "timestamp" in incidents.columns:
        try:
            latest = pd.to_datetime(incidents["timestamp"]).max()
            age_hours = (pd.Timestamp.now() - latest).total_seconds() / 3600

            if age_hours >= 24 * 30:
                return '<span class="badge status-badge-historical">🧾 Histórico (hasta {})</span>'.format(
                    latest.strftime("%Y-%m-%d")
                )
            if age_hours < 24:
                return '<span class="badge status-badge-fresh">🟢 Actualizado ({:.0f}h)</span>'.format(age_hours)
            elif age_hours < 72:
                return '<span class="badge status-badge-recent">🟡 Reciente ({:.0f}h)</span>'.format(age_hours)
            else:
                return '<span class="badge status-badge-stale">🔴 Desactualizado ({:.0f}h)</span>'.format(age_hours)
        except Exception:
            pass
    return '<span class="badge">⚪ Desconocido</span>'


def _tooltip_details(text: str) -> str:
    if not text:
        return ""
    safe_text = html.escape(text)
    return (
        "<details class='tooltip-details'>"
        "<summary class='tooltip-icon' aria-label='Detalle'>i</summary>"
        f"<div class='tooltip-text'>{safe_text}</div>"
        "</details>"
    )


def _metric_with_tooltip(label: str, value: str, tooltip: str, delta: float | None = None) -> None:
    """Render a KPI card with tooltip information."""
    delta_html = ""
    if delta is not None:
        klass = "kpi-delta" if delta >= 0 else "kpi-delta neg"
        delta_html = f"<div class='{klass}'>{delta:+.1%} vs anterior</div>"

    tooltip_html = _tooltip_details(tooltip)
    label_html = html.escape(label)
    value_html = html.escape(value)
    st.markdown(
        f"""
        <div class=\"kpi-card\">
            <div class=\"kpi-label\">
                {label_html}
                {tooltip_html}
            </div>
            <div class=\"kpi-value\">{value_html}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def _load_parquet(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        return None
    return pd.read_parquet(path)


def _display_df(df: pd.DataFrame) -> pd.DataFrame:
    """Formatea un DataFrame para visualización en el dashboard."""
    if df is None or df.empty:
        return df
    df = df.copy()
    day_map = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo",
    }
    rename_map = {
        "lon": "Longitud",
        "lat": "Latitud",
        "timestamp": "Fecha/Hora",
        "date": "Fecha",
        "count": "Conteo",
        "incidents": "Incidentes",
        "stops": "Paradas",
        "incidents_per_stop": "Incidentes por parada",
        "risk_z": "Riesgo z",
        "risk_score": "Riesgo",
        "access_score": "Puntaje acceso",
        "access_z": "Acceso z",
        "impact_score": "Impacto",
        "travel_time_min": "Tiempo caminando (min)",
        "nearest_stop_ring": "Anillos a parada",
        "access_distance_m": "Distancia a parada (m)",
        "day_of_week": "Día de semana",
        "hour": "Hora",
        "month": "Mes",
        "zone_id": "Zona",
        "id_zona": "Zona",
        "alcaldia": "Alcaldía",
        "colonia": "Colonia",
        "alcaldia_catalogo": "Alcaldía",
        "colonia_catalogo": "Colonia",
        "bikes_available": "Bicis disponibles",
        "docks_available": "Anclajes disponibles",
        "station_id": "ID estación",
        "stop_id": "ID parada",
        "stop_name": "Nombre de parada",
        "name": "Nombre",
        "flow": "Flujo",
        "delta_pct": "Cambio (%)",
        "last7": "Últimos 7d",
        "prev7": "Previos 7d",
        "rationale": "Justificación",
    }
    if "day_of_week" in df.columns:
        df["day_of_week"] = df["day_of_week"].map(
            day_map).fillna(df["day_of_week"])
    df = df.rename(columns=rename_map)
    df.columns = [str(col).upper() for col in df.columns]
    # Eliminar columnas de zona ID ya que mostramos alcaldía/colonia
    zona_cols = [col for col in df.columns if "ZONA" in str(col).upper()]
    if zona_cols:
        df = df.drop(columns=zona_cols, errors="ignore")
    # Reemplazar valores None/NaN/nan y pd.NA con un marcador visible
    for col in df.columns:
        if df[col].dtype == "object":
            # Reemplazar None, nan, NaN strings y pd.NA con guion para indicar sin datos
            df[col] = df[col].fillna("-").astype(str)
            df[col] = df[col].replace(["None", "nan", "NaN", "<NA>", ""], "-")
    return df


def _get_zone_key(df: pd.DataFrame) -> str | None:
    """Detecta de forma consistente si existe zone_id o id_zona en un DataFrame."""
    if "zone_id" in df.columns:
        return "zone_id"
    if "id_zona" in df.columns:
        return "id_zona"
    return None


def _ensure_zone_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Asegura que el DataFrame tenga ambas columnas zone_id e id_zona sin duplicar."""
    if df is None or df.empty:
        return df
    df = df.copy()
    # Eliminar duplicados primero
    df = df.loc[:, ~df.columns.duplicated()]
    # Solo crear la columna faltante si no existe
    if "zone_id" in df.columns and "id_zona" not in df.columns:
        df["id_zona"] = df["zone_id"]
    elif "id_zona" in df.columns and "zone_id" not in df.columns:
        df["zone_id"] = df["id_zona"]
    return df


def _merge_with_zone_meta(df: pd.DataFrame, zone_meta: pd.DataFrame, how: str = "left") -> pd.DataFrame:
    """Hace un merge limpio con zone_meta, manejando columnas de zona duplicadas."""
    if df.empty or zone_meta.empty:
        return df

    # Hacer copias profundas y eliminar columnas duplicadas
    df = df.copy()
    df = df.loc[:, ~df.columns.duplicated()]
    zone_meta = zone_meta.copy()
    zone_meta = zone_meta.loc[:, ~zone_meta.columns.duplicated()]

    # Detectar claves
    df_zone_key = _get_zone_key(df)
    meta_zone_key = _get_zone_key(zone_meta)

    if not df_zone_key or not meta_zone_key:
        return df

    # Si las claves son diferentes, renombrar temporalmente para que coincidan
    if df_zone_key != meta_zone_key:
        zone_meta = zone_meta.rename(columns={meta_zone_key: df_zone_key})
        meta_zone_key = df_zone_key

    # Hacer merge usando 'on' para evitar columnas duplicadas
    result = df.merge(zone_meta, on=df_zone_key,
                      how=how, suffixes=('', '_meta'))

    # Eliminar columnas duplicadas con sufijo _meta
    cols_to_drop = [col for col in result.columns if col.endswith('_meta')]
    if cols_to_drop:
        result = result.drop(columns=cols_to_drop)

    # Asegurar que no queden duplicados
    result = result.loc[:, ~result.columns.duplicated()]

    return result


# Temporalmente sin cache para debugging
# @st.cache_data(show_spinner=False)
def _load_zone_metadata_v4() -> pd.DataFrame:
    """Carga metadata de zonas con alcaldía y colonia desde múltiples fuentes. Versión 4."""

    # Intentar cargar desde múltiples fuentes para obtener todos los zone_ids posibles
    all_data = []

    # Cargar incidents
    incidents = _load_parquet(PROCESSED_DIR / "c5_incidents.parquet")
    if incidents is not None and not incidents.empty:
        all_data.append(incidents)

    # Cargar stops
    stops = _load_parquet(PROCESSED_DIR / "gtfs_stops.parquet")
    if stops is not None and not stops.empty:
        all_data.append(stops)

    # Si no hay datos, retornar vacío
    if not all_data:
        return pd.DataFrame()

    # Combinar todos los datasets
    combined = pd.concat(all_data, ignore_index=True)

    zone_col = _get_zone_key(combined)
    if zone_col is None:
        return pd.DataFrame()

    meta_cols = []
    if "alcaldia_catalogo" in combined.columns:
        meta_cols.append("alcaldia_catalogo")
    if "colonia_catalogo" in combined.columns:
        meta_cols.append("colonia_catalogo")

    # Si no hay columnas de metadata pero tenemos alcaldia/colonia directamente
    if not meta_cols:
        if "alcaldia" in combined.columns:
            meta_cols.append("alcaldia")
        if "colonia" in combined.columns:
            meta_cols.append("colonia")

    if not meta_cols:
        return pd.DataFrame()

    # Crear una función que retorna el modo más común
    def mode_or_na(x):
        mode_vals = x.mode()
        return mode_vals.iloc[0] if len(mode_vals) > 0 else pd.NA

    agg_dict = {col: mode_or_na for col in meta_cols}

    # Si hay latitud y longitud, calcular el centro promedio de cada zona
    has_coords = "latitud" in combined.columns and "longitud" in combined.columns
    if not has_coords:
        has_coords = "lat" in combined.columns and "lon" in combined.columns

    if has_coords:
        if "latitud" in combined.columns:
            agg_dict["latitud"] = "mean"
        if "longitud" in combined.columns:
            agg_dict["longitud"] = "mean"
        if "lat" in combined.columns and "latitud" not in combined.columns:
            agg_dict["lat"] = "mean"
        if "lon" in combined.columns and "longitud" not in combined.columns:
            agg_dict["lon"] = "mean"

    zone_meta = combined.groupby(
        zone_col, dropna=False).agg(agg_dict).reset_index()

    # Renombrar columnas para estandarizar
    rename_dict = {zone_col: "zone_id"}

    # Renombrar alcaldia_catalogo y colonia_catalogo si existen
    if "alcaldia_catalogo" in zone_meta.columns:
        rename_dict["alcaldia_catalogo"] = "alcaldia"
    if "colonia_catalogo" in zone_meta.columns:
        rename_dict["colonia_catalogo"] = "colonia"

    # Renombrar coordenadas si existen
    if "latitud" in zone_meta.columns:
        rename_dict["latitud"] = "lat"
    if "longitud" in zone_meta.columns:
        rename_dict["longitud"] = "lon"

    zone_meta = zone_meta.rename(columns=rename_dict)
    return zone_meta.loc[:, ~zone_meta.columns.duplicated()]


def _load_processed() -> dict[str, pd.DataFrame]:
    def _ensure(df: pd.DataFrame | None) -> pd.DataFrame:
        return df if df is not None else pd.DataFrame()

    data = {
        "incidentes": _ensure(_load_parquet(PROCESSED_DIR / "c5_incidents.parquet")),
        "paradas": _ensure(_load_parquet(PROCESSED_DIR / "gtfs_stops.parquet")),
        "estaciones": _ensure(_load_parquet(PROCESSED_DIR / "ecobici_rt.parquet")),
        "viajes": _ensure(_load_parquet(PROCESSED_DIR / "ecobici_trips.parquet")),
    }

    # Asegurar que todas las tablas tengan ambas columnas zone_id e id_zona
    for key in data:
        data[key] = _ensure_zone_columns(data[key])

    return data


def _load_analytics() -> dict[str, pd.DataFrame]:
    def _ensure(df: pd.DataFrame | None) -> pd.DataFrame:
        return df if df is not None else pd.DataFrame()

    def _load_accessibility() -> pd.DataFrame | None:
        primary = ANALYTICS_DIR / "accessibility_zones.parquet"
        legacy = ANALYTICS_DIR / "accesoibility_zones.parquet"
        if primary.exists():
            return _load_parquet(primary)
        return _load_parquet(legacy)

    analytics = {
        "c5_hourly": _ensure(_load_parquet(ANALYTICS_DIR / "c5_hourly.parquet")),
        "c5_dow": _ensure(_load_parquet(ANALYTICS_DIR / "c5_dow.parquet")),
        "c5_monthly": _ensure(_load_parquet(ANALYTICS_DIR / "c5_monthly.parquet")),
        "c5_hourly_total": _ensure(_load_parquet(ANALYTICS_DIR / "c5_hourly_total.parquet")),
        "c5_dow_total": _ensure(_load_parquet(ANALYTICS_DIR / "c5_dow_total.parquet")),
        "c5_zone_daily": _ensure(_load_parquet(ANALYTICS_DIR / "c5_zone_daily.parquet")),
        "c5_daily": _ensure(_load_parquet(ANALYTICS_DIR / "c5_daily.parquet")),
        "c5_anomalies": _ensure(_load_parquet(ANALYTICS_DIR / "c5_anomalies.parquet")),
        "c5_pressure": _ensure(_load_parquet(ANALYTICS_DIR / "c5_pressure.parquet")),
        "trips_hourly": _ensure(_load_parquet(ANALYTICS_DIR / "ecobici_trips_hourly.parquet")),
        "trips_dow": _ensure(_load_parquet(ANALYTICS_DIR / "ecobici_trips_dow.parquet")),
        "trips_monthly": _ensure(_load_parquet(ANALYTICS_DIR / "ecobici_trips_monthly.parquet")),
        "ecobici_trips_hourly_total": _ensure(
            _load_parquet(ANALYTICS_DIR / "ecobici_trips_hourly_total.parquet")
        ),
        "ecobici_trips_dow_total": _ensure(
            _load_parquet(ANALYTICS_DIR / "ecobici_trips_dow_total.parquet")
        ),
        "gps_like_monthly": _ensure(_load_parquet(ANALYTICS_DIR / "gps_like_monthly.parquet")),
        "gps_like_hourly": _ensure(_load_parquet(ANALYTICS_DIR / "gps_like_hourly.parquet")),
        "gps_like_dow": _ensure(_load_parquet(ANALYTICS_DIR / "gps_like_dow.parquet")),
        "gps_like_zones": _ensure(_load_parquet(ANALYTICS_DIR / "gps_like_zones.parquet")),
        "gps_like_zone_hour": _ensure(_load_parquet(ANALYTICS_DIR / "gps_like_zone_hour.parquet")),
        "gps_like_risk": _ensure(_load_parquet(ANALYTICS_DIR / "gps_like_risk.parquet")),
        "gps_like_od": _ensure(_load_parquet(ANALYTICS_DIR / "gps_like_od.parquet")),
        "accesoibility_zones": _ensure(_load_accessibility()),
        "impact_zones": _ensure(_load_parquet(ANALYTICS_DIR / "impact_zones.parquet")),
        "ppi": _ensure(_load_parquet(ANALYTICS_DIR / "ppi_zones.parquet")),
    }

    # Asegurar que todas las tablas tengan ambas columnas zone_id e id_zona
    for key in analytics:
        analytics[key] = _ensure_zone_columns(analytics[key])

    if analytics["accesoibility_zones"].empty and not analytics["impact_zones"].empty:
        analytics["accesoibility_zones"] = analytics["impact_zones"].copy()
    if not analytics["accesoibility_zones"].empty and "access_score" in analytics["accesoibility_zones"].columns:
        analytics["accesoibility_zones"] = analytics["accesoibility_zones"].rename(
            columns={"access_score": "acceso_score"}
        )
    return analytics


def _apply_filters(df: pd.DataFrame, date_range: tuple[pd.Timestamp, pd.Timestamp], hours: list[int], days: list[str]) -> pd.DataFrame:
    if df.empty or "timestamp" not in df.columns:
        return df
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    mask = (df["timestamp"] >= date_range[0]) & (
        df["timestamp"] <= date_range[1])
    if hours:
        mask &= df["timestamp"].dt.hour.isin(hours)
    if days:
        # Mapear días en español a inglés para filtrar
        day_map = {
            "Lunes": "Monday",
            "Martes": "Tuesday",
            "Miércoles": "Wednesday",
            "Jueves": "Thursday",
            "Viernes": "Friday",
            "Sábado": "Saturday",
            "Domingo": "Sunday"
        }
        english_days = [day_map.get(day, day) for day in days]
        mask &= df["timestamp"].dt.day_name().isin(english_days)
    return df[mask]


def _compute_zoom(min_lon: float, max_lon: float, min_lat: float, max_lat: float) -> float:
    span = max(max_lon - min_lon, max_lat - min_lat)
    if span <= 0:
        return 11
    # Rough heuristic for zoom level
    if span < 0.02:
        return 13
    if span < 0.05:
        return 12
    if span < 0.1:
        return 11
    if span < 0.2:
        return 10
    return 9


def _h3_center(cell: str) -> tuple[float, float] | None:
    if not cell:
        return None
    try:
        if hasattr(h3, "cell_to_latlng"):
            lat, lon = h3.cell_to_latlng(cell)
        else:
            lat, lon = h3.h3_to_geo(cell)
        return float(lat), float(lon)
    except Exception:
        return None


def _h3_resolution(cell: str) -> int | None:
    if not cell:
        return None
    try:
        if hasattr(h3, "get_resolution"):
            return int(h3.get_resolution(cell))
        return int(h3.h3_get_resolution(cell))
    except Exception:
        return None


def _h3_parent(cell: str, resolution: int) -> str | None:
    if not cell:
        return None
    try:
        if hasattr(h3, "cell_to_parent"):
            return h3.cell_to_parent(cell, resolution)
        return h3.h3_to_parent(cell, resolution)
    except Exception:
        return None


def _zone_heatmap(df: pd.DataFrame, value_col: str = "conteo") -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    zone_key = _get_zone_key(df)
    if not zone_key:
        return pd.DataFrame()
    counts = df.groupby(zone_key, dropna=False).size(
    ).reset_index(name=value_col)
    # Eliminar duplicados antes de apply
    counts = counts.loc[:, ~counts.columns.duplicated()]
    centers = counts[zone_key].apply(_h3_center)
    counts["lat"] = centers.apply(lambda x: x[0] if x else pd.NA)
    counts["lon"] = centers.apply(lambda x: x[1] if x else pd.NA)
    return counts.dropna(subset=["lat", "lon"])


def _kpi_stats(df: pd.DataFrame, label: str, date_range: tuple[pd.Timestamp, pd.Timestamp]) -> dict[str, object]:
    if df.empty or "timestamp" not in df.columns:
        return {"label": label, "conteo": 0, "delta": None, "peak_hour": None, "peak_day": None}

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    current = df[(df["timestamp"] >= date_range[0]) &
                 (df["timestamp"] <= date_range[1])]

    count = int(len(current))
    peak_hour = None
    peak_day = None
    if not current.empty:
        peak_hour = int(current["timestamp"].dt.hour.value_counts().idxmax())
        peak_day = str(
            current["timestamp"].dt.day_name().value_counts().idxmax())

    duration = date_range[1] - date_range[0]
    prev_start = date_range[0] - duration
    prev_end = date_range[0]
    prev = df[(df["timestamp"] >= prev_start) & (df["timestamp"] < prev_end)]
    prev_count = int(len(prev))
    delta = None
    if prev_count > 0:
        delta = (count - prev_count) / prev_count

    return {
        "label": label,
        "conteo": count,
        "delta": delta,
        "peak_hour": peak_hour,
        "peak_day": peak_day,
    }


def _kpi_card(label: str, value: str, delta: float | None = None) -> None:
    delta_html = ""
    if delta is not None:
        klass = "kpi-delta" if delta >= 0 else "kpi-delta neg"
        delta_html = f"<div class='{klass}'>{delta:+.1%} vs anterior</div>"
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            {delta_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_notes(title: str, notes: list[dict]) -> None:
    if not notes:
        return
    st.markdown(title)
    blocks_list: list[str] = []
    for note in notes:
        sev = note.get("severity", "note-low")
        title_text = html.escape(note.get("title", "Sin título"))
        body_text = html.escape(note.get("body", ""))
        hint_text = note.get("hint", "")
        hint_html = _tooltip_details(hint_text) if hint_text else ""
        blocks_list.append(
            "<div class='note {sev}'>"
            "<div class='note-title'>{title}{hint}</div>"
            "<div class='note-body'>{body}</div>"
            "</div>".format(
                sev=sev,
                title=title_text,
                hint=hint_html,
                body=body_text,
            )
        )
    blocks = "\n".join(blocks_list)
    st.markdown(f"<div class='note-grid'>{blocks}</div>", unsafe_allow_html=True)


def _render_insights(
    incidents: pd.DataFrame,
    trips: pd.DataFrame,
    stops: pd.DataFrame,
    date_range: tuple[pd.Timestamp, pd.Timestamp],
    analytics: dict[str, pd.DataFrame],
) -> None:
    st.subheader("Resumen Ejecutivo")
    with st.expander("Finalidad de esta vista", expanded=False):
        st.markdown(
            "Resumen rápido del estado del sistema para una lectura ejecutiva: "
            "volumen de incidentes y viajes en el rango filtrado, y una ventana de cobertura. "
            "Úsalo para validar que el rango seleccionado tiene datos suficientes."
        )

    inc_kpi = _kpi_stats(incidents, "Incidentes", date_range)
    trip_kpi = _kpi_stats(trips, "Viajes ECOBICI", date_range)

    col1, col2, col3 = st.columns(3)
    with col1:
        _kpi_card(inc_kpi["label"], f"{inc_kpi['conteo']:,}", inc_kpi["delta"])
    with col2:
        _kpi_card(trip_kpi["label"],
                  f"{trip_kpi['conteo']:,}", trip_kpi["delta"])
    with col3:
        _kpi_card("Ventana de Cobertura",
                  f"{date_range[0].date()} -> {date_range[1].date()}", None)

    zone_meta = _load_zone_metadata_v4()

    def _load_geocode_cache() -> pd.DataFrame:
        cache_path = PROCESSED_DIR / "zone_geocoding.parquet"
        if cache_path.exists():
            return pd.read_parquet(cache_path)
        return pd.DataFrame(columns=["id_zona", "address"])

    def _save_geocode_cache(df: pd.DataFrame) -> None:
        cache_path = PROCESSED_DIR / "zone_geocoding.parquet"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, index=False)

    def _reverse_geocode(lat: float, lon: float) -> str | None:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "jsonv2",
            "lat": lat,
            "lon": lon,
            "zoom": 16,
            "addressdetails": 1,
        }
        headers = {"User-Agent": "cdmx-mobility-pulse/1.0"}
        try:
            resp = requests.get(url, params=params,
                                headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data.get("display_name")
        except Exception:
            return None

    def _zone_table_with_geocode(series: pd.Series, value_name: str, zone_meta: pd.DataFrame | None = None) -> pd.DataFrame:
        df = series.reset_index(name=value_name)
        zone_key = _get_zone_key(df)
        if not zone_key:
            return df
        # Eliminar duplicados antes de apply
        df = df.loc[:, ~df.columns.duplicated()]

        # Solo intentar obtener coordenadas de H3 si parece ser celda H3
        sample_zone = df[zone_key].iloc[0] if not df.empty else None
        is_h3 = sample_zone and isinstance(
            sample_zone, str) and sample_zone[0].isdigit()

        if is_h3:
            centers = df[zone_key].apply(_h3_center)
            df["lat"] = centers.apply(lambda x: x[0] if x else pd.NA)
            df["lon"] = centers.apply(lambda x: x[1] if x else pd.NA)

        if zone_meta is not None and not zone_meta.empty:
            df = _merge_with_zone_meta(df, zone_meta, how="left")
        if geocode_enabled:
            cache = _load_geocode_cache()
            df = df.merge(cache, left_on=zone_key,
                          right_on="id_zona", how="left")
            missing = df[df["address"].isna()].head(10)
            new_rows = []
            for _, row in missing.iterrows():
                lat = row.get("lat")
                lon = row.get("lon")
                if pd.isna(lat) or pd.isna(lon):
                    continue
                address = _reverse_geocode(float(lat), float(lon))
                if address:
                    new_rows.append(
                        {"id_zona": row.get(zone_key), "address": address})
                time.sleep(1.0)
            if new_rows:
                cache = pd.concat([cache, pd.DataFrame(new_rows)],
                                  ignore_index=True).drop_duplicates("id_zona")
                _save_geocode_cache(cache)
                if _get_zone_key(cache):
                    df = df.drop(columns=["address"], errors="ignore")
                    df = _merge_with_zone_meta(df, cache)
        return df

    def _zone_label(row: pd.Series) -> str:
        parts = []
        if "alcaldia_catalogo" in row and pd.notna(row["alcaldia_catalogo"]):
            parts.append(str(row["alcaldia_catalogo"]))
        if "colonia_catalogo" in row and pd.notna(row["colonia_catalogo"]):
            parts.append(str(row["colonia_catalogo"]))
        if "alcaldia" in row and pd.notna(row["alcaldia"]):
            parts.append(str(row["alcaldia"]))
        if "colonia" in row and pd.notna(row["colonia"]):
            parts.append(str(row["colonia"]))
        return " / ".join(parts) if parts else "Área desconocida"

    def _unique_label(label: str, row: pd.Series, used: set[str]) -> str:
        if label not in used:
            used.add(label)
            return label
        zone_id = row.get("id_zona") or row.get("zone_id")
        if pd.notna(zone_id):
            candidate = f"{label} (ID {zone_id})"
            if candidate not in used:
                used.add(candidate)
                return candidate
        suffix = 2
        while f"{label} ({suffix})" in used:
            suffix += 1
        candidate = f"{label} ({suffix})"
        used.add(candidate)
        return candidate

    def _render_card_list(title: str, lines: list[str]) -> None:
        if not lines:
            return
        st.markdown(f"{title}")
        st.markdown("<div style='margin-bottom: 0.4rem;'></div>",
                    unsafe_allow_html=True)
        cols = st.columns(3)
        for idx, line in enumerate(lines):
            if ":" in line:
                label, value = line.split(":", 1)
            else:
                label, value = title, line
            with cols[idx % 3]:
                _kpi_card(label.strip(), value.strip(), None)
        st.markdown("<div style='margin-bottom: 0.6rem;'></div>",
                    unsafe_allow_html=True)

    insight_lines = []
    day_map = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miércoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sábado",
        "Sunday": "Domingo",
    }
    if inc_kpi["peak_hour"] is not None:
        insight_lines.append(
            f"Hora pico de incidentes: {inc_kpi['peak_hour']:02d}:00")
    if inc_kpi["peak_day"] is not None:
        insight_lines.append(
            f"Día más activo de incidentes: {day_map.get(inc_kpi['peak_day'], inc_kpi['peak_day'])}")
    if trip_kpi["peak_hour"] is not None:
        insight_lines.append(
            f"Hora pico ECOBICI: {trip_kpi['peak_hour']:02d}:00")
    if trip_kpi["peak_day"] is not None:
        insight_lines.append(
            f"Día más activo ECOBICI: {day_map.get(trip_kpi['peak_day'], trip_kpi['peak_day'])}")

    if insight_lines:
        st.markdown("Resumen ejecutivo")
        cols = st.columns(len(insight_lines))
        for col, line in zip(cols, insight_lines):
            label, value = line.split(":", 1)
            with col:
                _kpi_card(label, value, None)
    else:
        _empty_state(
            "📊",
            "Datos Insuficientes para Perspectivas",
            "La ventana de tiempo seleccionada no contiene suficientes datos.'t contain enough data points.",
            "Intente expandir el rango de fechas o quitar filtros"
        )

    if not incidents.empty and "id_zona" in incidents.columns:
        zone_counts = incidents.groupby(
            "id_zona", dropna=False).size().sort_values(ascending=False).head(3)
        if not zone_counts.empty:
            st.markdown("Resumen por zona")
            cols = st.columns(len(zone_counts))
            meta_zone_key = _get_zone_key(
                zone_meta) if not zone_meta.empty else None
            for col, (zone_id, count) in zip(cols, zone_counts.items()):
                row = None
                if meta_zone_key:
                    matching = zone_meta[zone_meta[meta_zone_key] == zone_id]
                    row = matching.iloc[0] if not matching.empty else None
                zone_label = _zone_label(
                    row) if row is not None else "Área desconocida"
                with col:
                    _kpi_card(zone_label, f"{int(count):,}", None)

    if not incidents.empty and "alcaldia_catalogo" in incidents.columns:
        alc_counts = (
            incidents.groupby("alcaldia_catalogo", dropna=False)
            .size()
            .sort_values(ascending=False)
            .head(3)
        )
        if not alc_counts.empty:
            st.markdown("Resumen por alcaldía")
            cols = st.columns(len(alc_counts))
            for col, (alcaldia, count) in zip(cols, alc_counts.items()):
                with col:
                    _kpi_card(str(alcaldia), f"{int(count):,}", None)

    acceso = analytics.get("accesoibility_zones", pd.DataFrame())
    if not acceso.empty and not zone_meta.empty:
        zone_key = "id_zona" if "id_zona" in acceso.columns else (
            "zone_id" if "zone_id" in acceso.columns else None)
        if zone_key is None:
            acceso_meta = pd.DataFrame()
        else:
            acceso_meta = acceso.merge(
                zone_meta.rename(
                    columns={"alcaldia_catalogo": "alcaldia", "colonia_catalogo": "colonia"}),
                left_on=zone_key,
                right_on="zone_id",
                how="left",
            )
        if "alcaldia" in acceso_meta.columns and "acceso_score" in acceso_meta.columns:
            alc_acceso = (
                acceso_meta.groupby("alcaldia", dropna=False)["acceso_score"]
                .mean()
                .sort_values(ascending=False)
                .head(3)
            )
            if not alc_acceso.empty:
                st.markdown("Accesibilidad por alcaldía (principales 3)")
                cols = st.columns(len(alc_acceso))
                for col, (alcaldia, score) in zip(cols, alc_acceso.items()):
                    with col:
                        _kpi_card(str(alcaldia), f"{score:.2f}", None)

            alc_summary = (
                acceso_meta.groupby("alcaldia", dropna=False)["acceso_score"]
                .agg(["mean", "median"])
                .reset_index()
            )
            if not alc_summary.empty:
                alc_summary["p25"] = acceso_meta.groupby("alcaldia", dropna=False)[
                    "acceso_score"].quantile(0.25).values
                alc_summary["p75"] = acceso_meta.groupby("alcaldia", dropna=False)[
                    "acceso_score"].quantile(0.75).values
                alc_summary = alc_summary.sort_values(
                    "mean", ascending=False).head(10)
                notes = []
                for _, row in alc_summary.head(6).iterrows():
                    mean_val = row.get("mean")
                    median_val = row.get("median")
                    severity = "note-low"
                    if pd.notna(mean_val):
                        if mean_val <= 0.35:
                            severity = "note-high"
                        elif mean_val <= 0.55:
                            severity = "note-med"
                    body = "Media: {0:.2f} | Mediana: {1:.2f}".format(
                        float(mean_val) if pd.notna(mean_val) else 0.0,
                        float(median_val) if pd.notna(median_val) else 0.0,
                    )
                    notes.append(
                        {
                            "title": str(row.get("alcaldia", "Alcaldia")),
                            "body": body,
                            "severity": severity,
                        }
                    )
                _render_notes("Accesibilidad por alcaldia (resumen)", notes)

    # Coverage context
    coverage_lines = []
    if not incidents.empty and "timestamp" in incidents.columns:
        inc_ts = pd.to_datetime(incidents["timestamp"], errors="coerce")
        coverage_lines.append(
            f"Cobertura de incidentes: {inc_ts.min().date()} -> {inc_ts.max().date()}")
    if not trips.empty and "timestamp" in trips.columns:
        trip_ts = pd.to_datetime(trips["timestamp"], errors="coerce")
        coverage_lines.append(
            f"Cobertura de viajes ECOBICI: {trip_ts.min().date()} -> {trip_ts.max().date()}")
    if coverage_lines:
        _render_card_list("Cobertura de datos", coverage_lines)

    def _load_geocode_cache() -> pd.DataFrame:
        cache_path = PROCESSED_DIR / "zone_geocoding.parquet"
        if cache_path.exists():
            return pd.read_parquet(cache_path)
        return pd.DataFrame(columns=["id_zona", "address"])

    def _save_geocode_cache(df: pd.DataFrame) -> None:
        cache_path = PROCESSED_DIR / "zone_geocoding.parquet"
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, index=False)

    def _reverse_geocode(lat: float, lon: float) -> str | None:
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            "format": "jsonv2",
            "lat": lat,
            "lon": lon,
            "zoom": 16,
            "addressdetails": 1,
        }
        headers = {"User-Agent": "cdmx-mobility-pulse/1.0"}
        try:
            resp = requests.get(url, params=params,
                                headers=headers, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return data.get("display_name")
        except Exception:
            return None

    def _zone_table(series: pd.Series, value_name: str, zone_meta: pd.DataFrame | None = None, geocode: bool = False) -> pd.DataFrame:
        df = series.reset_index(name=value_name)
        zone_key = _get_zone_key(df)
        if not zone_key:
            return df
        # Eliminar duplicados antes de apply
        df = df.loc[:, ~df.columns.duplicated()]

        # Solo intentar obtener coordenadas de H3 si parece ser celda H3 (empieza con números)
        # De lo contrario, las coordenadas vendrán del merge con zone_meta
        sample_zone = df[zone_key].iloc[0] if not df.empty else None
        is_h3 = sample_zone and isinstance(
            sample_zone, str) and sample_zone[0].isdigit()

        if is_h3:
            centers = df[zone_key].apply(_h3_center)
            df["lat"] = centers.apply(lambda x: x[0] if x else pd.NA)
            df["lon"] = centers.apply(lambda x: x[1] if x else pd.NA)

        if zone_meta is not None and not zone_meta.empty:
            df = _merge_with_zone_meta(df, zone_meta, how="left")
        if geocode:
            cache = _load_geocode_cache()
            df = df.merge(cache, left_on=zone_key,
                          right_on="id_zona", how="left")
            missing = df[df["address"].isna()].head(10)
            new_rows = []
            for _, row in missing.iterrows():
                lat = row.get("lat")
                lon = row.get("lon")
                if pd.isna(lat) or pd.isna(lon):
                    continue
                address = _reverse_geocode(float(lat), float(lon))
                if address:
                    new_rows.append(
                        {"id_zona": row.get(zone_key), "address": address})
                time.sleep(1.0)
            if new_rows:
                cache = pd.concat([cache, pd.DataFrame(new_rows)],
                                  ignore_index=True).drop_duplicates("id_zona")
                _save_geocode_cache(cache)
                df = df.drop(columns=["address"]).merge(
                    cache, left_on=zone_key, right_on="id_zona", how="left")
        return df

    # Note: geocode_enabled moved to Executive Brief tab
    zone_key = _get_zone_key(incidents)
    if not incidents.empty and zone_key:
        meta_cols = []
        if "alcaldia_catalogo" in incidents.columns:
            meta_cols.append("alcaldia_catalogo")
        if "colonia_catalogo" in incidents.columns:
            meta_cols.append("colonia_catalogo")
        if meta_cols:
            zone_meta = (
                incidents.groupby(zone_key, dropna=False)[meta_cols]
                .agg(lambda x: x.mode().iloc[0] if not x.mode().empty else pd.NA)
                .reset_index()
            )
        zone_counts = incidents.groupby(
            zone_key, dropna=False).size().sort_values(ascending=False).head(5)
        total_inc = len(incidents)
        share = zone_counts.sum() / total_inc if total_inc else 0
        st.markdown(
            f"Principales zonas de incidentes (principales 5 = {share:.1%} de incidentes)")
        table = _zone_table(zone_counts, "incidentes",
                            zone_meta, geocode=False)
        table = table.rename(
            columns={"alcaldia_catalogo": "alcaldia", "colonia_catalogo": "colonia"})
        table = table.drop(columns=["id_zona"], errors="ignore")
        notes = []
        used = set()
        for _, row in table.head(5).iterrows():
            label = _unique_label(_zone_label(row), row, used)
            count = row.get("incidentes")
            severity = "note-med"
            if total_inc:
                ratio = float(count) / total_inc if pd.notna(count) else 0
                if ratio >= 0.12:
                    severity = "note-high"
                elif ratio <= 0.05:
                    severity = "note-low"
            body = f"Incidentes: {int(count):,}" if pd.notna(count) else "Incidentes: n/d"
            notes.append(
                {
                    "title": label,
                    "body": body,
                    "severity": severity,
                }
            )
        _render_notes("Zonas con mayor volumen de incidentes", notes)

        principales_row = table.iloc[0] if not table.empty else None
        if principales_row is not None:
            st.markdown(
                f"Punto caliente: {_zone_label(principales_row)} lidera el volumen de incidentes en esta ventana.")

    pressure = analytics.get("c5_pressure", pd.DataFrame())
    anomalies = analytics.get("c5_anomalies", pd.DataFrame())

    # Normalizar nombre de columna zone_id -> id_zona si viene de analytics
    if not pressure.empty and "zone_id" in pressure.columns:
        pressure = pressure.rename(columns={"zone_id": "id_zona"})

    inc_zone_key = _get_zone_key(incidents)
    stops_zone_key = _get_zone_key(stops)
    if pressure.empty and not incidents.empty and not stops.empty and inc_zone_key and stops_zone_key:
        inc = incidents.groupby(
            inc_zone_key, dropna=False).size().rename("Incidentes")
        stp = stops.groupby(
            stops_zone_key, dropna=False).size().rename("Paradas")
        pressure = (
            pd.concat([inc, stp], axis=1)
            .fillna(0)
            .assign(incidents_per_stop=lambda df: df["Incidentes"] / (df["Paradas"] + 1))
            .reset_index()
            .rename(columns={"index": "id_zona"})
        )


    if not pressure.empty:
        principales5 = pressure.sort_values("risk_z", ascending=False).head(5)
        if not zone_meta.empty:
            principales5 = _merge_with_zone_meta(principales5, zone_meta)
            principales5 = principales5.rename(
                columns={"alcaldia_catalogo": "alcaldia", "colonia_catalogo": "colonia"})
        notes = []
        used = set()
        for _, row in principales5.iterrows():
            label = _unique_label(_zone_label(row), row, used)
            if label == "Área desconocida":
                raw_id = row.get("id_zona") or row.get("zone_id")
                if pd.notna(raw_id):
                    label = f"Zona {raw_id}"
            risk = row.get("risk_z")
            severity = "note-low"
            if pd.notna(risk):
                if risk >= 2:
                    severity = "note-high"
                elif risk >= 1:
                    severity = "note-med"
            parts = []
            if "incidentes" in row and pd.notna(row["incidentes"]):
                parts.append(f"Incidentes: {int(row['incidentes']):,}")
            if "paradas" in row and pd.notna(row["paradas"]):
                parts.append(f"Paradas: {int(row['paradas']):,}")
            if "incidents_per_stop" in row and pd.notna(row["incidents_per_stop"]):
                parts.append(f"Inc/Parada: {row['incidents_per_stop']:.2f}")
            if pd.notna(risk):
                parts.append(f"Riesgo z: {risk:.2f}")
            notes.append(
                {
                    "title": label,
                    "body": " | ".join(parts) if parts else "Sin detalles adicionales.",
                    "severity": severity,
                }
            )
        _render_notes("Prioridades inmediatas (zonas de riesgo)", notes)


    if not acceso.empty:
        low_acceso = acceso.sort_values("acceso_score", ascending=True).head(5)
        if not zone_meta.empty:
            low_acceso = _merge_with_zone_meta(low_acceso, zone_meta)
            low_acceso = low_acceso.rename(
                columns={"alcaldia_catalogo": "alcaldia", "colonia_catalogo": "colonia"})
        notes = []
        used = set()
        for _, row in low_acceso.iterrows():
            label = _unique_label(_zone_label(row), row, used)
            if label == "Área desconocida":
                raw_id = row.get("id_zona") or row.get("zone_id")
                if pd.notna(raw_id):
                    label = f"Zona {raw_id}"
            score = row.get("acceso_score")
            severity = "note-low"
            if pd.notna(score):
                if score <= 0.35:
                    severity = "note-high"
                elif score <= 0.55:
                    severity = "note-med"
            parts = []
            if pd.notna(score):
                parts.append(f"Acceso: {score:.2f}")
            if "travel_time_min" in row and pd.notna(row["travel_time_min"]):
                parts.append(f"Tiempo a parada: {row['travel_time_min']:.1f} min")
            if "paradas" in row and pd.notna(row["paradas"]):
                parts.append(f"Paradas: {int(row['paradas']):,}")
            notes.append(
                {
                    "title": label,
                    "body": " | ".join(parts) if parts else "Sin detalles adicionales.",
                    "severity": severity,
                }
            )
        _render_notes("Zonas de menor acceso (candidatas para expansión)", notes)

    actions = []
    if not pressure.empty:
        principales = pressure.sort_values("risk_z", ascending=False).head(3)
        for _, row in principales.iterrows():
            zone_label = row.get("alcaldia_catalogo") or row.get(
                "alcaldia") or "Área desconocida"
            actions.append(
                {
                    "prioridad": "Alto",
                    "enfoque": zone_label,
                    "accion": "Vigilancia dirigida + pacificacion",
                    "razon": f"Puntaje z de riesgo {row['risk_z']:.2f}",
                }
            )
    if not acceso.empty:
        low = acceso.sort_values("acceso_score", ascending=True).head(2)
        for _, row in low.iterrows():
            actions.append(
                {
                    "prioridad": "Medio",
                    "enfoque": row.get("alcaldia_catalogo") or row.get("alcaldia") or "Área desconocida",
                    "accion": "Expandir cobertura de paradas / plan ultima milla",
                    "razon": f"Puntaje de acceso {row['acceso_score']:.2f}",
                }
            )
    if not anomalies.empty:
        spike = anomalies.sort_values("zscore", ascending=False).head(1)
        if not spike.empty:
            actions.append(
                {
                    "prioridad": "Alto",
                    "enfoque": f"Fecha {spike['date'].iloc[0]}",
                    "accion": "Investigar causas del pico",
                    "razon": f"+{spike['zscore'].iloc[0]:.2f} sigma",
                }
            )

    if actions:
        notes = []
        for action in actions[:5]:
            prioridad = action.get("prioridad", "Medio")
            severity = "note-med"
            if prioridad.lower().startswith("alto"):
                severity = "note-high"
            elif prioridad.lower().startswith("bajo"):
                severity = "note-low"
            body = f"{action.get('accion', '')} | {action.get('razon', '')}".strip(" |")
            notes.append(
                {
                    "title": action.get("enfoque", "Acción prioritaria"),
                    "body": body or "Sin detalles adicionales.",
                    "severity": severity,
                }
            )
        _render_notes("Acciones recomendadas", notes)

    c5_zone_daily = analytics.get("c5_zone_daily", pd.DataFrame())
    if not c5_zone_daily.empty:
        recent = c5_zone_daily.dropna(subset=["date"]).copy()
        recent["date"] = pd.to_datetime(recent["date"], errors="coerce")
        recent = recent.sort_values("date")
        last_date = recent["date"].max()
        if pd.notna(last_date):
            last_7_start = last_date - pd.Timedelta(days=6)
            prev_7_start = last_date - pd.Timedelta(days=13)
            prev_7_end = last_date - pd.Timedelta(days=7)

            last7 = recent[(recent["date"] >= last_7_start)
                           & (recent["date"] <= last_date)]
            prev7 = recent[(recent["date"] >= prev_7_start)
                           & (recent["date"] <= prev_7_end)]

            # Detectar la clave de zona antes del groupby y eliminar duplicados
            zone_key = _get_zone_key(last7)
            if zone_key:
                # Asegurar que la columna zone_key no esté duplicada
                if isinstance(last7[zone_key], pd.DataFrame):
                    # Si es DataFrame (columna duplicada), tomar solo la primera
                    last7 = last7.loc[:, ~last7.columns.duplicated()]
                    prev7 = prev7.loc[:, ~prev7.columns.duplicated()]

                last7_sum = last7.groupby(zone_key, dropna=False)[
                    "count"].sum().rename("last7")
                prev7_sum = prev7.groupby(zone_key, dropna=False)[
                    "count"].sum().rename("prev7")
                delta = pd.concat([last7_sum, prev7_sum], axis=1).fillna(0)
                delta["delta_pct"] = (
                    delta["last7"] - delta["prev7"]) / (delta["prev7"] + 1)
                delta = delta.reset_index().sort_values("delta_pct", ascending=False).head(10)

                if not zone_meta.empty:
                    right_key = _get_zone_key(zone_meta)
                    if right_key:
                        delta = delta.merge(
                            zone_meta, left_on=zone_key, right_on=right_key, how="left")

                notes = []
                used = set()
                for _, row in delta.head(6).iterrows():
                    label = _unique_label(_zone_label(row), row, used)
                    if label == "Área desconocida":
                        raw_id = row.get(zone_key)
                        if pd.notna(raw_id):
                            label = f"Zona {raw_id}"
                    pct = row.get("delta_pct")
                    severity = "note-low"
                    if pd.notna(pct):
                        if pct >= 0.5:
                            severity = "note-high"
                        elif pct >= 0.2:
                            severity = "note-med"
                    parts = []
                    if pd.notna(pct):
                        parts.append(f"Variación: {pct:+.0%}")
                    if "last7" in row and pd.notna(row.get("last7")):
                        parts.append(f"Últimos 7d: {int(row['last7']):,}")
                    if "prev7" in row and pd.notna(row.get("prev7")):
                        parts.append(f"7d previos: {int(row['prev7']):,}")
                    notes.append(
                        {
                            "title": label,
                            "body": " | ".join(parts) if parts else "Sin detalles adicionales.",
                            "severity": severity,
                        }
                    )
                _render_notes(
                    "Puntos calientes emergentes (últimos 7d vs 7d anteriores)",
                    notes,
                )

                if not zone_meta.empty and "alcaldia" in delta.columns:
                    alc_delta = (
                        delta.groupby("alcaldia", dropna=False)["delta_pct"]
                        .mean()
                        .sort_values(ascending=False)
                        .head(6)
                        .reset_index()
                    )
                    notes = []
                    for _, row in alc_delta.iterrows():
                        pct = row.get("delta_pct")
                        severity = "note-low"
                        if pd.notna(pct):
                            if pct >= 0.5:
                                severity = "note-high"
                            elif pct >= 0.2:
                                severity = "note-med"
                        notes.append(
                            {
                                "title": str(row.get("alcaldia", "Alcaldía")),
                                "body": f"Variación media: {pct:+.0%}" if pd.notna(pct) else "Sin detalles adicionales.",
                                "severity": severity,
                            }
                        )
                    _render_notes("Hotspots emergentes por alcaldía", notes)


def _render_exec_brief(
    incidents: pd.DataFrame,
    trips: pd.DataFrame,
    stops: pd.DataFrame,
    date_range: tuple[pd.Timestamp, pd.Timestamp],
    analytics: dict[str, pd.DataFrame],
) -> None:
    _render_insights(incidents, trips, stops, date_range, analytics)


def _render_exec_header(
    incidents: pd.DataFrame,
    trips: pd.DataFrame,
    analytics: dict[str, pd.DataFrame],
) -> None:
    pressure = analytics.get("c5_pressure", pd.DataFrame())
    acceso = analytics.get("accesoibility_zones", pd.DataFrame())

    risk_z = None
    if not pressure.empty and "risk_z" in pressure.columns:
        risk_z = float(pressure["risk_z"].max())

    acceso_avg = None
    if not acceso.empty and "acceso_score" in acceso.columns:
        acceso_avg = float(acceso["acceso_score"].mean())

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        _metric_with_tooltip(
            "Incidentes (filtrados)",
            f"{len(incidents):,}",
            "Total de incidentes en el rango de fechas y filtros seleccionados.",
            None,
        )
    with col2:
        _metric_with_tooltip(
            "Viajes ECOBICI (filtrados)",
            f"{len(trips):,}",
            "Total de viajes ECOBICI en el rango de fechas y filtros seleccionados.",
            None,
        )
    with col3:
        _metric_with_tooltip(
            "Riesgo z max",
            f"{risk_z:.2f}" if risk_z is not None else "n/d",
            "Máximo puntaje z de riesgo (incidentes vs exposición). Valores altos indican zonas críticas.",
            None,
        )
    with col4:
        _metric_with_tooltip(
            "Acceso promedio",
            f"{acceso_avg:.2f}" if acceso_avg is not None else "n/d",
            "Promedio del puntaje de accesibilidad (0 a 1). Valores bajos indican baja cobertura.",
            None,
        )

    alerts = []
    if risk_z is not None and risk_z >= 2.0:
        alerts.append(
            {
                "title": "Riesgo elevado",
                "body": f"Riesgo z max {risk_z:.2f}",
                "severity": "note-high",
                "hint": "Umbral activado: riesgo z >= 2.0 (incidentes inusualmente altos).",
            }
        )
    if acceso_avg is not None and acceso_avg <= 0.35:
        alerts.append(
            {
                "title": "Acceso bajo",
                "body": f"Acceso promedio {acceso_avg:.2f}",
                "severity": "note-med",
                "hint": "Umbral activado: acceso promedio <= 0.35 (cobertura limitada).",
            }
        )
    if alerts:
        _render_notes("Alertas", alerts)


def _render_decision_intel(incidents: pd.DataFrame) -> None:
    st.subheader("Alertas y Prioridades")
    with st.expander("Finalidad de esta vista", expanded=False):
        st.markdown(
            "Identificar zonas y periodos que requieren atencion inmediata: "
            "picos estadisticos, crecimiento semana a semana y persistencia de hotspots."
        )

    if incidents.empty or "timestamp" not in incidents.columns:
        st.info("No hay datos de incidentes para analizar alertas.")
        return

    df = incidents.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    if df.empty:
        st.info("No hay fechas validas para analizar.")
        return

    zone_key = _get_zone_key(df)
    zone_meta = _load_zone_metadata_v4()

    daily_total = df.groupby(df["timestamp"].dt.date).size().rename("count").reset_index()
    daily_total["zscore"] = (daily_total["count"] - daily_total["count"].mean()) / (
        daily_total["count"].std(ddof=0) + 1e-6
    )
    top_daily = daily_total.sort_values("zscore", ascending=False).head(5)
    notes = []
    for _, row in top_daily.iterrows():
        severity = "note-high" if row["zscore"] >= 2 else "note-med"
        notes.append(
            {
                "title": f"Fecha {row['timestamp']}",
                "body": f"Incidentes: {int(row['count']):,} | z={row['zscore']:.2f}",
                "severity": severity,
            }
        )
    _render_notes("Picos diarios (alertas)", notes)

    if not zone_key:
        st.info("No hay zona para calcular crecimiento o persistencia.")
        return

    daily = (
        df.groupby([df["timestamp"].dt.date, zone_key])
        .size()
        .reset_index(name="count")
        .rename(columns={"timestamp": "date"})
    )
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    total_days = daily["date"].nunique()

    if total_days >= 14:
        last_date = daily["date"].max()
        last_7_start = last_date - pd.Timedelta(days=6)
        prev_7_start = last_date - pd.Timedelta(days=13)
        prev_7_end = last_date - pd.Timedelta(days=7)

        last7 = daily[(daily["date"] >= last_7_start) & (daily["date"] <= last_date)]
        prev7 = daily[(daily["date"] >= prev_7_start) & (daily["date"] <= prev_7_end)]

        last7_sum = last7.groupby(zone_key)["count"].sum().rename("last7")
        prev7_sum = prev7.groupby(zone_key)["count"].sum().rename("prev7")
        growth = pd.concat([last7_sum, prev7_sum], axis=1).fillna(0)
        growth["delta_pct"] = (growth["last7"] - growth["prev7"]) / (growth["prev7"] + 1)
        growth = growth.reset_index().sort_values("delta_pct", ascending=False).head(6)

        if not zone_meta.empty:
            growth = _merge_with_zone_meta(growth, zone_meta)

        notes = []
        for _, row in growth.iterrows():
            label = row.get("alcaldia") or row.get("colonia") or row.get(zone_key) or "Zona"
            pct = row.get("delta_pct", 0)
            severity = "note-high" if pct >= 0.5 else "note-med" if pct >= 0.2 else "note-low"
            notes.append(
                {
                    "title": str(label),
                    "body": f"Crecimiento: {pct:+.0%} | 7d: {int(row['last7']):,}",
                    "severity": severity,
                }
            )
        _render_notes("Crecimiento semana a semana", notes)
    else:
        st.info("Se requieren al menos 14 dias para crecimiento semana a semana.")

    if total_days >= 5:
        top = daily.sort_values(["date", "count"], ascending=[True, False]).copy()
        top["rank"] = top.groupby("date")["count"].rank(method="first", ascending=False)
        top = top[top["rank"] <= 10]
        persistence = top.groupby(zone_key).size().rename("dias_top10").reset_index()
        persistence["persistence"] = persistence["dias_top10"] / total_days
        persistence = persistence.sort_values("persistence", ascending=False).head(6)
        if not zone_meta.empty:
            persistence = _merge_with_zone_meta(persistence, zone_meta)

        notes = []
        for _, row in persistence.iterrows():
            label = row.get("alcaldia") or row.get("colonia") or row.get(zone_key) or "Zona"
            pct = row.get("persistence", 0)
            severity = "note-high" if pct >= 0.5 else "note-med" if pct >= 0.3 else "note-low"
            notes.append(
                {
                    "title": str(label),
                    "body": f"Presencia: {pct:.0%} de los dias",
                    "severity": severity,
                }
            )
        _render_notes("Persistencia de hotspots", notes)
    else:
        st.info("Se requieren al menos 5 dias para persistencia de hotspots.")


def _render_trends(incidents: pd.DataFrame, trips: pd.DataFrame) -> None:
    st.subheader("Tendencias operativas")

    def _prep(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "timestamp" not in df.columns:
            return pd.DataFrame()
        df = df.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        return df

    inc = _prep(incidents)
    if inc.empty:
        st.info("No hay datos para mostrar tendencias.")
        return

    def _monthly(df: pd.DataFrame, label: str) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["month", "count", "serie"])
        monthly = (
            df.groupby(df["timestamp"].dt.to_period("M"))
            .size()
            .rename("count")
            .reset_index()
        )
        monthly = monthly.rename(columns={"timestamp": "month"})
        monthly["serie"] = label
        return monthly[["month", "count", "serie"]]

    inc_monthly = _monthly(inc, "Incidentes")

    if inc_monthly.empty:
        st.info("No hay datos mensuales para mostrar.")
        return

    all_months = pd.period_range(
        inc_monthly["month"].min(),
        inc_monthly["month"].max(),
        freq="M",
    )
    inc_monthly = (
        inc_monthly.set_index("month")
        .reindex(all_months, fill_value=0)
        .reset_index()
        .rename(columns={"index": "month"})
    )
    inc_monthly["serie"] = "Incidentes"
    inc_monthly["month_str"] = inc_monthly["month"].astype(str)
    mean = inc_monthly["count"].mean()
    std = inc_monthly["count"].std(ddof=0)
    if std == 0 or pd.isna(std):
        inc_monthly["zscore"] = 0.0
    else:
        inc_monthly["zscore"] = (inc_monthly["count"] - mean) / std

    def _coverage_text(df: pd.DataFrame, label: str) -> str:
        if df.empty or "timestamp" not in df.columns:
            return f"{label}: sin datos"
        ts = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
        if ts.empty:
            return f"{label}: sin datos"
        months = ts.dt.to_period("M").nunique()
        return f"{label}: {ts.min().date()} -> {ts.max().date()} ({months} meses)"

    st.caption("Cobertura mensual - " + _coverage_text(inc, "Incidentes"))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=inc_monthly["month_str"],
            y=inc_monthly["count"],
            mode="lines+markers",
            name="Incidentes",
        )
    )
    fig = apply_plotly_theme(fig, "Tendencia mensual (Incidentes)", 320)
    fig.update_xaxes(title_text="Mes")
    fig.update_yaxes(title_text="Conteo")
    st.plotly_chart(fig, width="stretch", key="trend_month")

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=inc_monthly["month_str"],
            y=inc_monthly["zscore"],
            name="Anomalía z-score",
        )
    )
    fig.add_hline(y=0, line_dash="dash", line_color="rgba(255,255,255,0.25)")
    fig = apply_plotly_theme(fig, "Anomalías mensuales (z-score)", 220)
    fig.update_xaxes(title_text="Mes")
    fig.update_yaxes(title_text="Z-score")
    st.plotly_chart(fig, width="stretch", key="trend_month_zscore")

    def _hourly(df: pd.DataFrame, label: str) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["hour", "count", "serie"])
        hourly = df.groupby(df["timestamp"].dt.hour).size().rename("count").reset_index()
        hourly["serie"] = label
        return hourly.rename(columns={"timestamp": "hour"})

    hourly_df = _hourly(inc, "Incidentes")

    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    day_map = {
        "Monday": "Lunes",
        "Tuesday": "Martes",
        "Wednesday": "Miercoles",
        "Thursday": "Jueves",
        "Friday": "Viernes",
        "Saturday": "Sabado",
        "Sunday": "Domingo",
    }

    def _dow(df: pd.DataFrame, label: str) -> pd.DataFrame:
        if df.empty:
            return pd.DataFrame(columns=["day", "count", "serie"])
        dow = df["timestamp"].dt.day_name().value_counts().reindex(day_order, fill_value=0)
        return pd.DataFrame({"day": [day_map[d] for d in day_order], "count": dow.values, "serie": label})

    dow_df = _dow(inc, "Incidentes")

    col1, col2 = st.columns(2)
    with col1:
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=hourly_df["hour"],
                y=hourly_df["count"],
                name="Incidentes",
            )
        )
        fig = apply_plotly_theme(fig, "Distribucion por hora", 320)
        fig.update_xaxes(title_text="Hora del dia")
        fig.update_yaxes(title_text="Conteo")
        st.plotly_chart(fig, width="stretch", key="trend_hour")

    with col2:
        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=dow_df["day"],
                y=dow_df["count"],
                name="Incidentes",
            )
        )
        fig = apply_plotly_theme(fig, "Distribucion por dia", 320)
        fig.update_xaxes(title_text="Dia de la semana")
        fig.update_yaxes(title_text="Conteo")
        st.plotly_chart(fig, width="stretch", key="trend_dow")


def _render_ppi(analytics: dict[str, pd.DataFrame]) -> None:
    st.subheader("Indice de Prioridad")
    with st.expander("Finalidad de esta vista", expanded=False):
        st.markdown(
            "Priorizar zonas de intervencion combinando incidentes y exposicion."
        )
    ppi = analytics.get("ppi", pd.DataFrame())
    if not ppi.empty and "zone_id" in ppi.columns:
        ppi = ppi.rename(columns={"zone_id": "id_zona"})
    if ppi.empty:
        st.info("No hay datos de Indice de Prioridad.")
        return

    principales = ppi.sort_values("ppi", ascending=False).head(10)
    bottom = ppi.sort_values("ppi", ascending=True).head(10)
    zone_meta = _load_zone_metadata_v4()
    if not zone_meta.empty:
        principales = _merge_with_zone_meta(principales, zone_meta)
        bottom = _merge_with_zone_meta(bottom, zone_meta)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("Zonas con mayor prioridad")
        st.dataframe(_display_df(principales), width="stretch")
    with col2:
        st.markdown("Zonas con menor prioridad")
        st.dataframe(_display_df(bottom), width="stretch")


def _render_forecast_xgb(incidents: pd.DataFrame) -> None:
    st.subheader("Pronostico a 7 dias")
    with st.expander("Finalidad de esta vista", expanded=False):
        st.markdown(
            "Pronostico operativo con modelos de boosting, "
            "entrenado con el rango seleccionado. Se muestra split 80/20 "
            "y un pronostico de 7 dias con bandas 95%."
        )

    if incidents.empty or "timestamp" not in incidents.columns:
        st.info("No hay datos de incidentes para pronosticar.")
        return

    try:
        from sklearn.metrics import mean_absolute_error, mean_squared_error
    except Exception:
        st.error("scikit-learn no esta instalado. Ejecuta: pip install scikit-learn")
        return

    df = incidents.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    df = df.dropna(subset=["timestamp"])
    if df.empty:
        st.info("No hay fechas validas para pronosticar.")
        return

    daily = (
        df.groupby(df["timestamp"].dt.date)
        .size()
        .reset_index(name="count")
        .rename(columns={"timestamp": "date"})
        .sort_values("date")
    )
    daily["date"] = pd.to_datetime(daily["date"])
    span_days = (daily["date"].max() - daily["date"].min()).days + 1
    if span_days < 21:
        st.info("Se requieren al menos 21 dias de datos para entrenar y validar el modelo.")
        return

    daily = daily.set_index("date").asfreq("D", fill_value=0)
    last_date = daily.index.max()

    model_choice = st.selectbox(
        "Modelo de pronostico",
        ["XGBoost", "LightGBM", "CatBoost"],
        index=0,
    )
    wide_view = st.toggle(
        "Vista amplia (apilar graficas)",
        value=False,
        help="Activalo para ver cada grafico en ancho completo.",
    )
    chart_height = 420

    def _build_features(series: pd.Series, lags: int = 7) -> pd.DataFrame:
        data = pd.DataFrame({"y": series})
        for i in range(1, lags + 1):
            data[f"lag_{i}"] = data["y"].shift(i)
        data["dow"] = data.index.dayofweek
        data["week"] = data.index.isocalendar().week.astype(int)
        data["month"] = data.index.month
        data["trend"] = np.arange(len(data))
        return data.dropna()

    feats = _build_features(daily["count"], lags=7)
    X = feats.drop(columns=["y"])
    y = feats["y"]

    split_idx = int(len(X) * 0.8)
    if split_idx < 10 or split_idx >= len(X):
        st.info("No hay datos suficientes para el split 80/20.")
        return

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    y_pred_test = None
    resid_std = 0.0
    forecast_df = pd.DataFrame()

    if model_choice == "XGBoost":
        try:
            import xgboost as xgb
        except Exception:
            st.error("XGBoost no esta instalado. Ejecuta: pip install xgboost scikit-learn")
            return
        model = xgb.XGBRegressor(
            n_estimators=400,
            max_depth=4,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            objective="reg:squarederror",
            random_state=42,
        )
        model.fit(X_train, y_train)
        y_pred_test = pd.Series(model.predict(X_test), index=y_test.index)

        residuals = (y_test - y_pred_test).to_numpy()
        resid_std = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0

        history = daily["count"].copy()
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 8)]
        preds = []
        for fdate in future_dates:
            temp = history.copy()
            temp.loc[fdate] = temp.iloc[-1]
            feat_row = _build_features(temp, lags=7).iloc[-1]
            pred = float(model.predict(feat_row.drop(labels=["y"]).to_frame().T)[0])
            pred = max(pred, 0.0)
            preds.append(pred)
            history.loc[fdate] = pred

        forecast_df = pd.DataFrame(
            {"date": future_dates, "count": np.round(preds, 0).astype(int)}
        )
        forecast_df["lower"] = np.clip(forecast_df["count"] - 1.96 * resid_std, 0, None)
        forecast_df["upper"] = forecast_df["count"] + 1.96 * resid_std
    elif model_choice == "LightGBM":
        try:
            import lightgbm as lgb
        except Exception:
            st.error("LightGBM no esta instalado. Ejecuta: pip install lightgbm scikit-learn")
            return
        model = lgb.LGBMRegressor(
            n_estimators=400,
            max_depth=-1,
            learning_rate=0.05,
            subsample=0.85,
            colsample_bytree=0.85,
            random_state=42,
        )
        model.fit(X_train, y_train)
        y_pred_test = pd.Series(model.predict(X_test), index=y_test.index)

        residuals = (y_test - y_pred_test).to_numpy()
        resid_std = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0

        history = daily["count"].copy()
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 8)]
        preds = []
        for fdate in future_dates:
            temp = history.copy()
            temp.loc[fdate] = temp.iloc[-1]
            feat_row = _build_features(temp, lags=7).iloc[-1]
            pred = float(model.predict(feat_row.drop(labels=["y"]).to_frame().T)[0])
            pred = max(pred, 0.0)
            preds.append(pred)
            history.loc[fdate] = pred

        forecast_df = pd.DataFrame(
            {"date": future_dates, "count": np.round(preds, 0).astype(int)}
        )
        forecast_df["lower"] = np.clip(forecast_df["count"] - 1.96 * resid_std, 0, None)
        forecast_df["upper"] = forecast_df["count"] + 1.96 * resid_std
    elif model_choice == "CatBoost":
        try:
            from catboost import CatBoostRegressor
        except Exception:
            st.error("CatBoost no esta instalado. Ejecuta: pip install catboost scikit-learn")
            return
        model = CatBoostRegressor(
            iterations=500,
            depth=6,
            learning_rate=0.05,
            loss_function="RMSE",
            random_seed=42,
            verbose=False,
        )
        model.fit(X_train, y_train)
        y_pred_test = pd.Series(model.predict(X_test), index=y_test.index)

        residuals = (y_test - y_pred_test).to_numpy()
        resid_std = float(np.std(residuals, ddof=1)) if len(residuals) > 1 else 0.0

        history = daily["count"].copy()
        future_dates = [last_date + pd.Timedelta(days=i) for i in range(1, 8)]
        preds = []
        for fdate in future_dates:
            temp = history.copy()
            temp.loc[fdate] = temp.iloc[-1]
            feat_row = _build_features(temp, lags=7).iloc[-1]
            pred = float(model.predict(feat_row.drop(labels=["y"]).to_frame().T)[0])
            pred = max(pred, 0.0)
            preds.append(pred)
            history.loc[fdate] = pred

        forecast_df = pd.DataFrame(
            {"date": future_dates, "count": np.round(preds, 0).astype(int)}
        )
        forecast_df["lower"] = np.clip(forecast_df["count"] - 1.96 * resid_std, 0, None)
        forecast_df["upper"] = forecast_df["count"] + 1.96 * resid_std
    else:
        st.error("Modelo no soportado.")
        return

    mse = float(mean_squared_error(y_test, y_pred_test))
    rmse = float(np.sqrt(mse))
    mae = float(mean_absolute_error(y_test, y_pred_test))
    avg_test = float(np.mean(y_test)) if len(y_test) else 0.0
    nrmse = (rmse / avg_test) if avg_test > 0 else np.nan
    nmae = (mae / avg_test) if avg_test > 0 else np.nan
    denom = float(np.sum(np.abs(y_test)))
    wmape = (np.sum(np.abs(y_test - y_pred_test)) / denom * 100) if denom > 0 else np.nan

    def _fmt_pct(val: float) -> str:
        return "NA" if pd.isna(val) else f"{val:.1f}%"

    metrics_df = pd.DataFrame(
        [
            {
                "Metrica": "RMSE",
                "Valor": f"{rmse:,.2f}" + (f" (nRMSE {_fmt_pct(nrmse * 100)})" if not pd.isna(nrmse) else ""),
                "Que mide": "Error tipico penalizando mas los errores grandes.",
                "Guia (orientativa)": "nRMSE <10% excelente; 10-20% bueno; 20-30% regular; >30% debil.",
            },
            {
                "Metrica": "MAE",
                "Valor": f"{mae:,.2f}" + (f" (nMAE {_fmt_pct(nmae * 100)})" if not pd.isna(nmae) else ""),
                "Que mide": "Error promedio absoluto (mas robusto a outliers).",
                "Guia (orientativa)": "nMAE <10% excelente; 10-20% bueno; 20-30% regular; >30% debil.",
            },
            {
                "Metrica": "WMAPE",
                "Valor": _fmt_pct(wmape),
                "Que mide": "Error absoluto ponderado por el volumen total de la serie.",
                "Guia (orientativa)": "<10% excelente; 10-20% bueno; 20-30% regular; >30% debil.",
            },
        ]
    )
    st.markdown("Desempeno del modelo (prueba)")
    st.dataframe(_display_df(metrics_df), width="stretch")

    # Preparar descargas
    train_df = pd.DataFrame(
        {
            "date": y_train.index,
            "y": y_train.values,
            "split": "train",
            "y_pred": np.nan,
        }
    )
    test_df = pd.DataFrame(
        {
            "date": y_test.index,
            "y": y_test.values,
            "split": "test",
            "y_pred": y_pred_test.values if hasattr(y_pred_test, "values") else y_pred_test,
        }
    )
    train_test_df = pd.concat([train_df, test_df], ignore_index=True)
    forecast_out = forecast_df.copy()
    forecast_out["model"] = model_choice
    forecast_out["generated_at"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    metrics_out = metrics_df.copy()
    metrics_out["model"] = model_choice

    train_start = y_train.index.min()
    train_end = y_train.index.max()
    test_start = y_test.index.min()
    test_end = y_test.index.max()
    st.markdown(
        f"**Entrenamiento:** {train_start:%Y-%m-%d} a {train_end:%Y-%m-%d} ({len(y_train)} dias)"
    )
    st.markdown(
        f"**Prueba:** {test_start:%Y-%m-%d} a {test_end:%Y-%m-%d} ({len(y_test)} dias)"
    )

    def _render_train_test_chart() -> None:
        split_line = y_test.index.min()
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=y_train.index,
                y=y_train.values,
                mode="lines",
                name="Entrenamiento",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=y_test.index,
                y=y_test.values,
                mode="lines",
                name="Prueba",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=y_pred_test.index,
                y=y_pred_test.values,
                mode="lines",
                name="Prediccion (prueba)",
                line=dict(dash="dot"),
            )
        )
        fig.add_vline(x=split_line, line_dash="dash", line_color="#f26457")
        fig = apply_plotly_theme(fig, "Entrenamiento vs Prueba (80/20)", chart_height)
        fig.update_xaxes(title_text="Fecha")
        fig.update_yaxes(title_text="Conteo")
        st.plotly_chart(fig, width="stretch", key="train_test")

    def _render_forecast_chart() -> None:
        last_real = daily.loc[
            daily.index >= (last_date - pd.Timedelta(days=13))
        ].reset_index().rename(columns={"count": "y"})
        plot_real = last_real.assign(tipo="Real")
        plot_forecast = forecast_df.rename(columns={"count": "y"}).assign(tipo="Pronostico")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=plot_real["date"],
                y=plot_real["y"],
                mode="lines+markers",
                name="Real (14 dias)",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=plot_forecast["date"],
                y=plot_forecast["y"],
                mode="lines+markers",
                name="Pronostico (7 dias)",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=forecast_df["date"],
                y=forecast_df["upper"],
                mode="lines",
                name="IC 95% (superior)",
                line=dict(color="rgba(242,100,87,0.35)", dash="dash"),
            )
        )
        fig.add_trace(
            go.Scatter(
                x=forecast_df["date"],
                y=forecast_df["lower"],
                mode="lines",
                name="IC 95% (inferior)",
                line=dict(color="rgba(242,100,87,0.35)", dash="dash"),
                fill="tonexty",
                fillcolor="rgba(242,100,87,0.12)",
            )
        )
        fig = apply_plotly_theme(
            fig,
            f"Pronostico 7 dias (14 dias historicos) - {model_choice}",
            chart_height,
        )
        fig.update_xaxes(title_text="Fecha")
        fig.update_yaxes(title_text="Conteo")
        st.plotly_chart(fig, width="stretch", key="forecast")

    if wide_view:
        _render_train_test_chart()
        _render_forecast_chart()
    else:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            _render_train_test_chart()
        with col2:
            _render_forecast_chart()

    st.markdown("Tabla de pronostico (7 dias)")
    st.dataframe(_display_df(forecast_df), width="stretch")

    st.markdown("Descargas")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.download_button(
            "Descargar entrenamiento/prueba (CSV)",
            data=export_dataframe_to_csv(train_test_df),
            file_name="forecast_train_test.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Descargar pronostico 7d (CSV)",
            data=export_dataframe_to_csv(forecast_out),
            file_name="forecast_7d.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c3:
        st.download_button(
            "Descargar metricas (CSV)",
            data=export_dataframe_to_csv(metrics_out),
            file_name="forecast_metrics.csv",
            mime="text/csv",
            use_container_width=True,
        )


def _render_data_quality(data: dict[str, pd.DataFrame], analytics: dict[str, pd.DataFrame]) -> None:
    st.subheader("Calidad y Procesamiento")
    with st.expander("Finalidad de esta vista", expanded=False):
        st.markdown(
            "Monitorear cobertura, frescura y completitud de los datos, "
            "y el estado de los analiticos clave."
        )

    dataset_map = {
        "Incidentes C5": data.get("incidentes", pd.DataFrame()),
        "Viajes ECOBICI": data.get("viajes", pd.DataFrame()),
        "Paradas (GTFS)": data.get("paradas", pd.DataFrame()),
        "Estaciones ECOBICI": data.get("estaciones", pd.DataFrame()),
    }

    coverage_rows = []
    for name, df in dataset_map.items():
        if df.empty or "timestamp" not in df.columns:
            coverage_rows.append(
                {
                    "Dataset": name,
                    "Registros": len(df),
                    "Desde": "n/d",
                    "Hasta": "n/d",
                    "Dias cubiertos": "n/d",
                    "Frescura (dias)": "n/d",
                }
            )
            continue
        ts = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
        if ts.empty:
            coverage_rows.append(
                {
                    "Dataset": name,
                    "Registros": len(df),
                    "Desde": "n/d",
                    "Hasta": "n/d",
                    "Dias cubiertos": "n/d",
                    "Frescura (dias)": "n/d",
                }
            )
            continue
        start = ts.min().date()
        end = ts.max().date()
        days = (end - start).days + 1
        freshness = (pd.Timestamp.now().date() - end).days
        coverage_rows.append(
            {
                "Dataset": name,
                "Registros": len(df),
                "Desde": start,
                "Hasta": end,
                "Dias cubiertos": days,
                "Frescura (dias)": freshness,
            }
        )

    st.markdown("Cobertura y frescura")
    st.dataframe(_display_df(pd.DataFrame(coverage_rows)), width="stretch")

    missing_rows = []
    key_columns = [
        "timestamp",
        "id_zona",
        "zone_id",
        "lat",
        "lon",
        "alcaldia_catalogo",
        "colonia_catalogo",
    ]
    for name, df in dataset_map.items():
        if df.empty:
            continue
        for col in key_columns:
            if col in df.columns:
                missing_pct = float(df[col].isna().mean() * 100)
                missing_rows.append(
                    {
                        "Dataset": name,
                        "Campo": col,
                        "% faltante": missing_pct,
                    }
                )

    if missing_rows:
        missing_df = pd.DataFrame(missing_rows).sort_values(
            "% faltante", ascending=False
        )
        st.markdown("Completitud de campos clave")
        st.dataframe(_display_df(missing_df), width="stretch")

    analytics_rows = []
    for key, df in analytics.items():
        status = "OK" if not df.empty else "VACIO"
        analytics_rows.append(
            {"Analitico": key, "Estado": status, "Filas": len(df)}
        )
    st.markdown("Estado de analiticos")
    st.dataframe(_display_df(pd.DataFrame(analytics_rows)), width="stretch")

    processed_paths = [
        PROCESSED_DIR / "c5_incidents.parquet",
        PROCESSED_DIR / "ecobici_trips.parquet",
        PROCESSED_DIR / "gtfs_stops.parquet",
        PROCESSED_DIR / "ecobici_rt.parquet",
    ]
    analytics_paths = [
        ANALYTICS_DIR / "c5_daily.parquet",
        ANALYTICS_DIR / "c5_zone_daily.parquet",
        ANALYTICS_DIR / "ppi_zones.parquet",
    ]

    def _latest_mtime(paths: list[Path]) -> str:
        times = []
        for path in paths:
            if path.exists():
                times.append(pd.Timestamp.fromtimestamp(path.stat().st_mtime))
        if not times:
            return "n/d"
        return max(times).strftime("%Y-%m-%d %H:%M")

    st.markdown("Ultimas actualizaciones de archivos")
    st.dataframe(
        _display_df(
            pd.DataFrame(
                [
                    {"Grupo": "Procesados", "Ultima actualizacion": _latest_mtime(processed_paths)},
                    {"Grupo": "Analiticos", "Ultima actualizacion": _latest_mtime(analytics_paths)},
                ]
            )
        ),
        width="stretch",
    )


def main() -> None:
    # Header profesional con logo y branding
    freshness = _data_freshness_badge()
    st.markdown(
        f"""
        <div class="hero">
            <div style="display: flex; align-items: center; gap: 1rem; flex-wrap: wrap;">
                <div style="font-size: 2.5rem;">🚦</div>
                <div style="flex: 1; min-width: 300px;">
                    <div class="hero-title">CDMX Mobility Pulse</div>
                    <div class="hero-sub">
                        Real-time urban mobility intelligence platform
                        <span class="badge">v0.1.0</span>
                        {freshness}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Load data with elegant loading message
    with st.spinner('🔄 Analyzing mobility patterns...'):
        data = _load_processed()
        analytics = _load_analytics()

    incidents = data["incidentes"]
    if not incidents.empty and "timestamp" in incidents.columns:
        incidents["timestamp"] = pd.to_datetime(
            incidents["timestamp"], errors="coerce")
        min_date = incidents["timestamp"].min()
        max_date = incidents["timestamp"].max()
    else:
        min_date = pd.Timestamp("2020-01-01")
        max_date = pd.Timestamp("2020-12-31")

    st.sidebar.header("🔍 Filtros Globales")
    st.sidebar.caption("Estos filtros aplican a todas las pestañas")
    date_range = st.sidebar.date_input(
        "Rango de fechas",
        (min_date, max_date),
        help="Filtrar todos los datos dentro de este rango de fechas"
    )
    if not isinstance(date_range, (tuple, list)) or len(date_range) != 2:
        st.info("Selecciona un intervalo de 2 fechas para continuar.")
        st.stop()
    hour_options = list(range(24))
    hours = st.sidebar.multiselect(
        "Hora del día",
        hour_options,
        default=[],
        help="Filtrar por horas específicas (vacío = todas las horas)"
    )
    day_options = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    days = st.sidebar.multiselect(
        "Día de la semana",
        day_options,
        default=[],
        help="Filtrar por días específicos (vacío = todos los días)"
    )

    with st.sidebar.expander("Actualización de datos", expanded=False):
        st.caption("Ejecuta ingestas y recalcula analíticos desde el dashboard.")
        run_ingest = st.checkbox(
            "Actualizar fuentes (ingesta)",
            value=False,
            help="Requiere conexión a las fuentes; puede tardar varios minutos."
        )
        sources = []
        if run_ingest:
            sources = st.multiselect(
                "Fuentes",
                ["C5", "GTFS", "ECOBICI RT", "ECOBICI trips", "GPS CDMX"],
                default=["C5"],
            )
            st.caption(
                "C5: incidentes de seguridad. "
                "GTFS: paradas y rutas oficiales de transporte. "
                "ECOBICI RT: disponibilidad en tiempo real de estaciones. "
                "ECOBICI trips: viajes históricos. "
                "GPS CDMX: proxy de movilidad basado en incidentes C5."
            )
        run_build = st.checkbox(
            "Recalcular analíticos",
            value=True,
            help="Ejecuta estandarización y métricas."
        )
        confirm = st.checkbox("Confirmo que quiero ejecutar la actualización", value=False)
        if st.button("Actualizar ahora", disabled=not confirm):
            errors = []
            warnings = []
            with st.spinner("Actualizando datos..."):
                if run_ingest and sources:
                    try:
                        if "C5" in sources:
                            from mobility_pulse.ingest.c5 import ingest_c5
                            ingest_c5()
                        if "GTFS" in sources:
                            from mobility_pulse.ingest.gtfs import ingest_gtfs
                            ingest_gtfs()
                        if "ECOBICI RT" in sources:
                            from mobility_pulse.ingest.ecobici_rt import ingest_ecobici_rt
                            ingest_ecobici_rt(snapshots=1, interval_sec=1)
                        if "ECOBICI trips" in sources:
                            from mobility_pulse.ingest.ecobici_trips import ingest_ecobici_trips
                            ingest_ecobici_trips(limit_rows=None)
                        if "GPS CDMX" in sources:
                            from mobility_pulse.ingest.gps_cdmx import ingest_gps_cdmx
                            gps_result = ingest_gps_cdmx()
                            if hasattr(gps_result, "name") and gps_result.name == "no_gps_dataset_found.txt":
                                warnings.append(
                                    "GPS CDMX: no se encontró un dataset en CKAN. "
                                    "Revisa palabras clave o carga un archivo manualmente."
                                )
                    except Exception as exc:
                        errors.append(f"Ingesta: {exc}")
                if run_build:
                    try:
                        from mobility_pulse.transform.standardize import standardize_all
                        from mobility_pulse.analytics.aggregates import build_analytics
                        from mobility_pulse.analytics.ppi import build_ppi
                        standardize_all()
                        build_analytics()
                        build_ppi()
                    except Exception as exc:
                        errors.append(f"Analíticos: {exc}")
            if errors:
                st.error("Errores durante la actualización:\n- " + "\n- ".join(errors))
            if warnings and not errors:
                st.warning("\n".join(warnings))
            if not errors:
                st.success("Actualización completada. Recargando panel...")
                st.cache_data.clear()
                st.cache_resource.clear()
                st.rerun()
    date_tuple = (pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1]))
    incidents_filtered = _apply_filters(
        data["incidentes"], date_tuple, hours, days)
    trips_filtered = _apply_filters(data["viajes"], date_tuple, hours, days)

    _render_exec_header(incidents_filtered, trips_filtered, analytics)

    tabs = st.tabs(
        [
            "Resumen Ejecutivo",
            "Alertas y Prioridades",
            "Tendencias Operativas",
            "Pronostico",
            "Calidad y Procesamiento",
        ]
    )

    with tabs[0]:
        st.markdown('<div class="section-title">Resumen Ejecutivo</div>',
                    unsafe_allow_html=True)
        _render_exec_brief(incidents_filtered, trips_filtered, data["paradas"], date_tuple, analytics)

    with tabs[1]:
        st.markdown('<div class="section-title">Alertas y Prioridades</div>',
                    unsafe_allow_html=True)
        _render_decision_intel(incidents_filtered)
        with st.expander("Indice de Prioridad (detalle)", expanded=False):
            _render_ppi(analytics)

    with tabs[2]:
        st.markdown(
            '<div class="section-title">Tendencias Operativas</div>', unsafe_allow_html=True)
        _render_trends(incidents_filtered, trips_filtered)

    with tabs[3]:
        st.markdown('<div class="section-title">Pronostico</div>',
                    unsafe_allow_html=True)
        _render_forecast_xgb(incidents_filtered)

    with tabs[4]:
        st.markdown('<div class="section-title">Calidad y Procesamiento</div>',
                    unsafe_allow_html=True)
        _render_data_quality(data, analytics)


if __name__ == "__main__":
    main()






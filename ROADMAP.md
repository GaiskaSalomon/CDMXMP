# Roadmap profesional (fases)

## Fase 0 — Base sólida (MVP listo)
Objetivo: que el pipeline funcione y sea reproducible.
- Ingesta de datos (C5, GTFS, ECOBICI)
- Validación de calidad (pandera + reporte)
- Procesamiento y H3
- Dash con mapas, filtros y PPI básico
- CLI + Makefile + CI + tests

Estado: Completo

## Fase 1 — Profesionalización de insights (v1 Analítico)
Objetivo: aportar valor más interpretativo.
- Top zonas con riesgo (incidentes / exposición)
- Ranking de presión por zona
- Indicadores de peak-hour por zona
- Anomaly Watch (picos anormales)
- Texto de insights automáticos (resumen ejecutivo)

## Fase 2 — Accesibilidad urbana (línea ITDP)
Objetivo: agregar análisis de accesibilidad real.
- Índice de accesibilidad a empleo, salud, educación
- Isochrones por zona (30–45 min)
- Ranking de alcaldías por accesibilidad
- Integración con GTFS (viaje multimodal + walking)

## Fase 3 — UX empresarial (Flagship)
Objetivo: dashboard tipo producto.
- Página Executive Brief
- KPI cards con narrativa automática
- Panel lateral con detalle contextual (zonas, colonia, alcaldía)
- Modo scenarios (cambios de rutas)

## Fase 4 — Publicación y portafolio
Objetivo: mostrarlo como producto profesional.
- Página pública (GitHub Pages / Streamlit Cloud)
- PDF automático de reporte
- Dataset versioning + metadata
- Documentación tipo whitepaper

## Fase 5 — Integración avanzada (proyecto real)
Objetivo: listo para institución.
- Ingesta incremental + cron
- API propia
- Evaluación de impactos de política
- Tablero operativo con alertas

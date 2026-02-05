# CDMX Mobility Pulse

CDMX Mobility Pulse es un pipeline reproducible y un dashboard interactivo para analizar movilidad urbana en Ciudad de Mexico con datos abiertos. El proyecto ingesta, valida, procesa y visualiza incidentes viales, transporte publico y bikeshare para apoyar la toma de decisiones.

## Alcance
- Ingestion y estandarizacion de datos (C5, GTFS, ECOBICI RT y viajes historicos).
- Tablas analiticas y reportes de calidad.
- Dashboard con vistas ejecutivas, alertas, tendencias y pronostico.

## Requisitos
- Python 3.10+
- 1+ GB de espacio en disco para datos

## Instalacion rapida
```bash
make setup
make data
make app
```
El dashboard se abre en `http://localhost:8501`.

Verificacion:
```bash
python verify_setup.py
```

## Pipeline y comandos
```bash
make data       # ingesta y procesamiento
make validate   # reporte de calidad
make build      # tablas analiticas
make app        # dashboard
make report     # reportes en reports/
```

CLI (equivalente):
```bash
python -m mobility_pulse ingest --source gtfs
python -m mobility_pulse ingest --source c5
python -m mobility_pulse ingest --source ecobici_rt --snapshots 1
python -m mobility_pulse ingest --source ecobici_trips --limit_rows 500000
python -m mobility_pulse validate
python -m mobility_pulse build
python -m mobility_pulse app
python -m mobility_pulse report
```

## Fuentes de datos (que significan)
- C5: incidentes viales de la CDMX.
- GTFS: feed estandar de transporte publico (paradas, rutas, horarios).
- ECOBICI RT: disponibilidad en tiempo real (GBFS).
- ECOBICI viajes: viajes historicos (CSV mensual).
- GPS CKAN: busqueda automatica de datasets GPS en datos.cdmx.gob.mx.

Las URLs estan en `config/datasets.yml` y se pueden sobreescribir con variables de entorno.

## Uso del dashboard
Los filtros globales (fecha, hora y dia de semana) afectan la mayoria de las vistas analiticas y el pronostico. La vista de calidad no depende del filtro.

Vistas:
- Resumen Ejecutivo: KPIs de incidentes y viajes, ventana de cobertura y alertas principales. Uso: lectura rapida del estado general y validacion del rango seleccionado.
- Alertas y Prioridades: picos diarios, crecimiento semana a semana y persistencia de hotspots. Uso: detectar zonas y periodos que requieren atencion inmediata.
- Tendencias Operativas: tendencia mensual y distribucion por hora y dia. Uso: entender patrones operativos y estacionalidad.
- Pronostico: modelos de boosting (XGBoost, LightGBM, CatBoost) con split 80/20, metricas (RMSE, MAE, WMAPE) y pronostico a 7 dias con bandas 95%. Uso: estimar demanda operativa a corto plazo y descargar resultados.
- Calidad y Procesamiento: cobertura temporal, estado de tablas analiticas y ultima actualizacion. Uso: diagnostico de datos y pipeline.

Actualizacion de datos:
- En la barra lateral puedes ejecutar ingestas y reconstruccion de tablas analiticas.

## Estructura de carpetas
- `data/raw/`: datos descargados
- `data/processed/`: datos limpios (parquet)
- `data/analytics/`: tablas analiticas para el dashboard
- `reports/`: reportes y salidas de calidad

## Limitaciones
- Las URLs de datos pueden cambiar con el tiempo.
- ECOBICI viajes puede tener cobertura parcial si se descarga un solo mes.
- La accesibilidad es una aproximacion basada en cobertura, no rutas reales.

## Documentacion
- `QUICKREF.md`
- `docs/PIPELINE.md`
- `docs/ARCHITECTURE.md`
- `docs/CHANGELOG.md`
- `ROADMAP.md`
- `CONTRIBUTING.md`

## Licencia
MIT. Ver `LICENSE`.

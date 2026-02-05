# Contribuir a CDMX Mobility Pulse

Gracias por tu interes en contribuir. Este documento describe el flujo de trabajo y los requisitos para cambios en codigo, datos y documentacion.

## Formas de contribuir
- Reportar bugs con pasos reproducibles.
- Mejorar el dashboard o los analiticos.
- Agregar documentacion o ejemplos claros.
- Optimizar rendimiento o calidad de datos.

## Requisitos
- Python 3.10+
- Conocimientos basicos de Git

## Clonar y preparar entorno
```bash
# clona el repo (reemplaza USUARIO)
git clone https://github.com/USUARIO/CDMXMP.git
cd CDMXMP

# crear y activar entorno
python -m venv .venv
# Windows
.venv\Scripts\activate

# instalar dependencias
make setup
```

Verifica instalacion:
```bash
python verify_setup.py
```

## Flujo recomendado de desarrollo
```bash
# ingesta y procesamiento de datos
make data
make validate
make build

# dashboard
make app
```

## Pruebas y calidad de codigo
```bash
make test
make lint
```

## Estructura clave
- `mobility_pulse/`: codigo principal
- `config/datasets.yml`: URLs de datos
- `data/`: datos generados (se ignoran en git)
- `reports/`: salidas y reportes (solo se versiona `reports/data_quality.md`)

## Buenas practicas
- Mantener cambios pequenos y enfocados.
- Escribir mensajes de commit claros (ej: `fix: corrige filtro de fechas`).
- Agregar pruebas cuando se introduce logica nueva.
- No subir datos crudos ni archivos grandes.

## Reportar bugs
Incluye:
- Pasos exactos para reproducir
- Resultado esperado vs resultado real
- Tu sistema operativo y version de Python
- Logs o traceback completos

Ejemplo minimo:
```text
OS: Windows 11
Python: 3.10.x
Comando: make app
Error: KeyError: "id_zona"
```

## Pull Requests
Antes de abrir un PR:
- `make test` y `make lint` sin errores
- Documentacion actualizada si aplica
- Describir claramente el problema y la solucion

## Alcance de datos
Los datos pueden cambiar con el tiempo. Si tu cambio depende de una fuente externa, documenta:
- URL actualizada
- fecha aproximada de extraccion
- cambios de esquema detectados

---

Gracias por mejorar CDMX Mobility Pulse.

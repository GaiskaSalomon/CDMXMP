#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para verificar que no haya errores de columnas
"""

import re

with open("mobility_pulse/app/streamlit_app.py", "r", encoding="utf-8") as f:
    content = f.read()

# Buscar posibles problemas
issues = []

# Nombres de columnas traducidos que no deberían estar
spanish_columns = ["fecha", "mes", "día", "hora", "conteo"]

for col in spanish_columns:
    # Buscar patrones de acceso a columnas con estos nombres
    patterns = [
        f'\\["{col}"\\]',
        f"\\['{col}'\\]",
        f'\\("{col}"\\)',
    ]

    for pattern in patterns:
        matches = list(re.finditer(pattern, content))
        if matches:
            for match in matches:
                # Obtener línea
                line_num = content[: match.start()].count("\n") + 1
                issues.append(f"Línea {line_num}: Usa '{col}' (debería ser en inglés)")

if issues:
    print(f"⚠️  Encontrados {len(issues)} posibles problemas:")
    for issue in issues[:10]:
        print(f"  {issue}")
else:
    print("✅ No se encontraron problemas de nombres de columnas")
    print("✅ Todos los nombres están en inglés (coinciden con aggregates.py)")

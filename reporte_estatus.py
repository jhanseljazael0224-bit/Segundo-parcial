
import json
import re
from datetime import datetime
from pathlib import Path

import pandas as pd

from config import integrantes


# Carpeta de resultados
carpeta = Path("resultados")

# Leer el Excel de Plusval
archivo = carpeta / "plusval_completo_200.xlsx"

tabla = pd.read_excel(archivo)


# Separar moneda y cantidad
def convertir_precio(texto):
    """Extrae la moneda y el valor numérico de un precio."""

    patron = r"(US|RD)\$\s*([\d,]+(?:\.\d+)?)"
    encontrado = re.search(patron, str(texto))

    if not encontrado:
        return None, None

    tipo_moneda = encontrado.group(1) + "$"

    valor = float(
        encontrado.group(2).replace(",", "")
    )

    return tipo_moneda, valor


# Crear columnas temporales para analizar precios
tabla[["Moneda", "Valor"]] = tabla["Precio"].apply(
    lambda precio: pd.Series(convertir_precio(precio))
)


# Buscar precios máximos y mínimos por moneda
extremos = {}

for moneda in ["US$", "RD$"]:
    grupo = tabla[tabla["Moneda"] == moneda]

    if grupo.empty:
        continue

    mas_cara = grupo.loc[grupo["Valor"].idxmax()]
    mas_barata = grupo.loc[grupo["Valor"].idxmin()]

    extremos[moneda] = {
        "mas_cara": {
            "nombre": mas_cara["Nombre"],
            "precio": mas_cara["Precio"]
        },
        "mas_barata": {
            "nombre": mas_barata["Nombre"],
            "precio": mas_barata["Precio"]
        }
    }


# Crear reporte de estado
reporte = {
    "fuente": "Plusval",
    "fecha_generacion": datetime.now().isoformat(
        timespec="seconds"
    ),
    "autores": integrantes,
    "cantidad_propiedades": len(tabla),
    "filas_identicas": int(
        tabla.iloc[:, :9].duplicated().sum()
    ),
    "datos_faltantes": {
        columna: int(cantidad)
        for columna, cantidad in tabla.iloc[:, :9].isna().sum().items()
    },
    "precios_extremos": extremos,
    "duracion_total_scraping_segundos": None,
    "duracion_por_request": [],
    "observacion": (
        "Los tiempos de las solicitudes anteriores "
        "no fueron almacenados. Pendiente registrar "
        "duraciones en una nueva ejecución."
    )
}


# Guardar JSON
destino = carpeta / "estatus_plusval.json"

with open(destino, "w", encoding="utf-8") as archivo_json:
    json.dump(
        reporte,
        archivo_json,
        ensure_ascii=False,
        indent=4
    )


print("=== REPORTE DE ESTADO ===")
print("Fuente:", reporte["fuente"])
print("Propiedades:", reporte["cantidad_propiedades"])
print("Filas idénticas:", reporte["filas_identicas"])

print("\nPrecios máximos y mínimos:")
for moneda, datos in extremos.items():
    print("\nMoneda:", moneda)
    print("Más cara:", datos["mas_cara"])
    print("Más barata:", datos["mas_barata"])

print("\nReporte guardado:", destino)

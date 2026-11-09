
from pathlib import Path

import pandas as pd
from ydata_profiling import ProfileReport


# Carpeta donde están los resultados
carpeta = Path("resultados")
archivo_excel = carpeta / "plusval_completo_200.xlsx"

# Comprobar que existe el Excel
if not archivo_excel.exists():
    raise SystemExit(
        "No se encontró resultados/plusval_completo.xlsx"
    )

# Leer las propiedades guardadas
tabla = pd.read_excel(archivo_excel)

print("=== VERIFICACIÓN DE PLUSVAL ===")
print("Total de registros:", len(tabla))
print("Número de columnas:", len(tabla.columns))

print("\nDatos faltantes por columna:")
print(tabla.isna().sum())

print("\nFilas exactamente repetidas:")
print(tabla.duplicated().sum())

if "Vendedor" in tabla.columns:
    vendedores = tabla["Vendedor"].notna().sum()
    print("\nRegistros con vendedor:", vendedores)


# Exportar a Parquet
tabla.to_parquet(
    carpeta / "plusval.parquet",
    index=False
)

print("\nParquet generado correctamente.")


# Exportar a JSON
tabla.to_json(
    carpeta / "plusval.json",
    orient="records",
    force_ascii=False,
    indent=2
)

print("JSON generado correctamente.")


# Generar reporte HTML de análisis
print("\nGenerando reporte HTML...")

reporte = ProfileReport(
    tabla,
    title="Análisis de propiedades - Plusval",
    minimal=True
)

reporte.to_file(
    carpeta / "reporte_plusval.html"
)

print("\n=== PROCESO FINALIZADO ===")
print("Archivos generados correctamente.")


"""Registra los tiempos de las solicitudes del scraper."""

import json
import time
from datetime import datetime
from pathlib import Path

import requests

from scrapers.plusval_scraper import PlusvalScraper


class SesionConTiempo(requests.Session):
    """Sesión HTTP que mide cada solicitud."""

    def __init__(self):
        super().__init__()
        self.registros = []

    def request(self, method, url, **kwargs):  # pylint: disable=arguments-differ
        """Realiza una solicitud y registra su duración."""

        inicio = time.perf_counter()
        respuesta = None
        error = None

        try:
            respuesta = super().request(
                method, url, **kwargs
            )

            return respuesta

        except requests.RequestException as excepcion:
            error = str(excepcion)
            raise

        finally:
            duracion = time.perf_counter() - inicio

            self.registros.append({
                "metodo": method,
                "url": url,
                "estado_http": (
                    respuesta.status_code
                    if respuesta is not None else None
                ),
                "duracion_segundos": round(duracion, 3),
                "error": error
            })


# Crear el scraper
scraper = PlusvalScraper()

# Activar el registro de tiempos
sesion = SesionConTiempo()
sesion.headers.update(scraper.session.headers)

scraper.session = sesion

# Registrar fecha de inicio
fecha_inicio = datetime.now().isoformat(
    timespec="seconds"
)

inicio_total = time.perf_counter()

# Extraer solamente 3 propiedades
propiedades = scraper.obtener_propiedades(limite=200)

# Calcular duración total
duracion_total = time.perf_counter() - inicio_total

# Crear reporte
reporte = {
    "fuente": "Plusval",
    "fecha_inicio": fecha_inicio,
    "fecha_fin": datetime.now().isoformat(
        timespec="seconds"
    ),
    "cantidad_propiedades": len(propiedades),
    "cantidad_requests": len(sesion.registros),
    "duracion_total_segundos": round(duracion_total, 3),
    "duracion_por_request": sesion.registros
}

# Guardar JSON
carpeta = Path("resultados")
carpeta.mkdir(exist_ok=True)

archivo = carpeta / "tiempos_prueba_200.json"

with open(archivo, "w", encoding="utf-8") as archivo_json:
    json.dump(
        reporte,
        archivo_json,
        ensure_ascii=False,
        indent=4
    )

print("\n=== REPORTE DE TIEMPOS ===")
print("Propiedades:", len(propiedades))
print("Solicitudes realizadas:", len(sesion.registros))
print(
    "Duración total:",
    round(duracion_total, 3),
    "segundos"
)

for numero, registro in enumerate(sesion.registros, 1):
    print(
        f"Request {numero}:",
        registro["duracion_segundos"],
        "segundos"
    )

print("\nReporte guardado:", archivo)

"""
Prueba del modulo de reportes con datos de ejemplo.
Simula requests y propiedades para comprobar que se generan los 4 archivos,
sin depender de que los scrapers esten terminados.
"""

import random
import time

import config
from models.propiedades import Propiedad
from utils.data_processor import DataProcessor
from utils.reportes import EstatusScraping, Exportador

fuentes = ["Corotos", "SuperCasas", "Plusval"]
zonas = ["Piantini", "Naco", "Bella Vista", "Santiago", "Punta Cana", "Los Prados"]

procesador = DataProcessor()
estatus = EstatusScraping(config.integrantes)
estatus.iniciar()

for f in fuentes:
    for pag in range(1, 4):
        # Simula el tiempo de un request
        t = random.uniform(0.05, 0.2)
        time.sleep(t)
        estatus.registrar_request(f, f"https://ejemplo.com/{f.lower()}?page={pag}", t)

    for i in range(10):
        procesador.agregar_propiedad(Propiedad(
            f,
            f"Apartamento {i + 1} en {random.choice(zonas)}",
            f"US$ {random.randint(60, 900) * 1000:,}",
            random.choice(zonas),
            f"Inmobiliaria {random.randint(1, 5)}",
            f"{random.randint(60, 300)} m2",
            random.randint(1, 4),
            random.randint(1, 4),
            random.randint(0, 3),
        ))

estatus.finalizar()

tabla = procesador.mostrar_resumen()
print(tabla.head())

resumen = estatus.mostrar(tabla)
Exportador("resultados_prueba").exportar_todo(tabla, resumen)

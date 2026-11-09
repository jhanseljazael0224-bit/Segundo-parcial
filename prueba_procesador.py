
from models.propiedades import Propiedad
from utils.data_processor import DataProcessor


# Crear una propiedad de ejemplo
casa = Propiedad(
    "Plusval",
    "Apartamento en Santo Domingo",
    150000,
    "Santo Domingo",
    "Vendedor de prueba",
    120,
    3,
    2,
    2
)

# Crear el procesador
procesador = DataProcessor()

# Agregar la propiedad
procesador.agregar_propiedad(casa)

# Convertir los datos en una tabla
tabla = procesador.mostrar_resumen()

# Mostrar la tabla
print(tabla)

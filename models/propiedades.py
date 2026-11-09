
class Propiedad:

    def __init__(
        self,
        fuente,
        nombre,
        precio,
        ubicacion,
        vendedor,
        tamano,
        habitaciones,
        baños,
        parqueos
    ):
        self.fuente = fuente
        self.nombre = nombre
        self.precio = precio
        self.ubicacion = ubicacion
        self.vendedor = vendedor
        self.tamano = tamano
        self.habitaciones = habitaciones
        self.baños = baños
        self.parqueos = parqueos

    def mostrar_informacion(self):
        return {
            "Fuente de info": self.fuente,
            "Nombre": self.nombre,
            "Precio": self.precio,
            "Ubicación": self.ubicacion,
            "Vendedor": self.vendedor,
            "Tamaño": self.tamano,
            "Número de habitaciones": self.habitaciones,
            "Número de baños": self.baños,
            "Número de parqueos": self.parqueos
        }

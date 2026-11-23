
from datetime import datetime
from pyDatalog import pyDatalog

from schebuilder.generator import Weekday, Time, Group


def convertir_hora(hora):
    """
    Convierte una hora a minutos desde medianoche.

    Acepta:
    - Un objeto Time de generator.py
    - Una cadena en formato HH:MM
    """
    if isinstance(hora, Time):
        return hora.to_minutes()

    if isinstance(hora, str):
        valor = datetime.strptime(hora, "%H:%M")
        return valor.hour * 60 + valor.minute

    raise ValueError("La hora debe ser Time o HH:MM")


def normalizar_dia(dia):
    """
    Convierte un Weekday o una cadena a un nombre
    uniforme para utilizarlo en pyDatalog.
    """
    if isinstance(dia, Weekday):
        return dia.name.lower()

    if isinstance(dia, str):
        dia = dia.strip().lower()

        equivalencias = {
            "lunes": "monday",
            "martes": "tuesday",
            "miercoles": "wednesday",
            "miércoles": "wednesday",
            "jueves": "thursday",
            "viernes": "friday",
            "sabado": "saturday",
            "sábado": "saturday"
        }

        return equivalencias.get(dia, dia)

    raise ValueError("Dia no valido")


class FiltroHorarios:
    """
    Sistema de filtrado de horarios con pyDatalog.

    Descarta grupos que tengan al menos una sesion
    en un dia e intervalo de tiempo restringido.

    Compatible con las clases de generator.py.
    """

    def __init__(self, dia, hora_inicio, hora_fin):

        self.dia = normalizar_dia(dia)

        if self.dia not in {
            dia.name.lower() for dia in Weekday
        }:
            raise ValueError("Dia no valido")

        self.inicio = convertir_hora(hora_inicio)
        self.fin = convertir_hora(hora_fin)

        if self.inicio >= self.fin:
            raise ValueError(
                "La hora inicial debe ser menor que la final"
            )

    def filtrar(self, grupos, obtener_sesiones):
        """
        Filtra una coleccion de grupos.

        obtener_sesiones debe devolver:
        (dia, hora_inicio, hora_fin)

        Retorna:
        (permitidos, descartados)
        """

        grupos = list(grupos)
        registros = []

        # Obtener sesiones de los grupos.
        for indice, grupo in enumerate(grupos):

            sesiones = obtener_sesiones(grupo)

            for dia, inicio, fin in sesiones:

                dia_normalizado = normalizar_dia(dia)
                minuto_inicio = convertir_hora(inicio)
                minuto_fin = convertir_hora(fin)

                if minuto_inicio >= minuto_fin:
                    raise ValueError(
                        f"Horario invalido en grupo {indice}"
                    )

                registros.append((
                    indice,
                    dia_normalizado,
                    minuto_inicio,
                    minuto_fin
                ))

        if not registros:
            return grupos, []
        
        # Iniciar el motor logico.
        pyDatalog.Logic()

        # Crear terminos logicos.
        sesion, conflicto, G, D, I, F = (
            pyDatalog.create_terms(
                "sesion, conflicto, G, D, I, F"
            )
        )

        # Registrar los horarios como hechos.
        for indice, dia, inicio, fin in registros:
            +sesion(indice, dia, inicio, fin)

        # Regla de conflicto:
        # mismo dia e interseccion de horarios.
        conflicto(G) <= (
            sesion(G, D, I, F)
            & (D == self.dia)
            & (I < self.fin)
            & (F > self.inicio)
        )

        # Consultar los grupos que tienen conflicto.
        resultados = conflicto(G).data

        indices_descartados = {
            resultado[0] for resultado in resultados
        }

        # Separar los grupos.
        permitidos = []
        descartados = []

        for indice, grupo in enumerate(grupos):
            if indice in indices_descartados:
                descartados.append(grupo)
            else:
                permitidos.append(grupo)

        return permitidos, descartados

    def filtrar_grupos(self, grupos: list[Group]):
        """
        Filtra directamente objetos Group de generator.py.

        Cada Group contiene time_blocks:
        dict[Weekday, TimeBlock]

        No es necesario modificar generator.py.
        """

        def obtener_sesiones(grupo):
            for dia, bloque in grupo.time_blocks.items():
                yield (
                    dia,
                    bloque.start,
                    bloque.end
                )

        return self.filtrar(grupos, obtener_sesiones)

    def filtrar_materias(self, materias: list[list[Group]]) -> list[list[Group]]:
        """Filtra los grupos y conserva el orden de las materias."""
        resultado = []

        for grupos in materias:
            permitidos, _ = self.filtrar_grupos(grupos)
            resultado.append(permitidos)

        return resultado
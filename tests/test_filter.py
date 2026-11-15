
from src.schebuilder.filter import FiltroHorarios

from src.schebuilder.generator import (
    Weekday,
    ClassType,
    Subject,
    Professor,
    Time,
    TimeBlock,
    Group
)


def crear_grupo(codigo, horarios):
    """
    Crea un grupo utilizando las clases del generador.
    """

    materia = Subject(101, ClassType.THEORY)
    profesor = Professor("Profesor de prueba", 9.0)

    bloques = {}

    for dia, inicio, fin in horarios:
        bloques[dia] = TimeBlock(
            Time(*inicio),
            Time(*fin)
        )

    return Group(
        codigo,
        materia,
        profesor,
        bloques
    )


def test_filtro_grupos_reales():

    # Grupo 1: lunes de 07:00 a 09:00
    grupo1 = crear_grupo(1, [
        (Weekday.MONDAY, (7, 0), (9, 0))
    ])

    # Grupo 2: lunes de 10:00 a 12:00
    grupo2 = crear_grupo(2, [
        (Weekday.MONDAY, (10, 0), (12, 0))
    ])

    # Grupo 3: martes de 08:00 a 10:00
    grupo3 = crear_grupo(3, [
        (Weekday.TUESDAY, (8, 0), (10, 0))
    ])

    # Grupo 4: lunes 09:00-11:00 y miercoles
    grupo4 = crear_grupo(4, [
        (Weekday.MONDAY, (9, 0), (11, 0)),
        (Weekday.WEDNESDAY, (12, 0), (14, 0))
    ])

    grupos = [grupo1, grupo2, grupo3, grupo4]

    # Restringir lunes de 07:00 a 10:00.
    filtro = FiltroHorarios(
        Weekday.MONDAY,
        Time(7, 0),
        Time(10, 0)
    )

    permitidos, descartados = filtro.filtrar_grupos(
        grupos
    )

    codigos_permitidos = [
        grupo.key_code for grupo in permitidos
    ]

    codigos_descartados = [
        grupo.key_code for grupo in descartados
    ]

    assert codigos_permitidos == [2, 3]
    assert codigos_descartados == [1, 4]


def test_limites_del_intervalo():

    grupo1 = crear_grupo(1, [
        (Weekday.MONDAY, (6, 0), (7, 0))
    ])

    grupo2 = crear_grupo(2, [
        (Weekday.MONDAY, (10, 0), (11, 0))
    ])

    filtro = FiltroHorarios(
        Weekday.MONDAY,
        Time(7, 0),
        Time(10, 0)
    )

    permitidos, descartados = filtro.filtrar_grupos(
        [grupo1, grupo2]
    )

    assert len(permitidos) == 2
    assert len(descartados) == 0


def test_sin_conflictos():

    grupo = crear_grupo(1, [
        (Weekday.FRIDAY, (12, 0), (14, 0))
    ])

    filtro = FiltroHorarios(
        Weekday.MONDAY,
        Time(7, 0),
        Time(10, 0)
    )

    permitidos, descartados = filtro.filtrar_grupos(
        [grupo]
    )

    assert permitidos == [grupo]
    assert descartados == []

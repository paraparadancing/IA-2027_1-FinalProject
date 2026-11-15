
from src.schebuilder.main import procesar_grupos

from src.schebuilder.generator import (
    Group,
    Subject,
    Professor,
    ClassType,
    Weekday,
    Time,
    TimeBlock
)


def test_integracion_main():

    materia = Subject(101, ClassType.THEORY)
    profesor = Professor("Profesor A", 9.0)

    grupo1 = Group(
        1, materia, profesor,
        {
            Weekday.MONDAY: TimeBlock(
                Time(7, 0), Time(9, 0)
            )
        }
    )

    grupo2 = Group(
        2, materia, profesor,
        {
            Weekday.TUESDAY: TimeBlock(
                Time(10, 0), Time(12, 0)
            )
        }
    )

    grupos = [grupo1, grupo2]

    permitidos, descartados = procesar_grupos(
        grupos,
        Weekday.MONDAY,
        Time(7, 0),
        Time(10, 0)
    )

    assert permitidos == [grupo2]
    assert descartados == [grupo1]

from schebuilder.ui import main

def cli():
    main()

if __name__ == "__main__":
    cli()

from schebuilder.generator import Group, Weekday, Time
from schebuilder.filter import FiltroHorarios


def procesar_grupos(
    grupos: list[Group],
    dia_restringido: Weekday,
    hora_inicio: Time,
    hora_fin: Time
):
    """
    Aplica una restriccion horaria a los grupos.

    Retorna:
        permitidos: grupos sin conflictos
        descartados: grupos que incumplen la restriccion
    """

    filtro = FiltroHorarios(
        dia_restringido,
        hora_inicio,
        hora_fin
    )

    permitidos, descartados = filtro.filtrar_grupos(grupos)

    return permitidos, descartados


from .generator import Group, Weekday, Time
from .filter import FiltroHorarios


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

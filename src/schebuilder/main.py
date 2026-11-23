if __name__ == "__main__":
    import runpy
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    sys.path[:0] = [
        str(root / "src"),
        str(root / "build" / "Release"),
        str(root / "build"),
    ]
    runpy.run_module("schebuilder.ui", run_name="__main__")
    raise SystemExit(0)

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

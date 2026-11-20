from pathlib import Path
import csv
from sys import stderr

from schebuilder.generator import (
    Time,
    TimeBlock,
    Group,
    Weekday
)

def parse_time(input_string: str) -> Time | None:
    partitioned_input = input_string.partition(':')
    try:
        hours = int(partitioned_input[0])
    except ValueError:
        stderr.write(f"Couldn't parse {partitioned_input[0]} as hours")
        return None
    try:
        minutes = int(partitioned_input[2])
    except ValueError:
        stderr.write(f"Couldn't parse {partitioned_input[2]} as minutes")
        return None
    try:
        output = Time(hours, minutes)
    except ValueError as e:
        stderr.write("")
        return None
    return output

def parse_time_block(input_string: str) -> TimeBlock | None:
    partitioned_input = input_string.partition(' a ')
    start_time = parse_time(partitioned_input[0])
    end_time = parse_time(partitioned_input[2])

    if start_time is None or end_time is None:
        print(f"Couldn't parse {input_string} as a time period")
        return None
    else:
        return TimeBlock(start_time, end_time)

def parse_days(input_string: str) -> list[Weekday]:
    output: list[Weekday] = list()
    for substr in input_string.split(','):
        cleaned = substr.strip().lower()
        if not cleaned:
            continue

        day: Weekday | None = None
        match cleaned:
            case 'mon' | 'monday' | 'lun' | 'lunes':
                day = Weekday.MONDAY
            case 'tue' | 'tuesday' | 'mar' | 'martes':
                day = Weekday.TUESDAY
            case 'wed' | 'wednesday' | 'mie' | 'miercoles' | 'miércoles':
                day = Weekday.WEDNESDAY
            case 'thu' | 'thursday' | 'jue' | 'jueves':
                day = Weekday.THURSDAY
            case 'fri' | 'friday' | 'vie' | 'viernes':
                day = Weekday.FRIDAY
            case 'sat' | 'saturday' | 'sab' | 'sabado' | 'sábado':
                day = Weekday.SATURDAY
            case _:
                stderr.write(f"Couldn't match {substr} to any weekday\n")

        if day is not None and day not in output:
            output.append(day)

    return output

def load_from_csv(path: Path) -> list[Group]:
    """
    Loads only groups with exactly these columns:

        Clave: a positive int (optional). Defaults to 0 if no subject key is given.
        Gpo: a positive int (optional). Defaults to an increment if no group key is given.
        Profesor: a string (optional). The name is normalized and matched against
            existing objects; defaults to None if no professor is given.
        Horario: start time (inclusive) to end time (exclusive), formatted as
            `HH:MM a HH:MM`. Mandatory.
        Días: weekdays separated by commas. Mandatory.

    e.g. a valid entry:

    ```csv
    Clave,Gpo,Profesor,Horario,Días
    406,1,DR. OSCAR ARANA HERNANDEZ (PRESENCIAL),11:00 a 13:00,"Lun, Mie"
    406,2,DR. JOSE JAIME CAMACHO ESCOTO (PRESENCIAL) Ver Nota 2,13:00 a 15:00,"Lun, Mie"
    1535,1,DR. ABRAHAM PEREZ ALONZO (PRESENCIAL),09:00 a 10:30,"Lun,Jue",B305
    ,,,09:00 a 11:00,"Mar",T101
    ```

    Any other column is ignored.
    """
    output: list[Group] = list()
    n = 0  # Incremental value for groups without a key_code

    with open(path, "r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            raw_time_block = (row.get("Horario") or "").strip()
            ray_days = (row.get("Días") or "").strip()

            if not raw_time_block or not ray_days:
                continue

            days = parse_days(ray_days)
            if not days:
                continue

            try:
                time_block = parse_time_block(raw_time_block)
            except ValueError:
                continue

            if time_block is None:
                continue

            raw_clave = (row.get("Clave") or "").strip()
            raw_gpo = (row.get("Gpo") or "").strip()
            raw_prof = (row.get("Profesor") or "").strip()

            # If row doesn't contain 'Clave' nor 'Gpo' then it belongs to the last group
            if not raw_clave and not raw_gpo and output:
                for day in days:
                    output[-1].time_blocks.setdefault(day, time_block)
                continue

            time_blocks: dict[Weekday, TimeBlock] = {}
            for day in days:
                time_blocks.setdefault(day, time_block)

            if not raw_clave:
                subject_key = 0
            else:
                try:
                    parsed_clave = int(raw_clave)
                    subject_key = parsed_clave if parsed_clave > 0 else 0
                except ValueError:
                    stderr.write(f"Couldn't parse {raw_clave} as Clave\n")
                    subject_key = 0

            if not raw_gpo:
                n += 1
                key_code = n
            else:
                try:
                    parsed_gpo = int(raw_gpo)
                    if parsed_gpo > 0:
                        key_code = parsed_gpo
                    else:
                        n += 1
                        key_code = n
                except ValueError:
                    stderr.write(f"Couldn't parse {raw_gpo} as Gpo\n")
                    n += 1
                    key_code = n

            professor = raw_prof if raw_prof else None

            built_group = Group(
                key_code=key_code,
                subject_key=subject_key,
                professor=professor,
                time_blocks=time_blocks,
            )
            output.append(built_group)

    return output
    

import re

import generator_backend

from schebuilder.generator import (
    TimeBlock,
    Time,
    Weekday,
    Group
)

# First AI group
our_ai_time_block: TimeBlock = TimeBlock(start=Time(13, 00), end=Time(15, 00))
our_ai_datetime= {Weekday.MONDAY: our_ai_time_block, Weekday.WEDNESDAY: our_ai_time_block}
our_group: Group = Group(2, 406, "DR. JOSE JAIME CAMACHO ESCOTO", our_ai_datetime)
# Second AI group
mureddu = "ING. RODRIGO ARAGON MUREDDU"
their_ai_time_block: TimeBlock = TimeBlock(start=Time(15, 00), end=Time(17, 00))
their_ai_datetime = {Weekday.MONDAY: their_ai_time_block, Weekday.WEDNESDAY: their_ai_time_block}
their_group: Group = Group(4, 406, mureddu, their_ai_datetime)
# First VLSI group
vlsi_1_time_block: TimeBlock = TimeBlock(start=Time(17, 30), end=Time(19, 00))
vlsi_1_datetime = {Weekday.TUESDAY: vlsi_1_time_block, Weekday.THURSDAY: vlsi_1_time_block}
vlsi_group: Group = Group(4, 1535, "M.I. RAFAEL PRIETO MELENDEZ", vlsi_1_datetime)
# Second VLSI group
vlsi_2_time_block: TimeBlock = TimeBlock(start=Time(9, 0), end=Time(10, 30))
vlsi_2_datetime = {Weekday.MONDAY: vlsi_2_time_block, Weekday.THURSDAY: vlsi_2_time_block}
vlsi_group_2: Group = Group(1, 1535, "DR. ABRAHAM PEREZ ALONZO", vlsi_2_datetime)
# Third VLSI group
vlsi_3_time_block: TimeBlock = TimeBlock(start=Time(13, 0), end=Time(14, 30))
vlsi_3_datetime = {Weekday.MONDAY: vlsi_3_time_block, Weekday.WEDNESDAY: vlsi_3_time_block}
vlsi_group_3: Group = Group(2, 1535, "DR. ABRAHAM PEREZ ALONZO", vlsi_3_datetime)

ADDRESS_RE = re.compile(r"0x[0-9a-f]+")

def normalize(text: str) -> str:
    """Replace memory addresses so output comparisons are deterministic."""
    return ADDRESS_RE.sub("0xADDR", text)

def test_backend_group_repr_and_str(capsys):
    print(repr(our_group))
    print(str(our_group))
    out = normalize(capsys.readouterr().out)

    expected_repr = "<schebuilder.generator.Group object at 0xADDR>"
    assert out.splitlines()[0] == expected_repr

    expected_str = "\n".join([
        "Group keycode: 2",
        "Subject keycode: 406",
        "Professor: DR. JOSE JAIME CAMACHO ESCOTO",
        "Time blocks: "
        "{<Weekday.MONDAY: 1>: [13:00, 15:00], <Weekday.WEDNESDAY: 3>: [13:00, 15:00]}",
    ])
    assert out.splitlines()[1:] == expected_str.splitlines()

def test_backend_generator():
    valid_schedules = generator_backend.generate_valid_schedules(
        [[our_group, their_group], [vlsi_group, vlsi_group_2]]
    )
    assert len(valid_schedules) == 4
    set_repr = [set(schedule) for schedule in valid_schedules]
    assert {vlsi_group, our_group} in set_repr
    assert {vlsi_group_2, our_group} in set_repr
    assert {vlsi_group, their_group} in set_repr
    assert {vlsi_group_2, their_group} in set_repr

    # Empty list
    empty_schedules = generator_backend.generate_valid_schedules([])
    assert len(empty_schedules) == 0
    # List of empty lists
    empty_schedules = generator_backend.generate_valid_schedules([[],[]])
    assert len(empty_schedules) == 0
    # Collision
    empty_schedules = generator_backend.generate_valid_schedules([[our_group], [vlsi_group_3]])
    assert len(empty_schedules) == 0

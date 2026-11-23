import pytest

from schebuilder.generator import (
    Weekday,
    ClassType,
    Time,
    TimeBlock,
    Group,
    get_schedule_str,
    get_schedule_details
)

# First AI group
our_ai_time_block: TimeBlock = TimeBlock(start=Time(13, 00), end=Time(15, 00))
our_ai_datetime= {Weekday.MONDAY: our_ai_time_block, Weekday.WEDNESDAY: our_ai_time_block}
our_group: Group = Group(2, 406, "DR. JOSE JAIME CAMACHO ESCOTO", our_ai_datetime)
# Second AI group
their_ai_time_block: TimeBlock = TimeBlock(start=Time(15, 00), end=Time(17, 00))
their_ai_datetime = {Weekday.MONDAY: their_ai_time_block, Weekday.WEDNESDAY: their_ai_time_block}
their_group: Group = Group(4, 406, "ING. RODRIGO ARAGON MUREDDU", their_ai_datetime)
# VLSI group
vlsi_time_block: TimeBlock = TimeBlock(start=Time(17, 30), end=Time(19, 00))
vlsi_datetime = {Weekday.TUESDAY: vlsi_time_block, Weekday.THURSDAY: vlsi_time_block}
vlsi_group: Group = Group(4, 1535, "M.I. RAFAEL PRIETO MELENDEZ", vlsi_datetime)

def test_group_class():
    assert our_group.key_code == 2
    assert len(our_group.time_blocks[Weekday.MONDAY]) == 2 * 60

    assert our_group.subject_key == their_group.subject_key
    assert our_group.professor != their_group.professor
    assert our_group.time_blocks != their_group.time_blocks
    assert our_group.time_blocks[Weekday.MONDAY] < their_group.time_blocks[Weekday.MONDAY]
    assert len(their_group.time_blocks[Weekday.MONDAY]) == 2 * 60

    assert vlsi_group.subject_key != our_group.subject_key
    assert vlsi_group.professor != our_group.professor
    assert vlsi_group.time_blocks[Weekday.THURSDAY] > our_group.time_blocks[Weekday.WEDNESDAY]
    assert vlsi_group.time_blocks[Weekday.THURSDAY] > their_group.time_blocks[Weekday.WEDNESDAY]
    assert len(vlsi_group.time_blocks[Weekday.TUESDAY]) == 1.5 * 60

def test_schedule_print():
    schedule = [our_group, vlsi_group]
    schedule_str = get_schedule_str(schedule)
    assert schedule_str == [
        ['Time', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat'],
        ['13:00', '406', '', '406', '', '', ''],
        ['13:30', '406', '', '406', '', '', ''],
        ['14:00', '406', '', '406', '', '', ''],
        ['14:30', '406', '', '406', '', '', ''],
        ['15:00', '', '', '', '', '', ''],
        ['15:30', '', '', '', '', '', ''],
        ['16:00', '', '', '', '', '', ''],
        ['16:30', '', '', '', '', '', ''],
        ['17:00', '', '', '', '', '', ''],
        ['17:30', '', '1535', '', '1535', '', ''],
        ['18:00', '', '1535', '', '1535', '', ''],
        ['18:30', '', '1535', '', '1535', '', '']
    ]

def test_schedule_details():
    schedule = [our_group, vlsi_group]
    schedule_details = get_schedule_details(schedule)
    assert schedule_details == """406 - INTELIGENCIA ARTIFICIAL
Group: 2
Professor: DR. JOSE JAIME CAMACHO ESCOTO
--------------------------------------------------
1535 - DISEÑO DIGITAL VLSI
Group: 4
Professor: M.I. RAFAEL PRIETO MELENDEZ"""

def test_a():
    schedule = [our_group, vlsi_group]
    schedule_details = get_schedule_details(schedule)
    print(schedule_details)    

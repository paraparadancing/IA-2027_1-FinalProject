import pytest

from schebuilder.generator import (
    Weekday,
    ClassType,
    Subject,
    Professor,
    Time,
    TimeBlock,
    Group,
    Schedule
)

def test_group_class():
    ai: Subject = Subject(406, ClassType.THEORY)
    # First AI group
    camacho: Professor = Professor("DR. JOSE JAIME CAMACHO ESCOTO", 10.0)
    our_ai_time_block: TimeBlock = TimeBlock(start=Time(13, 00), end=Time(15, 00))
    our_ai_datetime= {Weekday.MONDAY: our_ai_time_block, Weekday.WEDNESDAY: our_ai_time_block}
    our_group: Group = Group(2, ai, camacho, our_ai_datetime)
    # Second AI group
    mureddu: Professor = Professor("ING. RODRIGO ARAGON MUREDDU", 8.0)
    their_ai_time_block: TimeBlock = TimeBlock(start=Time(15, 00), end=Time(17, 00))
    their_ai_datetime = {Weekday.MONDAY: their_ai_time_block, Weekday.WEDNESDAY: their_ai_time_block}
    their_group: Group = Group(4, ai, mureddu, their_ai_datetime)
    # VLSI group
    vlsi: Subject = Subject(1535, ClassType.THEORY)
    prieto: Professor = Professor("M.I. RAFAEL PRIETO MELENDEZ", 7.5)
    vlsi_time_block: TimeBlock = TimeBlock(start=Time(17, 30), end=Time(19, 00))
    vlsi_datetime = {Weekday.TUESDAY: vlsi_time_block, Weekday.THURSDAY: vlsi_time_block}
    vlsi_group: Group = Group(4, vlsi, prieto, vlsi_datetime)

    assert our_group.professor == camacho
    assert our_group.key_code == 2
    assert len(our_group.time_blocks[Weekday.MONDAY]) == 2 * 60
    assert our_group.subject == ai

    assert our_group.subject == their_group.subject
    assert our_group.professor != their_group.professor
    assert our_group.time_blocks != their_group.time_blocks
    assert our_group.time_blocks[Weekday.MONDAY] < their_group.time_blocks[Weekday.MONDAY]
    assert len(their_group.time_blocks[Weekday.MONDAY]) == 2 * 60
    assert our_group.professor > their_group.professor

    assert vlsi_group.subject != our_group.subject
    assert vlsi_group.professor != our_group.professor
    assert vlsi_group.time_blocks[Weekday.THURSDAY] > our_group.time_blocks[Weekday.WEDNESDAY]
    assert vlsi_group.time_blocks[Weekday.THURSDAY] > their_group.time_blocks[Weekday.WEDNESDAY]
    assert len(vlsi_group.time_blocks[Weekday.TUESDAY]) == 1.5 * 60
    assert vlsi_group.professor < our_group.professor
    assert vlsi_group.professor < their_group.professor

    my_schedule: Schedule = Schedule({our_group, vlsi_group})
    
    assert our_group in my_schedule and their_group not in my_schedule


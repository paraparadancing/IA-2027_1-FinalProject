import pytest

from schebuilder.generator import (
    Weekday,
    ClassType,
    Time,
    TimeBlock,
    Group
)

def test_group_class():
    ai = 406
    # First AI group
    camacho = "DR. JOSE JAIME CAMACHO ESCOTO"
    our_ai_time_block: TimeBlock = TimeBlock(start=Time(13, 00), end=Time(15, 00))
    our_ai_datetime= {Weekday.MONDAY: our_ai_time_block, Weekday.WEDNESDAY: our_ai_time_block}
    our_group: Group = Group(2, ai, camacho, our_ai_datetime)
    # Second AI group
    mureddu = "ING. RODRIGO ARAGON MUREDDU"
    their_ai_time_block: TimeBlock = TimeBlock(start=Time(15, 00), end=Time(17, 00))
    their_ai_datetime = {Weekday.MONDAY: their_ai_time_block, Weekday.WEDNESDAY: their_ai_time_block}
    their_group: Group = Group(4, ai, mureddu, their_ai_datetime)
    # VLSI group
    vlsi = 1535
    prieto = "M.I. RAFAEL PRIETO MELENDEZ"
    vlsi_time_block: TimeBlock = TimeBlock(start=Time(17, 30), end=Time(19, 00))
    vlsi_datetime = {Weekday.TUESDAY: vlsi_time_block, Weekday.THURSDAY: vlsi_time_block}
    vlsi_group: Group = Group(4, vlsi, prieto, vlsi_datetime)

    assert our_group.professor == camacho
    assert our_group.key_code == 2
    assert len(our_group.time_blocks[Weekday.MONDAY]) == 2 * 60
    assert our_group.subject_key == ai

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


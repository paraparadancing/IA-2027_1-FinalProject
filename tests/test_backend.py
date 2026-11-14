import generator_backend

from schebuilder.generator import (
    Subject,
    ClassType,
    Professor,
    TimeBlock,
    Time,
    Weekday,
    Group
)

def test_backend_import():
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
    
    generator_backend.read_group(our_group)
    generator_backend.read_group(their_group)
    generator_backend.read_group(vlsi_group)

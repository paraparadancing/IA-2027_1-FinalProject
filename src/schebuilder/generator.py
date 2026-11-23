from math import gcd
from functools import reduce
from enum import Enum, auto
from schebuilder.subjects import subject_names

class Weekday(Enum):
    MONDAY = 1
    TUESDAY = 2
    WEDNESDAY = 3
    THURSDAY = 4
    FRIDAY = 5
    SATURDAY = 6

class ClassType(Enum):
    THEORY = auto()
    LABORATORY = auto()
    LABORATORY_PLUS = auto()

SEPARATOR_AMOUNT = 50

class Time:
    """Represents an amount of time (e.g. 2h 15m) or a time of day (e.g. 2:15)."""
    @classmethod
    def format_time(cls, input_time: int)-> str:
        return str(input_time) if input_time > 9 else f"0{input_time}"

    def __init__(self, hours: int, minutes: int):
        if not 0 <= hours <= 23:  # 24-hour format
            raise ValueError("Hours must range between 0 and 23 hours")
        if not 0 <= minutes <= 59:
            raise ValueError("Minutes must range between 0 and 59 minutes")
        self.hours = hours
        self.minutes = minutes

    def to_hours(self) -> float:
        return self.hours + self.minutes / 60

    def to_minutes(self) -> int:
        return self.hours * 60 + self.minutes

    def __lt__(self, other: "Time") -> bool:
        return (self.hours, self.minutes) < (other.hours, other.minutes)

    def __gt__(self, other: "Time") -> bool:
        return (self.hours, self.minutes) > (other.hours, other.minutes)

    def __le__(self, other: "Time") -> bool:
        return (self.hours, self.minutes) <= (other.hours, other.minutes)

    def __ge__(self, other: "Time") -> bool:
        return (self.hours, self.minutes) >= (other.hours, other.minutes)

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Time) and 
            (self.hours, self.minutes) == (other.hours, other.minutes)
        )

    def __add__(self, other: "Time") -> "Time":
        total_minutes = self.to_minutes() + other.to_minutes()
        return Time(total_minutes // 60 % 24, total_minutes % 60)

    def __sub__(self, other: "Time") -> "Time":
        diff_minutes = self.to_minutes() - other.to_minutes()
        if diff_minutes < 0:
            diff_minutes += 24 * 60
        return Time(diff_minutes // 60, diff_minutes % 60)

    def __hash__(self) -> int:
        return hash((self.hours, self.minutes))

    def __repr__(self):
        return f"{Time.format_time(self.hours)}:{Time.format_time(self.minutes)}"

class TimeBlock:
    """Continuous time range [start, end) within a single day."""
    def __init__(self, start: Time, end: Time):
        if start >= end:
            raise ValueError("Second element must be greater than the first")
        self.start = start
        self.end = end

    def __len__(self) -> int:
        return (self.end - self.start).to_minutes()

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, TimeBlock) and 
            self.start == other.start and self.end == other.end
        )

    def __gt__(self, other: "TimeBlock") -> bool:
        return self.start > other.start or self.end > other.end

    def __lt__(self, other: "TimeBlock") -> bool:
        return self.start < other.start or self.end < other.end

    def __repr__(self):
        return f"[{self.start}, {self.end}]"


class Group:
    def __init__(
        self,
        key_code: int,
        subject_key: int,
        professor: str | None,
        time_blocks: dict[Weekday, TimeBlock],
    ):
        if key_code < 0:
            raise ValueError("Group's key code must be a non-negative number")
        if subject_key < 0:
            raise ValueError("Subject's key code must be a non-negative number")
        self.key_code = key_code
        self.subject_key = subject_key
        self.professor = professor
        self.time_blocks = time_blocks

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Group) and
            self.key_code == other.key_code and
            self.subject_key == other.subject_key
        )
    
    def __hash__(self):
        return hash((self.key_code, self.subject_key))

    def __str__(self):
        return (
            f"Group keycode: {self.key_code}\n"
            f"Subject keycode: {self.subject_key}\n"
            f"Professor: {self.professor}\n"
            f"Time blocks: {self.time_blocks}"
        )

def get_minimum_time(schedule: list[Group])-> Time:
    output = Time(23, 59)
    for group in schedule:
        for k, v in group.time_blocks.items():
            if v.start < output:
                output = v.start

    return output

def get_maximum_time(schedule: list[Group])-> Time:
    output = Time(0, 0)
    for group in schedule:
        for k, v in group.time_blocks.items():
            if v.end > output:
                output = v.end

    return output

def get_step(schedule: list[Group]) -> int:
    times = [60]
    for group in schedule:
        for block in group.time_blocks.values():
            times.append(block.start.to_minutes())
            times.append(block.end.to_minutes())
    return reduce(gcd, times)

# A schedule is a list of Groups
#   e.g. some_schedule = [group_1, group_2, group_3]

def get_schedule_str(
    schedule: list[Group],
    start_time: Time | None = None,
    end_time: Time | None = None,
    time_step: int | None = None # in minutes
)-> list[list[str]]:
    if start_time is None:
        start_time = get_minimum_time(schedule)
    if end_time is None:
        end_time = get_maximum_time(schedule)
    if time_step is None:
        time_step = get_step(schedule)

    headers = ["Time", "mon", "tue", "wed", "thu", "fri", "sat"]
    num_rows = (end_time - start_time).to_minutes() // time_step

    output = [headers]
    for j in range(num_rows):
        offset = j * time_step
        block_start = start_time + Time(offset // 60, offset % 60)
        output.append([str(block_start)] + [""] * 6)

    for group in schedule:
        for k, v in group.time_blocks.items():
            col = k.value
            for row in output[1:]:
                block_start = Time(*map(int, row[0].split(":")))
                if v.start <= block_start < v.end:
                    row[col] = str(group.subject_key)

    return output

def get_anonymous_subject_name(count: int) -> str:
    if count < 1:
        raise ValueError("Argument should be positive number.")
    result = ""
    while count > 0:
        count, remainder = divmod(count - 1, 26)
        result = chr(ord("A") + remainder) + result
    return result

def get_schedule_details(schedule: list[Group])-> str:
    output = []
    letter_amount = 0
    for group in schedule:
        group_name = subject_names.get(group.subject_key)
        if group_name is None:
            group_name = get_anonymous_subject_name(letter_amount)
            letter_amount += 1
        output.append('\n'.join((
            f"{group.subject_key} - {group_name}",
            f"Group: {group.key_code}",
            f"Professor: {group.professor}"
        )))

    return f"\n{''.join('-' for r in range(SEPARATOR_AMOUNT))}\n".join(output)

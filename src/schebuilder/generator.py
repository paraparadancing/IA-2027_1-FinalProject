from enum import Enum, auto

class Weekday(Enum):
    MONDAY = auto()
    TUESDAY = auto()
    WEDNESDAY = auto()
    THURSDAY = auto()
    FRIDAY = auto()
    SATURDAY = auto()

class ClassType(Enum):
    THEORY = auto()
    LABORATORY = auto()
    LABORATORY_PLUS = auto()


class Time:
    """Represents an amount of time (e.g. 2h 15m) or a time of day (e.g. 2:15)."""
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
        return f"{self.hours}:{self.minutes}"


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

# A schedule is a list of Groups
#   e.g. some_schedule = [group_1, group_2, group_3]

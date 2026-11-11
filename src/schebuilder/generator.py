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

class Subject:
    def __init__(self, key_code: int, class_type: ClassType):
        if key_code < 1:
            raise ValueError("Subject's key code must be a positive number")
        self.key_code = key_code
        self.type = class_type

        def __eq__(self, other: Subject) -> bool:
            return self.key_code == other.key_code

class Professor:
    def __init__(self, name: str, score: float):
        self.name = name
        self.score = score

    def __eq__(self, other: Professor) -> bool:
        return self.name == other.name
    
    def __gt__(self, other:Professor) -> bool:
        return self.score > other.score

    def __lt__(self, other:Professor) -> bool:
        return self.score < other.score

class Time:
    """
        Can represent either an amount of time (e.g. 2 hours and 15 minutes)
        or an specific time of the day (e.g. 2:15).
    """
    def __init__(self, hours: int, minutes: int):
        if hours < 0 or hours > 23: # 24 hour format
            raise ValueError("Hours must range between 0 and 23 hours")
        if minutes < 0 or minutes > 59:
            raise ValueError("Minutes must range between 0 and 59 minutes")
        self.hours = hours
        self.minutes = minutes

    def to_hours(self) -> float:
        return float(self.hours) + float(self.minutes)/60

    def to_minutes(self) -> int:
        return self.hours * 60 + self.minutes

    def __lt__(self, other: Time) -> bool:
        return self.hours < other.hours or (self.hours == other.hours and self.minutes < other.minutes)

    def __gt__(self, other: Time) -> bool:
        return self.hours > other.hours or (self.hours == other.hours and self.minutes > other.minutes)

    def __eq__(self, other: Time) -> bool:
        return self.hours == other.hours and self.minutes == other.minutes

    def __ge__(self, other: Time) -> bool:
        return (
            (self.hours > other.hours) or (self.hours == other.hours and self.minutes > other.minutes) or
            (self.hours == other.hours and self.minutes == other.minutes)
        )

    def __le__(self, other: Time) -> bool:
        return (
            (self.hours < other.hours) or (self.hours == other.hours and self.minutes < other.minutes) or
            (self.hours == other.hours and self.minutes == other.minutes)
        )

    def __add__(self, other: Time) -> Time:
        return Time(self.hours + other.hours, self.minutes + other.minutes)

    def __sub__(self, other: Time) -> Time:
        minute_substraction = self.minutes - other.minutes
        minute_result = minute_substraction if minute_substraction >= 0 else minute_substraction + 60
        hour_borrow = 1 if minute_substraction < 0 else 0
        return Time(self.hours - other.hours - hour_borrow, minute_result)

    def __len__(self) -> Time:
        return self

class TimeBlock:
    """
        Continuous time range between `start` and `end`.
        It can only represent a time range within a day.
        Time range is start-inclusive and end-exclusive `[start, end)`
    """
    def __init__(self, start: Time, end: Time):
        if start >= end:
            raise ValueError("Second element must be greater than the first")
        self.start = start
        self.end = end

    def __len__(self) -> Time:
        return (self.end - self.start).to_minutes()

    def __eq__(self, other: TimeBlock) -> bool:
        return self.start == other.start and self.end == other.end

    def __gt__(self, other: TimeBlock) -> bool:
        return self.start > other.start or self.end > other.end

    def __lt__(self, other: TimeBlock) -> bool:
        return self.start < other.start or self.end < other.end

class Group:
    def __init__(
            self,
            key_code: int,
            subject: Subject,
            professor: Professor,
            time_blocks: dict[Weekday, TimeBlock]
        ):
        if key_code < 1:
            raise ValueError("Group's key code must be a positive number")
        self.key_code = key_code
        self.subject = subject
        self.professor = professor
        self.time_blocks = time_blocks

    def __eq__(self, other: Group) -> bool:
        return (
            self.key_code == other.key_code and
            self.subject.key_code == other.subject.key_code
        )
    
    def __hash__(self):
        return hash((self.key_code, self.subject.key_code))

class Schedule:
    def __init__(self, groups: set[Group]):
        self.groups = groups

    def __contains__(self, item: Group) -> bool:
        return item in self.groups

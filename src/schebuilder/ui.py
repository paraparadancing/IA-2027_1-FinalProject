import csv
import sys
from functools import lru_cache
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QDialog, QFileDialog, QHBoxLayout,
    QHeaderView, QLineEdit, QLabel, QListWidget, QMessageBox, QPlainTextEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget,
)

from generator_backend import generate_valid_schedules
from .filter import FiltroHorarios
from .generator import Group, Weekday
from .loader import load_from_csv


def get_schedule_str(schedule: list[Group]) -> list[list[str]]:
    """Return a weekly grid, retaining exact boundaries for off-grid classes."""
    rows = [["Time", *(day.name[:3].lower() for day in Weekday)]]
    sessions = [
        (day, block.start.to_minutes(), block.end.to_minutes(), str(group.subject_key))
        for group in schedule for day, block in group.time_blocks.items()
    ]
    if not sessions:
        return rows

    boundaries = {point for _, start, end, _ in sessions for point in (start, end)}
    first, last = min(boundaries), max(boundaries)
    boundaries.update(range((first + 29) // 30 * 30, last, 30))
    for minute in sorted(boundaries - {last}):
        row = [f"{minute // 60:02d}:{minute % 60:02d}"] + [""] * len(Weekday)
        for day, start, end, subject in sessions:
            if start <= minute < end:
                row[day.value] = subject
        rows.append(row)
    return rows


def index_schedules(subjects):
    """Count valid completions, sharing counts for equivalent remaining choices."""

    # The backend accepts a group exactly when it fits every previous group.
    # Ask it for valid adjacent and non-adjacent subject pairs alike.
    compatible = []
    for depth, groups in enumerate(subjects):
        by_group = [[] for _ in groups]
        for other in subjects[depth + 1:]:
            # Bindings return references to the same Group objects.
            other_bits = {id(group): 1 << i for i, group in enumerate(other)}
            masks = {id(group): 0 for group in groups}
            for left, right in generate_valid_schedules([groups, other]):
                masks[id(left)] |= other_bits[id(right)]
            for row, group in zip(by_group, groups):
                row.append(masks[id(group)])
        compatible.append(by_group)

    @lru_cache(maxsize=8192)
    def count(remaining):
        if len(remaining) == 1:
            return remaining[0].bit_count()
        depth = len(subjects) - len(remaining)
        choices = remaining[0]
        total = 0
        while choices:
            bit = choices & -choices
            choices ^= bit
            masks = compatible[depth][bit.bit_length() - 1]
            tail = tuple(a & b for a, b in zip(remaining[1:], masks))
            if all(tail):
                total += count(tail)
        return total

    available = tuple((1 << len(groups)) - 1 for groups in subjects)
    def schedule_at(rank):
        remaining = available
        chosen = []
        for depth, groups in enumerate(subjects):
            choices = remaining[0]
            while choices:
                bit = choices & -choices
                choices ^= bit
                index = bit.bit_length() - 1
                tail = tuple(a & b for a, b in zip(remaining[1:], compatible[depth][index]))
                size = count(tail) if tail else 1
                if rank < size:
                    chosen.append([groups[index]])
                    remaining = tail
                    break
                rank -= size
            else:
                raise IndexError("Schedule number out of range")
        return generate_valid_schedules(chosen)[0]

    return count(available), schedule_at


STYLE = """
QWidget { color: #24344a; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
QDialog, QWidget#builder { background: #f4f7fb; }
QTableWidget, QListWidget, QPlainTextEdit, QLineEdit {
    background: white; alternate-background-color: #f5f8fc; border: 1px solid #ccd7e2;
    border-radius: 6px; selection-background-color: #365d86; selection-color: white;
}
QTableWidget { gridline-color: #e0e6ed; }
QHeaderView::section { background: #263d57; color: white; padding: 6px; border: 0; }
QPushButton { background: white; border: 1px solid #bdcbd9; border-radius: 6px; padding: 6px 12px; }
QPushButton:hover { background: #e2ecf8; }
QPushButton:disabled { color: #8390a0; background: #edf1f5; }
QPushButton#primary { background: #254d74; color: white; }
QLabel#position { font-size: 16px; font-weight: bold; }
"""
COLORS = ("#abd8f2", "#ffbfad", "#b5e0be", "#ffdb91", "#d3c0f1", "#9cddda", "#f2bdd9")


class ScheduleWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("builder")
        self.setStyleSheet(STYLE)
        self.setWindowTitle("Schedule Builder")
        self.resize(640, 400)
        self.subjects: dict[Path, list[Group]] = {}
        self.file_list = QListWidget()
        self.file_list.setAlternatingRowColors(True)
        load_button = QPushButton("Load CSV files…")
        load_button.clicked.connect(self.load_files)
        self.remove_button = QPushButton("Remove CSV")
        self.remove_button.setEnabled(False)
        self.remove_button.clicked.connect(self.remove_file)
        self.file_list.currentRowChanged.connect(
            lambda row: self.remove_button.setEnabled(row >= 0)
        )
        buttons = QHBoxLayout()
        buttons.addWidget(load_button)
        buttons.addWidget(self.remove_button)
        buttons.addStretch()

        self.rules_input = QPlainTextEdit()
        self.rules_input.setPlaceholderText("Monday 13:00-15:00\nFriday 08:00-10:00")
        self.rules_input.setMaximumHeight(85)
        generate_button = QPushButton("Generate schedules")
        generate_button.setObjectName("primary")
        generate_button.clicked.connect(self.generate_schedules)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Loaded subjects"))
        layout.addWidget(self.file_list)
        layout.addLayout(buttons)
        layout.addWidget(QLabel("Unavailable times (one rule per line)"))
        layout.addWidget(self.rules_input)
        layout.addWidget(generate_button)

    def load_files(self):
        filenames, _ = QFileDialog.getOpenFileNames(
            self, "Select subject files", "", "CSV files (*.csv)"
        )
        for filename in filenames:
            path = Path(filename)
            if path in self.subjects:
                continue
            try:
                groups = load_from_csv(path)
            except (OSError, UnicodeError, csv.Error) as error:
                QMessageBox.warning(self, "Could not load CSV", f"{path.name}\n{error}")
                continue
            if not groups:
                QMessageBox.warning(self, "Empty subject", f"No valid groups in {path.name}.")
                continue
            self.subjects[path] = groups
            self.file_list.addItem(f"{path.name}  —  {len(groups)} groups")
            self.file_list.setCurrentRow(self.file_list.count() - 1)

    def remove_file(self):
        row = self.file_list.currentRow()
        if row >= 0:
            del self.subjects[list(self.subjects)[row]]
            self.file_list.takeItem(row)

    def generate_schedules(self):
        if not self.subjects:
            QMessageBox.information(self, "No subjects", "Load at least one CSV file.")
            return
        subjects = list(self.subjects.values())
        for number, line in enumerate(self.rules_input.toPlainText().splitlines(), start=1):
            if not line.strip():
                continue
            try:
                day, interval = line.split(maxsplit=1)
                start, end = interval.split("-")
                rule = FiltroHorarios(day, start.strip(), end.strip())
            except ValueError:
                QMessageBox.warning(self, "Invalid rule",
                                    f"Check line {number}: {line}\nExample: Monday 13:00-15:00.")
                return
            subjects = rule.filtrar_materias(subjects)
        for path, groups in zip(self.subjects, subjects):
            if not groups:
                QMessageBox.information(self, "No available groups",
                                        f"No groups from {path.name} meet your rules.")
                return
        total, schedule_at = index_schedules(subjects)
        if not total:
            QMessageBox.information(self, "No schedules", "No conflict-free combination.")
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Generated schedules")
        dialog.resize(1020, 740)
        first = QPushButton("First")
        previous = QPushButton("Previous")
        following = QPushButton("Next")
        last = QPushButton("Last")
        position = QLabel()
        position.setObjectName("position")
        target = QLineEdit()
        target.setPlaceholderText("Schedule #")
        target.setAccessibleName("Schedule number")
        target.setMaximumWidth(110)
        jump = QPushButton("Go")
        navigation = QHBoxLayout()
        for control in (first, previous, position, following, last):
            navigation.addWidget(control)
        navigation.addStretch()
        navigation.addWidget(target)
        navigation.addWidget(jump)
        index = 0
        labels = {}
        for path, groups in self.subjects.items():
            for group in groups:
                labels.setdefault(group.subject_key, path.stem.removesuffix("_groups").replace("_", " ").upper())
        palette = {key: QColor(COLORS[i]) if i < len(COLORS)
                   else QColor.fromHsv(i * 137 % 360, 78, 244)
                   for i, key in enumerate(sorted(labels))}
        details = QPlainTextEdit()
        details.setReadOnly(True)
        details.setMaximumHeight(75)
        details.setAccessibleName("Schedule details")

        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.verticalHeader().hide()
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)

        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.verticalHeader().setDefaultSectionSize(32)

        def show_schedule(number):
            nonlocal index
            index = number
            schedule = schedule_at(index)
            headers, *rows = get_schedule_str(schedule)
            table.clearSpans()
            table.clearContents()
            table.setColumnCount(len(headers))
            table.setHorizontalHeaderLabels([header.title() for header in headers])
            table.setRowCount(len(rows))
            row_by_time = {row[0]: i for i, row in enumerate(rows)}
            for row_index, row in enumerate(rows):
                item = QTableWidgetItem(row[0])
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                table.setItem(row_index, 0, item)
            for group in schedule:
                for day, block in group.time_blocks.items():
                    start = f"{block.start.hours:02d}:{block.start.minutes:02d}"
                    end = f"{block.end.hours:02d}:{block.end.minutes:02d}"
                    r = row_by_time[start]
                    height = row_by_time.get(end, len(rows)) - r
                    if height > 1:
                        table.setSpan(r, day.value, height, 1)
                    key = group.subject_key
                    item = QTableWidgetItem(f"{labels[key]}  ·  G{group.key_code}")
                    item.setBackground(palette[key])
                    item.setForeground(QColor("#152c42"))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setToolTip(f"{key} | {start}–{end} | {group.professor or 'Unassigned'}")
                    table.setItem(r, day.value, item)
            # Connect the team's detail formatter here when it becomes available.
            details.clear()
            position.setText(f"Schedule {index + 1:,} of {total:,}")
            for button in (first, previous):
                button.setEnabled(index > 0)
            for button in (last, following):
                button.setEnabled(index < total - 1)

        def jump_to_number():
            try:
                number = int(target.text().strip().replace(",", ""))
            except ValueError:
                number = 0
            if 1 <= number <= total:
                show_schedule(number - 1)
            else:
                QMessageBox.warning(dialog, "Schedule number", f"Enter a number from 1 to {total:,}.")

        first.clicked.connect(lambda: show_schedule(0))
        last.clicked.connect(lambda: show_schedule(total - 1))
        previous.clicked.connect(lambda: show_schedule(index - 1))
        following.clicked.connect(lambda: show_schedule(index + 1))
        jump.clicked.connect(jump_to_number)
        target.returnPressed.connect(jump_to_number)
        for button in (first, last, previous, following, jump):
            button.setAutoDefault(False)
        show_schedule(0)
        layout = QVBoxLayout(dialog)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.addLayout(navigation)
        layout.addWidget(table)
        layout.addWidget(QLabel("Schedule details"))
        layout.addWidget(details)
        dialog.exec()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ScheduleWindow()
    window.show()
    sys.exit(app.exec())

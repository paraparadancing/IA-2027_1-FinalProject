import csv
import sys
from functools import lru_cache
from html import escape
from math import ceil
from pathlib import Path

from PySide6.QtCore import QIODevice, QSaveFile, Qt, QTime
from PySide6.QtGui import (
    QColor, QImage, QPageLayout, QPageSize, QPainter, QPdfWriter, QTextDocument,
)
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QDialog, QFileDialog,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QMenu,
    QMessageBox, QPlainTextEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QTimeEdit, QVBoxLayout, QWidget,
)

from generator_backend import generate_valid_schedules
from schebuilder.filter import FiltroHorarios
from schebuilder.generator import Group, Weekday, get_schedule_details
from schebuilder.loader import load_from_csv


def get_schedule_str(schedule: list[Group]) -> list[list[str]]:
    """Return a weekly grid, retaining exact boundaries for off-grid classes."""
    rows = [["Time", *(day.name[:3].lower() for day in Weekday)]]
    sessions = [
        (day, block.start.to_minutes(), block.end.to_minutes(), str(group.subject_key))
        for group in schedule
        for day, block in group.time_blocks.items()
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
    """Count valid schedules and retrieve one by its zero-based rank."""
    compatible = []
    for depth, groups in enumerate(subjects):
        by_group = [[] for _ in groups]
        for other in subjects[depth + 1:]:
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
                tail = tuple(
                    a & b
                    for a, b in zip(remaining[1:], compatible[depth][index])
                )
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
QWidget {
    color: #24344a;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}
QDialog, QWidget#builder {
    background: #f4f7fb;
}
QTableWidget, QListWidget, QPlainTextEdit, QLineEdit {
    background: white;
    alternate-background-color: #f5f8fc;
    border: 1px solid #ccd7e2;
    border-radius: 6px;
    selection-background-color: #365d86;
    selection-color: white;
}
QTimeEdit, QTimeEdit QLineEdit {
    background-color: white;
    color: #152c42;
    selection-background-color: #254d74;
    selection-color: white;
}
QTimeEdit {
    border: 1px solid #9babbc;
    border-radius: 5px;
    padding: 4px;
}
QTimeEdit:focus {
    border: 1px solid #254d74;
}
QTimeEdit:disabled, QTimeEdit:disabled QLineEdit {
    background-color: #edf1f5;
    color: #556575;
}
QTableWidget {
    gridline-color: #e0e6ed;
}
QHeaderView::section {
    background: #263d57;
    color: white;
    padding: 6px;
    border: 0;
}
QPushButton {
    background: white;
    border: 1px solid #bdcbd9;
    border-radius: 6px;
    padding: 6px 12px;
}
QPushButton:hover {
    background: #e2ecf8;
}
QPushButton:disabled {
    color: #8390a0;
    background: #edf1f5;
}
QPushButton#primary {
    background: #254d74;
    color: white;
}
QMenu {
    background-color: #ffffff;
    color: #152c42;
    border: 1px solid #9babbc;
}
QMenu::item {
    background-color: #ffffff;
    color: #152c42;
    padding: 7px 18px;
}
QMenu::item:selected {
    background-color: #254d74;
    color: #ffffff;
}
QLabel#position {
    font-size: 16px;
    font-weight: bold;
}
"""

COLORS = (
    "#abd8f2", "#ffbfad", "#b5e0be", "#ffdb91",
    "#d3c0f1", "#9cddda", "#f2bdd9",
)


def export_schedule(table, details, title, path, extension):
    """Write the displayed schedule, including rows outside the visible area."""
    headers = [
        table.horizontalHeaderItem(column).text()
        for column in range(table.columnCount())
    ]
    header_cells = "".join(
        f'<th width="112" bgcolor="#263d57">'
        f'<font color="white">{escape(header)}</font></th>'
        for header in headers
    )
    rows = ["<tr>" + header_cells + "</tr>"]

    # Write each class once, even when its cell spans several time slots.
    occupied_until = [0] * len(headers)
    for row in range(table.rowCount()):
        cells = []
        for column in range(len(headers)):
            if row < occupied_until[column]:
                continue

            item = table.item(row, column)
            span = table.rowSpan(row, column)
            occupied_until[column] = row + span

            color = item.background().color().name() if column and item else "#ffffff"
            label = escape(item.text()) if item else "&nbsp;"
            cells.append(
                f'<td align="center" valign="middle" rowspan="{span}" '
                f'bgcolor="{color}">{label}</td>'
            )

        rows.append("<tr>" + "".join(cells) + "</tr>")

    document = QTextDocument()
    document.setDefaultStyleSheet("""
        h2, h3, p, td { color: #152c42; }
        th { color: #ffffff; }
    """)
    document.setDocumentMargin(20)
    document.setHtml(
        f"<h2>{escape(title)}</h2>"
        '<table cellspacing="1" cellpadding="4" bgcolor="#ccd7e2">'
        + "".join(rows)
        + "</table><h3>Schedule details</h3><p>"
        + "<br>".join(escape(line) for line in details.splitlines())
        + "</p>"
    )

    output = QSaveFile(str(path))
    if not output.open(QIODevice.OpenModeFlag.WriteOnly):
        raise OSError(output.errorString())

    if extension == "pdf":
        writer = QPdfWriter(output)
        writer.setResolution(96)
        writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        writer.setPageOrientation(QPageLayout.Orientation.Landscape)
        document.print_(writer)
        del writer
    else:
        document.setTextWidth(960)
        size = document.size()
        image = QImage(
            ceil(size.width() * 2),
            ceil(size.height() * 2),
            QImage.Format.Format_RGB32,
        )
        if image.isNull():
            raise OSError("Insufficient memory to create the image.")

        image.fill(Qt.GlobalColor.white)
        painter = QPainter(image)
        try:
            painter.scale(2, 2)
            document.drawContents(painter)
        finally:
            painter.end()

        if not image.save(output, "JPEG", 95):
            raise OSError("Could not write the JPEG image.")

    if not output.commit():
        raise OSError(output.errorString())


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
        self.rules_input.setPlaceholderText(
            "Daily 13:00-15:00\nFriday 08:00-10:00"
        )
        self.rules_input.setMaximumHeight(85)

        weekdays = QHBoxLayout()
        day_boxes = {}
        for day in Weekday:
            box = QCheckBox(day.name[:3].title())
            day_boxes[day] = box
            weekdays.addWidget(box)

        every_day = QPushButton("Select all days")

        def select_all_days():
            for box in day_boxes.values():
                box.setChecked(True)

        every_day.clicked.connect(select_all_days)
        weekdays.addWidget(every_day)

        interval = QHBoxLayout()
        start_time = QTimeEdit(QTime(13, 0))
        end_time = QTimeEdit(QTime(15, 0))
        all_day = QCheckBox("All day free")

        for label, edit in (("From", start_time), ("To", end_time)):
            edit.setDisplayFormat("HH:mm")
            interval.addWidget(QLabel(label))
            interval.addWidget(edit)
            all_day.toggled.connect(edit.setDisabled)

        interval.addWidget(all_day)
        add_block = QPushButton("Add block")
        interval.addWidget(add_block)

        def add_time_block():
            selected = [
                day.name.title()
                for day, box in day_boxes.items()
                if box.isChecked()
            ]
            if not selected:
                QMessageBox.warning(self, "Choose days", "Select at least one day.")
                return

            period = "all day"
            if not all_day.isChecked():
                if start_time.time() >= end_time.time():
                    QMessageBox.warning(
                        self, "Invalid interval",
                        "Choose an end time after the start.",
                    )
                    return
                period = f"{start_time.text()}-{end_time.text()}"

            if len(selected) == len(Weekday):
                selected = ["Daily"]

            existing = set(self.rules_input.toPlainText().splitlines())
            for day in selected:
                line = f"{day} {period}"
                if line not in existing:
                    self.rules_input.appendPlainText(line)

            for box in day_boxes.values():
                box.setChecked(False)
            all_day.setChecked(False)

        add_block.clicked.connect(add_time_block)

        generate_button = QPushButton("Generate schedules")
        generate_button.setObjectName("primary")
        generate_button.clicked.connect(self.generate_schedules)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Loaded subjects"))
        layout.addWidget(self.file_list)
        layout.addLayout(buttons)
        layout.addWidget(QLabel("Unavailable times"))
        layout.addLayout(weekdays)
        layout.addLayout(interval)
        layout.addWidget(QLabel("Active blocks (edit or delete a line to change it)"))
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
                QMessageBox.warning(
                    self, "Empty subject", f"No valid groups in {path.name}."
                )
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
                if interval.strip().casefold() == "all day":
                    start, end = "00:00", "23:59"
                else:
                    start, end = interval.split("-")

                days = list(Weekday) if day.casefold() == "daily" else [day]
                for selected_day in days:
                    rule = FiltroHorarios(selected_day, start.strip(), end.strip())
                    subjects = rule.filtrar_materias(subjects)

            except ValueError:
                QMessageBox.warning(
                    self, "Invalid rule",
                    f"Check line {number}: {line}\nExample: Monday 13:00-15:00.",
                )
                return

        for path, groups in zip(self.subjects, subjects):
            if not groups:
                QMessageBox.information(
                    self, "No available groups",
                    f"No groups from {path.name} meet your rules.",
                )
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
            name = path.stem.removesuffix("_groups").replace("_", " ").upper()
            for group in groups:
                labels.setdefault(group.subject_key, name)

        palette = {
            key: (
                QColor(COLORS[i])
                if i < len(COLORS)
                else QColor.fromHsv(i * 137 % 360, 78, 244)
            )
            for i, key in enumerate(sorted(labels))
        }

        details = QPlainTextEdit()
        details.setReadOnly(True)
        details.setMaximumHeight(75)
        details.setAccessibleName("Schedule details")

        table = QTableWidget()
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        table.verticalHeader().hide()
        table.verticalHeader().setDefaultSectionSize(32)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.setAlternatingRowColors(True)

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
                    row_index = row_by_time[start]
                    height = row_by_time.get(end, len(rows)) - row_index

                    if height > 1:
                        table.setSpan(row_index, day.value, height, 1)

                    key = group.subject_key
                    item = QTableWidgetItem(f"{labels[key]}  ·  G{group.key_code}")
                    item.setBackground(palette[key])
                    item.setForeground(QColor("#152c42"))
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    item.setToolTip(
                        f"{key} | {start}–{end} | {group.professor or 'Unassigned'}"
                    )
                    table.setItem(row_index, day.value, item)

            details.setPlainText(get_schedule_details(schedule))
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
                QMessageBox.warning(
                    dialog, "Schedule number",
                    f"Enter a number from 1 to {total:,}.",
                )

        def save_current(extension):
            picker = QFileDialog(dialog, "Save current schedule")
            picker.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            picker.setNameFilter(
                "PDF (*.pdf)" if extension == "pdf" else "JPEG (*.jpg *.jpeg)"
            )
            picker.setDefaultSuffix(extension)
            picker.selectFile(f"Schedule_{index + 1}.{extension}")

            if picker.exec():
                try:
                    export_schedule(
                        table,
                        details.toPlainText(),
                        position.text(),
                        picker.selectedFiles()[0],
                        extension,
                    )
                except OSError as error:
                    QMessageBox.warning(dialog, "Could not save schedule", str(error))

        save = QPushButton("Save schedule")
        save.setAutoDefault(False)
        menu = QMenu(save)
        menu.addAction("Save as PDF…").triggered.connect(lambda: save_current("pdf"))
        menu.addAction("Save as JPG…").triggered.connect(lambda: save_current("jpg"))
        save.setMenu(menu)
        navigation.addWidget(save)

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


def main():
    app = QApplication(sys.argv)
    window = ScheduleWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

"""Workbook adapter. The original workbook is private input and is never committed."""
from datetime import date, datetime
from pathlib import Path
from openpyxl import load_workbook
from .domain import SourceRow

REQUIRED = {"00_README", "01_Excursion_Events", "02_Product_Master", "05_SOP_Index", "06_Stability_Index"}


class WorkbookCatalog:
    def __init__(self, path: str | Path):
        book = load_workbook(path, read_only=True, data_only=True)
        try:
            self._sheets = {}
            for sheet in book:
                iterator = sheet.iter_rows(values_only=True)
                header = next(iterator, None)
                if header is None:
                    raise ValueError("sheet has no header row: " + sheet.title)
                rows = []
                for i, values in enumerate(iterator, start=2):
                    record = {str(k): v.isoformat() if isinstance(v, (date, datetime)) else v
                              for k, v in zip(header, values) if k is not None}
                    rows.append(SourceRow(sheet.title, i, record))
                self._sheets[sheet.title] = tuple(rows)
        finally:
            book.close()
        if not REQUIRED <= self._sheets.keys():
            raise ValueError("required workbook sheets missing")

    def rows(self, sheet: str) -> tuple[SourceRow, ...]:
        if sheet not in self._sheets:
            raise ValueError("unknown sheet: " + sheet)
        return self._sheets[sheet]

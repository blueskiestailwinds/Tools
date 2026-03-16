"""
parse_composite.py

Parses a Delta PBS Composite Report HTML file for one or more employees
and outputs a schedule_change_data JSON file per employee.

Usage:
    python parse_composite.py
    -> GUI file picker opens, then prompts for employee number(s).
"""

import re
import json
import os
from datetime import date, timedelta
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog, messagebox


# ---------------------------------------------------------------------------
# 1. BID PERIOD
# ---------------------------------------------------------------------------

MONTH_PERIODS = {
    0:  ((1, 1),   (1, 30),  "January"),
    1:  ((1, 31),  (3, 1),   "February"),
    2:  ((3, 2),   (3, 31),  "March"),
    3:  ((4, 1),   (5, 1),   "April"),
    4:  ((5, 2),   (6, 1),   "May"),
    5:  ((6, 2),   (7, 1),   "June"),
    6:  ((7, 2),   (7, 31),  "July"),
    7:  ((8, 1),   (8, 30),  "August"),
    8:  ((8, 31),  (9, 30),  "September"),
    9:  ((10, 1),  (10, 31), "October"),
    10: ((11, 1),  (11, 30), "November"),
    11: ((12, 1),  (12, 31), "December"),
}


def get_bid_period(month_idx: int, year: int):
    (sm, sd), (em, ed), name = MONTH_PERIODS[month_idx]
    start = date(year, sm, sd)
    end   = date(year, em, ed)
    days  = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    return name, start, end, days


def detect_bid_period_from_title(title: str):
    """
    Extract month and year from a title like 'DTW-350-A APR 2026 Composite Report'.
    Returns (month_idx, year).
    """
    month_abbrevs = {
        "jan": 0, "feb": 1, "mar": 2, "apr": 3,
        "may": 4, "jun": 5, "jul": 6, "aug": 7,
        "sep": 8, "oct": 9, "nov": 10, "dec": 11,
    }
    title_lower = title.lower()
    month_idx = None
    for abbrev, idx in month_abbrevs.items():
        if abbrev in title_lower:
            month_idx = idx
            break
    year_match = re.search(r'\b(20\d{2})\b', title)
    year = int(year_match.group(1)) if year_match else date.today().year
    return month_idx, year


# ---------------------------------------------------------------------------
# 2. EMPLOYEE DIV EXTRACTION
# ---------------------------------------------------------------------------

def find_employee_div(soup, employee_id: str):
    """
    Locate the <div id="ReasonN"> that belongs to the given employee number.
    Uses the print button whose value contains the employee ID to find N.
    """
    pattern = re.compile(re.escape(employee_id))
    btn = soup.find("input", value=pattern)
    if not btn:
        raise ValueError(f"Employee {employee_id} not found in file.")
    onclick = btn.get("onclick", "")
    m = re.search(r'makeNewWindow\((\d+)\)', onclick)
    if not m:
        raise ValueError(f"Could not determine Reason div index for {employee_id}.")
    div_id = f"Reason{m.group(1)}"
    div = soup.find("div", id=div_id)
    if not div:
        raise ValueError(f"Div #{div_id} not found.")
    return div


# ---------------------------------------------------------------------------
# 3. SPAN PARSER
# ---------------------------------------------------------------------------

SPAN_RE = re.compile(
    r'([A-Z0-9]+)\s+(\d{4}-\d{2}-\d{2})\s+[\d:]+\s+(\d{4}-\d{2}-\d{2})\s+[\d:]+'
)

VAC_RE = re.compile(r'^[PSTQF]VAC$')


def clean_text(t: str) -> str:
    """Strip non-ASCII characters (U+FFFD replacement chars etc.) and collapse whitespace."""
    return re.sub(r'\s+', ' ', re.sub(r'[^\x20-\x7E]+', ' ', t)).strip()


def parse_spans(html_fragment: str) -> list:
    """
    Extract (code, start_date, end_date) tuples from PBSEvent spans
    in an HTML fragment, handling the U+FFFD encoding artefacts.
    """
    frag_soup = BeautifulSoup(html_fragment, "html.parser")
    results = []
    for span in frag_soup.find_all("span", class_="PBSEvent"):
        cleaned = clean_text(span.get_text())
        m = SPAN_RE.match(cleaned)
        if m:
            results.append((
                m.group(1),
                date.fromisoformat(m.group(2)),
                date.fromisoformat(m.group(3)),
            ))
    return results


def fill_range(schedule, code_value, event_start, event_end, bid_start, bid_end,
               overwrite=False):
    """Fill schedule[d] = code_value for every bid-period day in [event_start, event_end]."""
    d = max(event_start, bid_start)
    while d <= min(event_end, bid_end):
        if overwrite or schedule.get(d) is None:
            schedule[d] = code_value
        d += timedelta(days=1)


# ---------------------------------------------------------------------------
# 4. PARSE ONE EMPLOYEE  (core logic, wrapped as a function)
# ---------------------------------------------------------------------------

def parse_employee(div, bid_start: date, bid_end: date) -> dict:
    raw_html = str(div)

    # Split into pre-awards and current-bid blocks
    current_bid_marker = re.compile(r'<<[\s\xa0]+Current[\s\xa0]+Bid[\s\xa0]+>>')
    cb_match = current_bid_marker.search(raw_html)

    if "Pre-Awards" in raw_html and cb_match:
        pre_block     = raw_html.split("Pre-Awards")[1][:cb_match.start()]
        current_block = raw_html[cb_match.end():]
    elif "Pre-Awards" in raw_html:
        pre_block     = raw_html.split("Pre-Awards")[1]
        current_block = ""
    else:
        pre_block     = ""
        current_block = raw_html

    # Initialise schedule
    schedule = {
        bid_start + timedelta(days=i): None
        for i in range((bid_end - bid_start).days + 1)
    }

    # A. PRE-AWARDS
    for code, event_start, event_end in parse_spans(pre_block):
        if (code not in ("ALPP", "35WD") and not VAC_RE.match(code)
                and event_start < bid_start and event_end >= bid_start):
            fill_range(schedule, "CI",   event_start, event_end, bid_start, bid_end)
        elif code == "ALPP":
            fill_range(schedule, "ALPA", event_start, event_end, bid_start, bid_end)
        elif code == "35WD":
            fill_range(schedule, "CQ",   event_start, event_end, bid_start, bid_end)
        elif VAC_RE.match(code):
            fill_range(schedule, "A",    event_start, event_end, bid_start, bid_end)

    # B. AWARDED RESERVE DAYS
    div_text_clean = clean_text(div.get_text(separator=" "))
    if "Awarded Reserve Days:" in div_text_clean:
        res_block = div_text_clean.split("Awarded Reserve Days:")[1]
        for m in re.finditer(r'(\d{4}-\d{2}-\d{2})\s*\(RES\)', res_block):
            d = date.fromisoformat(m.group(1))
            if d in schedule and schedule[d] is None:
                schedule[d] = "R"

    # C. CURRENT BID — *VAC spans
    for code, event_start, event_end in parse_spans(current_block):
        if VAC_RE.match(code):
            fill_range(schedule, "A", event_start, event_end, bid_start, bid_end)

    # D. FINAL PASS — fill remaining None -> X
    for d in schedule:
        if schedule[d] is None:
            schedule[d] = "X"

    return schedule


# ---------------------------------------------------------------------------
# 5. PROCESS ONE EMPLOYEE NUMBER  (called repeatedly for each employee)
# ---------------------------------------------------------------------------

def process_employee(employee_id: str, soup, bid_start: date, bid_end: date,
                     output_dir: str):
    """
    Parse the schedule for employee_id, write JSON to output_dir,
    and print a summary. Returns True on success, False on error.
    """
    try:
        div      = find_employee_div(soup, employee_id)
        schedule = parse_employee(div, bid_start, bid_end)
    except ValueError as e:
        print(f"  ERROR: {e}")
        return False

    print(f"  Schedule for {employee_id}:")
    for d, v in schedule.items():
        print(f"    {d}  {v}")

    output = {
        "0": {},
        "1": {
            "current": list(schedule.values())
        }
    }

    out_file = os.path.join(output_dir, f"schedule_change_data_{employee_id}.json")
    with open(out_file, "w") as f:
        json.dump(output, f, indent=2)
    print(f"  Written to {out_file}\n")
    return True


# ---------------------------------------------------------------------------
# 6. MAIN — file picker + employee input loop
# ---------------------------------------------------------------------------

def pick_file() -> str:
    """Open a GUI file picker and return the chosen path, or '' if cancelled."""
    root = tk.Tk()
    root.withdraw()  # hide the blank root window
    root.lift()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(
        title="Select PBS Composite Report",
        filetypes=[("HTML files", "*.htm *.html"), ("All files", "*.*")]
    )
    root.destroy()
    return path


def main():
    # --- GUI file picker ---
    print("Opening file picker...")
    html_file = pick_file()
    if not html_file:
        print("No file selected. Exiting.")
        return

    print(f"File: {html_file}")
    output_dir = os.path.dirname(html_file) or "."

    # --- load & parse HTML ---
    with open(html_file, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    soup = BeautifulSoup(content, "html.parser")

    # --- detect bid period ---
    title_tag = soup.find("title")
    title     = clean_text(title_tag.get_text()) if title_tag else html_file
    month_idx, year = detect_bid_period_from_title(title)
    if month_idx is None:
        print(f"ERROR: Could not detect month from title: '{title}'")
        return

    _, bid_start, bid_end, _ = get_bid_period(month_idx, year)
    print(f"Bid period: {bid_start} -> {bid_end}  ({(bid_end - bid_start).days + 1} days)\n")

    # --- employee input loop ---
    while True:
        employee_id = input("Enter employee number (or press Enter to quit): ").strip()
        if not employee_id:
            print("Done.")
            break
        process_employee(employee_id, soup, bid_start, bid_end, output_dir)


if __name__ == "__main__":
    main()

"""Parse work-report and leave-request email subjects into structured data."""

import re
from datetime import datetime
from html.parser import HTMLParser


# ---------------------------------------------------------------------------
# HTML table parser — extracts the "Project" column from work-report emails
# ---------------------------------------------------------------------------

class _TableParser(HTMLParser):
    """Stack-based HTML table extractor — handles nested tables correctly.

    Each open <table> gets its own state dict so inner tables never corrupt
    outer table row data.
    """

    def __init__(self):
        super().__init__(convert_charrefs=True)
        # Stack of state dicts, one per open <table>:
        #   rows        – completed rows for this table
        #   current_row – row being assembled, or None between <tr> tags
        #   in_cell     – True while inside <td>/<th>
        #   cell_buf    – text fragments for the current cell
        self._stack = []
        self.tables = []   # completed tables, innermost-first

    def handle_starttag(self, tag, attrs):
        t = tag.lower()
        if t == "table":
            self._stack.append({"rows": [], "current_row": None,
                                 "in_cell": False, "cell_buf": []})
        elif t == "tr" and self._stack:
            self._stack[-1]["current_row"] = []
            self._stack[-1]["in_cell"] = False
        elif t in ("td", "th") and self._stack:
            s = self._stack[-1]
            if s["current_row"] is not None:
                s["cell_buf"] = []
                s["in_cell"] = True

    def handle_endtag(self, tag):
        t = tag.lower()
        if t in ("td", "th") and self._stack:
            s = self._stack[-1]
            if s["in_cell"]:
                s["in_cell"] = False
                if s["current_row"] is not None:
                    s["current_row"].append(" ".join(s["cell_buf"]).strip())
                s["cell_buf"] = []
        elif t == "tr" and self._stack:
            s = self._stack[-1]
            if s["current_row"] is not None:
                s["rows"].append(s["current_row"])
                s["current_row"] = None
        elif t == "table" and self._stack:
            done = self._stack.pop()
            if done["rows"]:
                self.tables.append(done["rows"])

    def handle_data(self, data):
        if self._stack and self._stack[-1]["in_cell"]:
            chunk = " ".join(data.split())
            if chunk:
                self._stack[-1]["cell_buf"].append(chunk)


def _clean_cell(text: str) -> str:
    """Strip whitespace including non-breaking spaces (\xa0) from cell text."""
    return text.replace("\xa0", " ").strip()


def parse_projects_from_html(html_body: str) -> list:
    """Extract unique project names from the 'Project' column of HTML tables.

    Works with the standard work-report email format:
        SI No | Project | Task | Status | Remarks | Hours
    Finds the first table that has a header cell containing the word "project"
    (case-insensitive) and collects values from that column in all data rows.
    """
    if not html_body:
        return []

    parser = _TableParser()
    try:
        parser.feed(html_body)
    except Exception:
        return []

    projects = []
    for table in parser.tables:
        # Find the header row: any row with a cell whose text contains "project"
        project_col = None
        header_idx  = None
        for i, row in enumerate(table):
            for j, cell in enumerate(row):
                if "project" in _clean_cell(cell).lower():
                    project_col = j
                    header_idx  = i
                    break
            if project_col is not None:
                break

        if project_col is None:
            continue

        # Collect the Project cell from every data row after the header
        for row in table[header_idx + 1 :]:
            if project_col < len(row):
                val = _clean_cell(row[project_col])
                if val:
                    projects.append(val)

    # Deduplicate while preserving insertion order
    seen, unique = set(), []
    for p in projects:
        if p not in seen:
            seen.add(p)
            unique.append(p)
    return unique


# Plain-text fallback: matches "Project: Foo" lines
_PROJECT_RE = re.compile(
    r"project(?:\s+name)?\s*[:\-]\s*(.+?)(?:\r?\n|$)",
    re.IGNORECASE,
)


def parse_projects_from_body(body: str) -> list:
    """Extract project names from plain-text email body (fallback)."""
    if not body:
        return []
    return [m.strip() for m in _PROJECT_RE.findall(body) if m.strip()]

# Daily Work Report_10 Jun 2026_Muhammed Muflih C
# Daily Work Report_10 June 2026_Sanjay P
_WORK_RE = re.compile(
    r"daily\s+work\s+report[_\s]+(\d{1,2}[_\s]\w+[_\s]\d{4})[_\s]+(.+)",
    re.IGNORECASE,
)

# LEAVE REQUEST: Muhammed Muflih – ON 23-07-2024 TUESDAY (HALF DAY/FULL DAY, AN/FN)
# LEAVE REQUEST: ASMA C A ON 03-06-2026 WEDNESDAY (HALF DAY)
# Dash separator between name and ON is optional.
_LEAVE_RE = re.compile(
    r"leave\s+request\s*:\s*(.+?)\s*(?:[–\-]\s*)?on\s+(\d{2}-\d{2}-\d{4})\s+\w+\s+\((.+?)\)",
    re.IGNORECASE,
)

# Minutes of Meeting | Medit Solutions | Celine George | 05 June 2026
# Greedy .+ consumes everything up to the last | so group(1) is the date segment.
_MOM_RE = re.compile(
    r"minutes\s+of\s+meeting\b.+\|\s*(\d{1,2}\s+\w+\s+\d{4})\s*$",
    re.IGNORECASE,
)

_DATE_FMTS = ("%d %b %Y", "%d %B %Y")


def _parse_date_str(raw: str):
    """Parse '10 Jun 2026' or '10_Jun_2026'."""
    clean = raw.replace("_", " ").strip()
    for fmt in _DATE_FMTS:
        try:
            return datetime.strptime(clean, fmt).date()
        except ValueError:
            pass
    return None


def parse_work_report(subject: str, sender_fallback: str = ""):
    """Return (date, employee_name) or None.

    Employee name is taken from the subject (third segment after the date).
    If the subject has no name segment, sender_fallback (From display name) is used.
    """
    m = _WORK_RE.match(subject.strip())
    if not m:
        # Subject may omit the name: "Daily Work Report_10 Jun 2026"
        # Try a looser pattern that only requires the date segment.
        loose = re.match(
            r"daily\s+work\s+report[_\s]+(\d{1,2}[_\s]\w+[_\s]\d{4})\s*$",
            subject.strip(),
            re.IGNORECASE,
        )
        if loose:
            date = _parse_date_str(loose.group(1))
            if date and sender_fallback:
                return date, sender_fallback
        return None
    date = _parse_date_str(m.group(1))
    if not date:
        return None
    name = m.group(2).strip() or sender_fallback
    return date, name


def parse_leave(subject: str, sender_fallback: str = ""):
    """Return (date, employee_name, leave_type) where leave_type is 'full' or 'half', or None."""
    m = _LEAVE_RE.match(subject.strip())
    if not m:
        return None
    employee = m.group(1).strip() or sender_fallback
    try:
        date = datetime.strptime(m.group(2), "%d-%m-%Y").date()
    except ValueError:
        return None
    leave_type = "half" if "half" in m.group(3).lower() else "full"
    return date, employee, leave_type


def parse_mom(subject: str):
    """Return date parsed from MOM subject, or None.

    Handles: 'Minutes of Meeting | Client | Employee | 05 June 2026'
    Employee is ignored here — callers use the FROM email address instead.
    """
    m = _MOM_RE.search(subject.strip())
    if not m:
        return None
    date_str = m.group(1).strip()
    for fmt in ("%d %B %Y", "%d %b %Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            pass
    return None


def parse_work_report_rows(html_body: str) -> list:
    """Extract all data rows from a work-report HTML table.

    Expected columns (detected dynamically): SI No | Project | Task | Status | Remarks | Hours
    Returns list of dicts: {project, task, description, hours}
    """
    if not html_body:
        return []

    parser = _TableParser()
    try:
        parser.feed(html_body)
    except Exception:
        return []

    rows_out = []
    for table in parser.tables:
        col_map = {}
        header_idx = None
        for i, row in enumerate(table):
            found_any = False
            for j, cell in enumerate(row):
                text = _clean_cell(cell).lower()
                if 'project' in text and 'project' not in col_map:
                    col_map['project'] = j; found_any = True
                elif 'task' in text and 'task' not in col_map:
                    col_map['task'] = j; found_any = True
                elif ('hour' in text or 'horus' in text or 'time' in text) and 'hours' not in col_map:
                    col_map['hours'] = j; found_any = True
                elif ('remark' in text or 'description' in text) and 'description' not in col_map:
                    col_map['description'] = j; found_any = True
                elif 'status' in text and 'status' not in col_map:
                    col_map['status'] = j; found_any = True
            if found_any:
                header_idx = i
                break

        if not col_map or header_idx is None:
            continue

        for row in table[header_idx + 1:]:
            def _get(key, _row=row):
                idx = col_map.get(key)
                if idx is not None and idx < len(_row):
                    return _clean_cell(_row[idx])
                return ''

            project = _get('project')
            task    = _get('task')
            if not project and not task:
                continue

            hours_raw = _get('hours')
            try:
                hours = float(re.sub(r'[^\d.]', '', hours_raw)) if hours_raw else 0.0
            except (ValueError, TypeError):
                hours = 0.0

            # Use Remarks column if available, fall back to Status
            description = _get('description') or _get('status')

            rows_out.append({
                'project':     project,
                'task':        task,
                'description': description,
                'hours':       hours,
            })

    return rows_out


def has_meeting_task(html_body: str) -> bool:
    """Return True if any Task-column cell in the work-report HTML contains 'meeting'."""
    if not html_body:
        return False
    parser = _TableParser()
    try:
        parser.feed(html_body)
    except Exception:
        return False
    for table in parser.tables:
        task_col = None
        header_idx = None
        for i, row in enumerate(table):
            for j, cell in enumerate(row):
                if "task" in _clean_cell(cell).lower():
                    task_col = j
                    header_idx = i
                    break
            if task_col is not None:
                break
        if task_col is None:
            continue
        for row in table[header_idx + 1:]:
            if task_col < len(row):
                if "meeting" in _clean_cell(row[task_col]).lower():
                    return True
    return False

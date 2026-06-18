import base64
import calendar
import logging
import re
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)

from django.conf import settings
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import GmailCredential, Project
from .parsers import has_meeting_task, parse_leave, parse_mom, parse_work_report, parse_work_report_rows
from .serializers import ProjectSerializer

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def _client_config():
    return {
        "web": {
            "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["postmessage"],
        }
    }


def _build_service(cred_obj: GmailCredential):
    """Build an authenticated Gmail API service, refreshing token if needed."""
    creds = Credentials(
        token=cred_obj.access_token,
        refresh_token=cred_obj.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.GOOGLE_OAUTH_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )
    if creds.expired or not creds.valid:
        creds.refresh(Request())
        cred_obj.access_token = creds.token
        if creds.expiry:
            cred_obj.token_expiry = creds.expiry.replace(tzinfo=timezone.utc)
        cred_obj.save(update_fields=["access_token", "token_expiry"])
    return build("gmail", "v1", credentials=creds)


class GmailConnectView(APIView):
    """POST {code} → exchange for tokens → store GmailCredential."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"detail": "Missing code."}, status=status.HTTP_400_BAD_REQUEST)

        if not settings.GOOGLE_CLIENT_SECRET:
            return Response(
                {"detail": "GOOGLE_CLIENT_SECRET not configured on the server."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        flow = Flow.from_client_config(
            _client_config(),
            scopes=SCOPES,
            redirect_uri="postmessage",
        )
        flow.fetch_token(code=code)
        creds = flow.credentials

        # Get the Gmail address this token belongs to.
        service = build("gmail", "v1", credentials=creds)
        profile = service.users().getProfile(userId="me").execute()
        gmail_email = profile.get("emailAddress", "")

        expiry = None
        if creds.expiry:
            expiry = creds.expiry.replace(tzinfo=timezone.utc)

        GmailCredential.objects.update_or_create(
            user=request.user,
            defaults={
                "gmail_email": gmail_email,
                "access_token": creds.token,
                "refresh_token": creds.refresh_token or "",
                "token_expiry": expiry,
            },
        )
        return Response({"gmail_email": gmail_email})


class GmailStatusView(APIView):
    """GET → returns whether Gmail is connected for this user."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cred = request.user.gmail_credential
            return Response({"connected": True, "gmail_email": cred.gmail_email})
        except GmailCredential.DoesNotExist:
            return Response({"connected": False, "gmail_email": None})

    def delete(self, request):
        GmailCredential.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class GmailSyncView(APIView):
    """GET → all months grouped.  GET ?month=YYYY-MM → single month."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        month_str = request.query_params.get("month", "")

        try:
            cred_obj = request.user.gmail_credential
        except GmailCredential.DoesNotExist:
            return Response({"detail": "Gmail not connected."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            service  = _build_service(cred_obj)
            messages = (
                self._fetch_month(service, *map(int, month_str.split("-")))
                if month_str else
                self._fetch_all(service)
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        # Parse every message and bucket into (year, month) groups
        month_reports: dict = {}   # (y,m) -> emp -> set[int day]
        month_leaves:  dict = {}   # (y,m) -> emp -> {int day: str type}

        for msg in messages:
            try:
                subject = self._get_subject(msg)
                if not subject:
                    continue
                sender = self._sender_display_name(msg)

                parsed = parse_work_report(subject, sender_fallback=sender)
                if parsed:
                    date, _ = parsed
                    emp = _emp_name(msg)
                    if emp:
                        key = (date.year, date.month)
                        month_reports.setdefault(key, {}).setdefault(emp, set()).add(date.day)
                    continue

                parsed = parse_leave(subject, sender_fallback=sender)
                if parsed:
                    date, _, leave_type = parsed
                    emp = _emp_name(msg)
                    if emp:
                        key = (date.year, date.month)
                        month_leaves.setdefault(key, {}).setdefault(emp, {})[date.day] = leave_type
            except Exception as exc:
                logger.warning("Skipped malformed message %s: %s", msg.get("id"), exc)
                continue

        all_keys = sorted(month_reports.keys() | month_leaves.keys(), reverse=True)

        def _build(y, m):
            _, days_in = calendar.monthrange(y, m)
            data = self._merge(month_reports.get((y, m), {}), month_leaves.get((y, m), {}))
            day_meta = [{"day": d, "weekend": datetime(y, m, d).weekday() >= 5}
                        for d in range(1, days_in + 1)]
            return {"employees": sorted(data.keys()), "day_meta": day_meta, "data": data}

        if month_str:
            try:
                y, m = map(int, month_str.split("-"))
            except ValueError:
                return Response({"detail": "month must be YYYY-MM."}, status=status.HTTP_400_BAD_REQUEST)
            entry = _build(y, m)
            entry["month"] = f"{y}-{m:02d}"
            return Response(entry)

        # All months — newest first
        months_out = []
        for (y, m) in all_keys:
            entry = _build(y, m)
            if entry["employees"]:
                entry["month"] = f"{y}-{m:02d}"
                months_out.append(entry)
        return Response({"months": months_out})

    # ── fetch helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _fetch_month(service, year: int, month: int) -> list:
        # ±14-day buffer around the calendar month so that late submissions
        # (e.g., a Jan 31 report filed on Feb 3) are still captured.
        # The backend groups messages by the date in the subject, so emails
        # from the buffer period that belong to a different month are
        # naturally bucketed into their own month, not this one.
        buf        = timedelta(days=14)
        month_start = datetime(year, month, 1)
        month_end   = datetime(year + 1, 1, 1) if month == 12 else datetime(year, month + 1, 1)
        after  = (month_start - buf).strftime("%Y/%m/%d")
        before = (month_end   + buf).strftime("%Y/%m/%d")
        work  = GmailSyncView._paginate(
            service, f'subject:Daily Work Report after:{after} before:{before}')
        leave = GmailSyncView._paginate(
            service, f'subject:"LEAVE REQUEST" after:{after} before:{before}')
        seen = {m['id'] for m in work}
        return work + [m for m in leave if m['id'] not in seen]

    @staticmethod
    def _fetch_all(service) -> list:
        # Limit to the current calendar year — at 40 emails/day this is
        # ~5 k messages vs ~30 k for a 2-year window, well within quota.
        after = f"{datetime.now().year}/01/01"
        work  = GmailSyncView._paginate(service, f'subject:Daily Work Report after:{after}')
        leave = GmailSyncView._paginate(service, f'subject:"LEAVE REQUEST" after:{after}')
        seen  = {m['id'] for m in work}
        return work + [m for m in leave if m['id'] not in seen]

    @staticmethod
    def _paginate(service, query: str) -> list:
        ids = _list_ids(service, query)
        return _batch_get_messages(service, ids,
                                   fmt="metadata",
                                   metadata_headers=["Subject", "From"])

    # ── merge helper ──────────────────────────────────────────────────────────

    @staticmethod
    def _merge(reports: dict, leaves: dict) -> dict:
        data = {}
        for emp in reports.keys() | leaves.keys():
            rep_days  = reports.get(emp, set())
            leave_map = leaves.get(emp, {})
            day_data  = {}
            for d in rep_days | leave_map.keys():
                has_rep   = d in rep_days
                leave_typ = leave_map.get(d)
                if has_rep and not leave_typ:
                    day_data[d] = "full"
                elif has_rep and leave_typ == "half":
                    day_data[d] = "half"
                elif leave_typ == "full":
                    day_data[d] = "leave_full"
                else:
                    day_data[d] = "leave_half"
            if day_data:
                data[emp] = day_data
        return data

    # ── header helpers (kept for backward compat) ─────────────────────────────

    def _fetch_messages(self, service, year: int, month: int) -> list:
        return self._fetch_month(service, year, month)

    @staticmethod
    def _get_header(msg: dict, name: str) -> str:

        headers = msg.get("payload", {}).get("headers", [])
        for h in headers:
            if h.get("name", "").lower() == name.lower():
                return h.get("value", "")
        return ""

    @staticmethod
    def _get_subject(msg: dict) -> str:
        return GmailSyncView._get_header(msg, "subject")

    @staticmethod
    def _sender_display_name(msg: dict) -> str:
        """Extract display name from From header, e.g. 'John Doe <john@example.com>' → 'John Doe'."""
        raw = GmailSyncView._get_header(msg, "from")
        if not raw:
            return ""
        # "Display Name <email>" → take the display name part
        if "<" in raw:
            name = raw[:raw.index("<")].strip().strip('"')
            return name if name else raw
        return raw.strip()


# ---------------------------------------------------------------------------
# Shared helpers used by WorkDayCountView
# ---------------------------------------------------------------------------

def _msg_header(msg: dict, name: str) -> str:
    for h in msg.get("payload", {}).get("headers", []):
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _msg_sender(msg: dict) -> str:
    raw = _msg_header(msg, "from")
    if not raw:
        return ""
    if "<" in raw:
        name = raw[:raw.index("<")].strip().strip('"')
        return name if name else raw
    return raw.strip()


def _msg_body(msg: dict) -> str:
    """Recursively extract the first text/plain part from the message payload."""
    def _extract(part):
        if part.get("mimeType") == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
        for sub in part.get("parts", []):
            text = _extract(sub)
            if text:
                return text
        return ""
    return _extract(msg.get("payload", {}))


def _msg_html_body(msg: dict) -> str:
    """Recursively extract the first text/html part from the message payload."""
    def _extract(part):
        if part.get("mimeType") == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="ignore")
        for sub in part.get("parts", []):
            text = _extract(sub)
            if text:
                return text
        return ""
    return _extract(msg.get("payload", {}))


_EMAIL_RE = re.compile(r"[\w.+\-]+@[\w.\-]+\.\w+")


def _extract_emails(header_val: str) -> set:
    """Return lowercase email addresses found in a To/Cc header string."""
    return {m.lower() for m in _EMAIL_RE.findall(header_val)}


def _msg_from_email_local(msg: dict) -> str:
    """Return the local part of the From address, e.g. 'muflih' from 'muflih@cybrosys.com'."""
    raw = _msg_header(msg, "from")
    m = _EMAIL_RE.search(raw)
    return m.group(0).split("@")[0] if m else ""


def _emp_name(msg: dict) -> str:
    """Return employee name from the From email local part, capitalized.
    e.g. muflih@cybrosys.com → 'Muflih'
    """
    local = _msg_from_email_local(msg)
    return local.capitalize() if local else ""


# ---------------------------------------------------------------------------
# Batch-fetch helpers — replaces N sequential .get() calls with ceil(N/100)
# batch calls, which is dramatically faster for large inboxes.
# ---------------------------------------------------------------------------

_BATCH_SIZE = 100   # Gmail API hard limit per batch request


def _list_ids(service, query: str) -> list:
    """Return all message IDs matching a Gmail search query."""
    ids, page_token = [], None
    while True:
        kwargs = {"userId": "me", "q": query, "maxResults": 500}
        if page_token:
            kwargs["pageToken"] = page_token
        result = service.users().messages().list(**kwargs).execute()
        ids.extend(m["id"] for m in result.get("messages", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return ids


def _batch_get_messages(service, ids, fmt="metadata", metadata_headers=None):
    """Fetch messages in batches of 100 using the Gmail batch endpoint.

    For N messages this issues ceil(N/100) HTTP requests instead of N,
    which eliminates the per-message latency that causes timeouts on large
    inboxes.
    """
    if not ids:
        return []

    results = {}

    def _cb(mid):
        def callback(request_id, response, exception):
            if exception is None and response:
                results[mid] = response
        return callback

    for i in range(0, len(ids), _BATCH_SIZE):
        chunk = ids[i : i + _BATCH_SIZE]
        batch = service.new_batch_http_request()
        for mid in chunk:
            kwargs = {"userId": "me", "id": mid, "format": fmt}
            if fmt == "metadata" and metadata_headers:
                kwargs["metadataHeaders"] = metadata_headers
            batch.add(service.users().messages().get(**kwargs), callback=_cb(mid))
        batch.execute()

    # Return in original order; silently drop any IDs that had errors
    return [results[mid] for mid in ids if mid in results]


class WorkDayCountView(APIView):
    """GET ?start=YYYY-MM-DD&end=YYYY-MM-DD&project=NAME&employee=NAME
    Count work-report emails for an employee whose To/Cc headers include
    at least one email address belonging to the selected project.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_str       = request.query_params.get("start", "")
        end_str         = request.query_params.get("end", "")
        project_filter  = request.query_params.get("project",  "")
        employee_filter = request.query_params.get("employee", "")

        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date   = datetime.strptime(end_str,   "%Y-%m-%d").date()
        except ValueError:
            return Response(
                {"detail": "start and end must be YYYY-MM-DD."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if start_date > end_date:
            return Response(
                {"detail": "start must be before end."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            cred_obj = request.user.gmail_credential
        except GmailCredential.DoesNotExist:
            return Response({"detail": "Gmail not connected."}, status=status.HTTP_400_BAD_REQUEST)

        # Resolve project emails from the Projects table
        project_emails: set = set()
        if project_filter:
            try:
                proj = Project.objects.get(user=request.user, name=project_filter)
                project_emails = {e.lower() for e in proj.emails}
            except Project.DoesNotExist:
                pass

        try:
            service  = _build_service(cred_obj)
            messages = self._fetch_messages(service, start_date, end_date)
        except HttpError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        emp_counts: dict[str, int] = {}
        parsed_count = 0
        seen_subjects: set = set()   # deduplicate: (emp_lower, subject_lower)

        for msg in messages:
            subject = _msg_header(msg, "subject")
            if not subject:
                continue

            sender = _msg_sender(msg)
            parsed = parse_work_report(subject, sender_fallback=sender)
            if not parsed:
                continue

            date, _ = parsed
            emp = _emp_name(msg)

            if not (start_date <= date <= end_date):
                continue

            parsed_count += 1

            if not emp:
                continue

            # Employee filter (case-insensitive)
            if employee_filter and emp.lower() != employee_filter.lower():
                continue

            # Project filter — To/Cc must contain at least one project email
            if project_emails:
                to_cc = _msg_header(msg, "to") + " " + _msg_header(msg, "cc")
                if not (project_emails & _extract_emails(to_cc)):
                    continue

            # Deduplicate: same employee + same subject = same work report, count once
            dedup_key = (emp.lower(), subject.strip().lower())
            if dedup_key in seen_subjects:
                continue
            seen_subjects.add(dedup_key)

            emp_counts[emp] = emp_counts.get(emp, 0) + 1

        rows = [{"employee": emp, "count": cnt} for emp, cnt in sorted(emp_counts.items())]

        return Response({
            "employees":     sorted(emp_counts.keys()),
            "rows":          rows,
            "emails_found":  len(messages),
            "emails_parsed": parsed_count,
        })

    @staticmethod
    def _fetch_messages(service, start_date, end_date) -> list:
        # Gmail after:/before: filter by receive date. 14-day buffer on each
        # side catches work reports submitted a few days late.
        buf    = timedelta(days=14)
        after  = (start_date - buf).strftime("%Y/%m/%d")
        before = (end_date   + buf).strftime("%Y/%m/%d")
        ids = _list_ids(service, f'subject:Daily Work Report after:{after} before:{before}')
        return _batch_get_messages(service, ids,
                                   fmt="metadata",
                                   metadata_headers=["Subject", "From", "To", "Cc"])


# ---------------------------------------------------------------------------
# Employees list (fast metadata-only fetch for current month)
# ---------------------------------------------------------------------------

class EmployeesListView(APIView):
    """GET → distinct employee names (email local parts) from all work-report emails."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cred_obj = request.user.gmail_credential
        except GmailCredential.DoesNotExist:
            return Response({"employees": []})

        query = 'subject:Daily Work Report'

        service = _build_service(cred_obj)
        msgs    = _batch_get_messages(
            service,
            _list_ids(service, query),
            fmt="metadata",
            metadata_headers=["Subject", "From"],
        )
        employees = set()
        for msg in msgs:
            subject = _msg_header(msg, "subject")
            sender  = _msg_sender(msg)
            parsed  = parse_work_report(subject, sender_fallback=sender)
            if parsed:
                emp = _emp_name(msg)
                if emp:
                    employees.add(emp)

        return Response({"employees": sorted(employees)})


# ---------------------------------------------------------------------------
# MOM Dashboard  (stub — data logic added when email format is confirmed)
# ---------------------------------------------------------------------------

class MomSyncView(APIView):
    """GET → months grouped for the MOM Dashboard.

    Logic:
    - For each employee, find work-report days where the Task column contains "meeting".
    - If they also sent a MOM email (subject: Minutes of Meeting …) on that date → present.
    - If they had a meeting task but sent no MOM → absent.
    - Days with no meeting task are omitted (shown as – in the frontend).
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        month_str = request.query_params.get("month", "")

        try:
            cred_obj = request.user.gmail_credential
        except GmailCredential.DoesNotExist:
            return Response({"detail": "Gmail not connected."}, status=status.HTTP_400_BAD_REQUEST)

        # Build Gmail date filters
        if month_str:
            try:
                ym_y, ym_m = map(int, month_str.split("-"))
            except ValueError:
                return Response({"detail": "month must be YYYY-MM."}, status=status.HTTP_400_BAD_REQUEST)
            after  = f"{ym_y}/{ym_m:02d}/01"
            bm     = ym_m % 12 + 1
            by_    = ym_y + 1 if ym_m == 12 else ym_y
            before = f"{by_}/{bm:02d}/01"
            work_q = f'subject:Daily Work Report after:{after} before:{before}'
            mom_q  = f'subject:"Minutes of Meeting" after:{after} before:{before}'
        else:
            after  = (datetime.now() - timedelta(days=730)).strftime("%Y/%m/%d")
            work_q = f'subject:Daily Work Report after:{after}'
            mom_q  = f'subject:"Minutes of Meeting" after:{after}'

        try:
            service   = _build_service(cred_obj)
            work_msgs = self._fetch_full(service, work_q)
            mom_msgs  = self._fetch_meta(service, mom_q)
        except HttpError as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        # emp -> (y, m) -> set[day]  — days where work report had a meeting task
        meeting_days: dict = {}
        for msg in work_msgs:
            try:
                subject = _msg_header(msg, "subject")
                if not subject:
                    continue
                sender = _msg_sender(msg)
                parsed = parse_work_report(subject, sender_fallback=sender)
                if not parsed:
                    continue
                date, _ = parsed
                emp = _emp_name(msg)
                if not emp:
                    continue
                if not has_meeting_task(_msg_html_body(msg)):
                    continue
                key = (date.year, date.month)
                meeting_days.setdefault(emp, {}).setdefault(key, set()).add(date.day)
            except Exception as exc:
                logger.warning("Skipped malformed work-report message %s: %s", msg.get("id"), exc)
                continue

        # emp -> (y, m) -> set[day]  — days where employee sent a MOM email
        mom_days: dict = {}
        for msg in mom_msgs:
            try:
                subject = _msg_header(msg, "subject")
                if not subject:
                    continue
                date = parse_mom(subject)
                if not date:
                    continue
                emp = _emp_name(msg)
                if not emp:
                    continue
                key = (date.year, date.month)
                mom_days.setdefault(emp, {}).setdefault(key, set()).add(date.day)
            except Exception as exc:
                logger.warning("Skipped malformed MOM message %s: %s", msg.get("id"), exc)
                continue

        def _build(y, m):
            emps = [emp for emp, ed in meeting_days.items() if (y, m) in ed]
            data = {}
            for emp in emps:
                meet_set = meeting_days[emp].get((y, m), set())
                mom_set  = mom_days.get(emp, {}).get((y, m), set())
                day_data = {d: ("present" if d in mom_set else "absent") for d in meet_set}
                if day_data:
                    data[emp] = day_data
            _, days_in = calendar.monthrange(y, m)
            day_meta = [{"day": d, "weekend": datetime(y, m, d).weekday() >= 5}
                        for d in range(1, days_in + 1)]
            return {
                "month":     f"{y}-{m:02d}",
                "employees": sorted(data.keys()),
                "day_meta":  day_meta,
                "data":      data,
            }

        if month_str:
            return Response(_build(ym_y, ym_m))

        all_keys = sorted(
            set().union(*(ed.keys() for ed in meeting_days.values())) if meeting_days else set(),
            reverse=True,
        )
        months_out = []
        for (y, m) in all_keys:
            entry = _build(y, m)
            if entry["employees"]:
                months_out.append(entry)
        return Response({"months": months_out})

    @staticmethod
    def _fetch_full(service, query: str) -> list:
        """Fetch messages with full body (needed to inspect task cell content)."""
        ids = _list_ids(service, query)
        return _batch_get_messages(service, ids, fmt="full")

    @staticmethod
    def _fetch_meta(service, query: str) -> list:
        """Fetch messages with metadata only (subject + from headers)."""
        ids = _list_ids(service, query)
        return _batch_get_messages(service, ids,
                                   fmt="metadata",
                                   metadata_headers=["Subject", "From"])


# ---------------------------------------------------------------------------
# Project CRUD
# ---------------------------------------------------------------------------

class ProjectListCreateView(APIView):
    """GET → list all projects.  POST {name, emails} → create."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        projects = Project.objects.filter(user=request.user)
        return Response(ProjectSerializer(projects, many=True).data)

    def post(self, request):
        serializer = ProjectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProjectDetailView(APIView):
    """PUT {name, emails} → update.  DELETE → remove."""
    permission_classes = [IsAuthenticated]

    def _get_obj(self, request, pk):
        try:
            return Project.objects.get(pk=pk, user=request.user)
        except Project.DoesNotExist:
            return None

    def put(self, request, pk):
        obj = self._get_obj(request, pk)
        if not obj:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        s = ProjectSerializer(obj, data=request.data)
        s.is_valid(raise_exception=True)
        s.save()
        return Response(s.data)

    def delete(self, request, pk):
        obj = self._get_obj(request, pk)
        if not obj:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ---------------------------------------------------------------------------
# AI Analysis — compare Gmail work-report emails vs Odoo timesheet entries
# ---------------------------------------------------------------------------

class AIAnalyzeView(APIView):
    """POST {employee_local, start, end, odoo_entries} →
    Fetch Gmail work-report emails for that employee in the date range,
    parse task/hours rows from each email body, then call Claude Haiku
    to compare against the provided Odoo timesheet entries.
    Returns {"sections": {"rows": [...], "summary": "..."}}
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        employee_local = (request.data.get("employee_local") or "").strip().lower()
        start_str      = (request.data.get("start") or "").strip()
        end_str        = (request.data.get("end")   or "").strip()
        odoo_entries   = request.data.get("odoo_entries") or []

        # --- validate input ---------------------------------------------------
        if not employee_local:
            return Response({"detail": "employee_local is required."}, status=status.HTTP_400_BAD_REQUEST)
        if not odoo_entries or not isinstance(odoo_entries, list):
            return Response({"detail": "odoo_entries must be a non-empty list."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            start_date = datetime.strptime(start_str, "%Y-%m-%d").date()
            end_date   = datetime.strptime(end_str,   "%Y-%m-%d").date()
        except ValueError:
            return Response({"detail": "start and end must be YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        # --- check API key ----------------------------------------------------
        api_key = settings.ANTHROPIC_API_KEY
        if not api_key:
            return Response(
                {"detail": "AI API key not configured. Set ANTHROPIC_API_KEY in .env."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        # --- check Gmail credential -------------------------------------------
        try:
            cred_obj = request.user.gmail_credential
        except GmailCredential.DoesNotExist:
            return Response({"detail": "Gmail not connected."}, status=status.HTTP_400_BAD_REQUEST)

        # --- fetch Gmail emails (two-phase: metadata → filter → full body) ------
        try:
            service = _build_service(cred_obj)
            buf    = timedelta(days=14)
            after  = (start_date - buf).strftime("%Y/%m/%d")
            before = (end_date   + buf).strftime("%Y/%m/%d")
            all_ids = _list_ids(service, f'subject:Daily Work Report after:{after} before:{before}')

            # Phase 1: metadata only — cheap, no body download
            meta_msgs = _batch_get_messages(
                service, all_ids, fmt="metadata",
                metadata_headers=["From", "Subject"],
            )

            # Filter to only this employee's message IDs before fetching bodies
            matched_ids = []
            for m in meta_msgs:
                from_local   = _msg_from_email_local(m).lower()
                display_name = _msg_sender(m).lower()
                if (
                    from_local == employee_local
                    or display_name == employee_local
                    or display_name.startswith(employee_local + " ")
                    or display_name.startswith(employee_local + ".")
                ):
                    matched_ids.append(m["id"])

            # Phase 2: full body only for matching emails
            msgs = _batch_get_messages(service, matched_ids, fmt="full") if matched_ids else []
        except HttpError as e:
            return Response({"detail": f"Gmail error: {e}"}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({"detail": f"Gmail error: {e}"}, status=status.HTTP_502_BAD_GATEWAY)

        # --- parse email rows -------------------------------------------------
        email_rows = []   # [{date, project, task, description, hours}]
        total_msgs_found = len(all_ids)
        matched_msgs = 0

        for msg in msgs:
            subject = _msg_header(msg, "subject")
            if not subject:
                continue
            sender = _msg_sender(msg)
            parsed = parse_work_report(subject, sender_fallback=sender)
            if not parsed:
                continue
            date, _ = parsed
            if not (start_date <= date <= end_date):
                continue

            matched_msgs += 1
            rows = parse_work_report_rows(_msg_html_body(msg))
            for r in rows:
                email_rows.append({**r, "date": date.isoformat()})

        if not email_rows:
            if total_msgs_found == 0:
                detail = (
                    f"No work-report emails found in Gmail for the date range "
                    f"{start_str} to {end_str}. Check that Gmail is synced."
                )
            elif matched_msgs == 0:
                detail = (
                    f"Found {total_msgs_found} work-report email(s) in the date range but none "
                    f"matched '{employee_local}'. The employee's Gmail address may not start with "
                    f"'{employee_local}'."
                )
            else:
                detail = (
                    f"Found {matched_msgs} email(s) from {employee_local} but could not parse "
                    "task rows from the email body. The work-report table format may differ."
                )
            return Response({"sections": {"rows": [], "summary": detail}})

        # --- build prompt -----------------------------------------------------
        odoo_cap   = odoo_entries[:100]
        email_cap  = email_rows[:100]
        odoo_total = round(sum(float(e.get("hours") or 0) for e in odoo_cap), 2)

        odoo_lines  = "\n".join(
            f"  {e.get('date','')} | {e.get('project','')} | {e.get('task','')} | "
            f"{e.get('hours',0)}h | {e.get('description','')}"
            for e in odoo_cap
        )
        email_lines = "\n".join(
            f"  {r['date']} | {r['project']} | {r['task']} | "
            f"{r['hours']}h | {r['description']}"
            for r in email_cap
        )

        prompt = (
            f"Employee: {employee_local}   Period: {start_str} to {end_str}\n\n"
            f"=== ODOO TIMESHEET ({len(odoo_cap)} entries, total {odoo_total}h) ===\n"
            f"  Date | Project | Task | Hours | Description\n"
            f"{odoo_lines}\n\n"
            f"=== GMAIL WORK-REPORT EMAILS ({len(email_cap)} rows across {matched_msgs} emails) ===\n"
            f"  Date | Project | Task | Hours mentioned | Remarks\n"
            f"{email_lines}\n\n"
            "For each Odoo entry, find the best matching Gmail row and classify it.\n"
            "Return ONLY a JSON object (no markdown, no preamble) with this exact shape:\n"
            "{\n"
            '  "rows": [\n'
            '    {\n'
            '      "date": "YYYY-MM-DD",\n'
            '      "task": "task name from Odoo",\n'
            '      "description": "description from Odoo",\n'
            '      "time": "Xh",\n'
            '      "status": one of ["matching_all", "matching_task", "matching_hours", "not_matching"],\n'
            '      "comparison": "2-3 sentences comparing this Odoo entry against the Gmail row: task name match, hours alignment, any description difference. Be specific and factual."\n'
            '    }\n'
            '  ],\n'
            '  "summary": "one sentence overall assessment"\n'
            "}\n\n"
            "Status rules:\n"
            "  matching_all    = task name, description AND hours all closely match a Gmail row\n"
            "  matching_task   = task name matches but hours or description differ significantly\n"
            "  matching_hours  = hours match but task name differs\n"
            "  not_matching    = no Gmail row matches this Odoo entry at all\n"
            "Be factual. Do not fabricate details not in the data."
        )

        # --- call Claude Haiku ------------------------------------------------
        try:
            import anthropic
            import json as _json
            client = anthropic.Anthropic(api_key=api_key)
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=min(4096, max(1200, len(odoo_cap) * 300 + 500)),
                system=(
                    "You are an HR analyst. Compare Odoo timesheet entries against Gmail "
                    "work-report emails row by row. Return ONLY valid JSON — no markdown fences, "
                    "no preamble, no extra text outside the JSON object."
                ),
                messages=[{"role": "user", "content": prompt}],
            )
            raw = message.content[0].text.strip()
            # Strip markdown fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
                raw = raw.rsplit("```", 1)[0].strip()
            # Extract outermost {...} block to handle any leading/trailing text
            import re as _re
            brace_match = _re.search(r'\{.*\}', raw, _re.DOTALL)
            if brace_match:
                raw = brace_match.group(0)
            try:
                sections = _json.loads(raw)
            except _json.JSONDecodeError:
                sections = {"rows": [], "summary": "Analysis could not be parsed. Please try again."}
            analysis = sections
        except anthropic.AuthenticationError:
            return Response(
                {"detail": "AI API key is invalid. Check ANTHROPIC_API_KEY in .env."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except anthropic.RateLimitError:
            return Response(
                {"detail": "AI rate limit reached. Please try again shortly."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )
        except Exception as e:
            return Response(
                {"detail": f"AI error: {e}"},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response({"sections": analysis})

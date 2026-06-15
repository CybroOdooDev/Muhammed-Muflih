import calendar
import socket
import xmlrpc.client
from datetime import date as date_cls

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import OdooCredential


def _authenticate(url: str, db: str, login: str, api_key: str) -> int:
    """Return uid on success, raise on failure."""
    common = xmlrpc.client.ServerProxy(f"{url.rstrip('/')}/xmlrpc/2/common")
    uid = common.authenticate(db, login, api_key, {})
    if not uid:
        raise ValueError("Authentication failed — check URL, database, login, and API key.")
    return uid


class OdooStatusView(APIView):
    """GET → connection state.  DELETE → disconnect."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cred = request.user.odoo_credential
            return Response({
                "connected": True,
                "url":   cred.url,
                "db":    cred.db,
                "login": cred.login,
            })
        except OdooCredential.DoesNotExist:
            return Response({"connected": False})

    def delete(self, request):
        OdooCredential.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class OdooConnectView(APIView):
    """POST {url, db, login, api_key} → verify & store credentials."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        url     = (request.data.get("url")     or "").strip().rstrip("/")
        db      = (request.data.get("db")      or "").strip()
        login   = (request.data.get("login")   or "").strip()
        api_key = (request.data.get("api_key") or "").strip()

        if not all([url, db, login, api_key]):
            return Response(
                {"detail": "url, db, login, and api_key are all required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            _authenticate(url, db, login, api_key)
        except (ValueError, xmlrpc.client.Fault) as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except (socket.gaierror, ConnectionRefusedError, OSError) as e:
            return Response(
                {"detail": f"Could not reach Odoo server: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        OdooCredential.objects.update_or_create(
            user=request.user,
            defaults={"url": url, "db": db, "login": login, "api_key": api_key},
        )
        return Response({"connected": True})


class OdooScrumView(APIView):
    """GET → sprint list from Odoo Scrum module."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            cred = request.user.odoo_credential
        except OdooCredential.DoesNotExist:
            return Response(
                {"detail": "Odoo not connected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            uid = _authenticate(cred.url, cred.db, cred.login, cred.api_key)
            models = xmlrpc.client.ServerProxy(
                f"{cred.url.rstrip('/')}/xmlrpc/2/object"
            )
            sprints = models.execute_kw(
                cred.db, uid, cred.api_key,
                "project.scrum.sprint",
                "search_read",
                [[]],
                {
                    "fields": ["name", "date_start", "date_stop", "state", "description"],
                    "order":  "date_start desc",
                    "limit":  200,
                },
            )
        except xmlrpc.client.Fault as e:
            return Response(
                {"detail": f"Odoo model error: {e.faultString}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except (ValueError, socket.gaierror, ConnectionRefusedError, OSError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        return Response({"sprints": sprints})


class OdooInspectView(APIView):
    """GET ?model=<model_name> → return all x_ fields + a sample record (debug)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        model = request.query_params.get('model', 'x_daily_tasks_line_7390c')
        try:
            cred = request.user.odoo_credential
        except OdooCredential.DoesNotExist:
            return Response({"detail": "Odoo not connected."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            uid = _authenticate(cred.url, cred.db, cred.login, cred.api_key)
            mdl = xmlrpc.client.ServerProxy(f"{cred.url.rstrip('/')}/xmlrpc/2/object")
            fields_meta = mdl.execute_kw(
                cred.db, uid, cred.api_key, model, 'fields_get', [],
                {'attributes': ['type', 'string', 'store', 'relation']},
            )
            x_fields = {f: v for f, v in fields_meta.items() if f.startswith('x_')}
            sample_ids = mdl.execute_kw(cred.db, uid, cred.api_key, model, 'search', [[]], {'limit': 1})
            sample = mdl.execute_kw(cred.db, uid, cred.api_key, model, 'read',
                                    [sample_ids], {'fields': list(x_fields.keys())}) if sample_ids else []
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"model": model, "x_fields": x_fields, "sample": sample})


class OdooDailyTaskView(APIView):
    """GET ?month=YYYY-MM → per-employee daily task ticks from Odoo Scrum."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        month_str = request.query_params.get('month', '')
        if not month_str:
            from datetime import datetime
            now = datetime.now()
            month_str = f"{now.year}-{now.month:02d}"

        try:
            parts = month_str.split('-')
            y, m = int(parts[0]), int(parts[1])
            if not (1 <= m <= 12):
                raise ValueError
        except (ValueError, AttributeError, IndexError):
            return Response(
                {"detail": "month must be YYYY-MM."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        month_start = f"{y}-{m:02d}-01"
        month_end   = f"{y + 1}-01-01" if m == 12 else f"{y}-{m + 1:02d}-01"

        try:
            cred = request.user.odoo_credential
        except OdooCredential.DoesNotExist:
            return Response(
                {"detail": "Odoo not connected."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        HEADER_MODEL = 'x_daily_tasks'
        LINE_MODEL   = 'x_daily_tasks_line_7390c'

        try:
            uid    = _authenticate(cred.url, cred.db, cred.login, cred.api_key)
            mdl    = xmlrpc.client.ServerProxy(f"{cred.url.rstrip('/')}/xmlrpc/2/object")

            def kw(model, method, domain, kwargs):
                return mdl.execute_kw(cred.db, uid, cred.api_key, model, method, domain, kwargs)

            # ── Discover header fields ────────────────────────────────────
            hf = kw(HEADER_MODEL, 'fields_get', [], {'attributes': ['type', 'relation', 'store']})

            # Only pick stored date fields (skip computed ones like activity_date_deadline)
            date_field = next(
                (f for f, v in hf.items()
                 if v['type'] == 'date' and v.get('store', False) and f.startswith('x_')),
                None,
            ) or next(
                (f for f, v in hf.items()
                 if v['type'] == 'date' and v.get('store', False)),
                'x_date',
            )
            line_o2m = next(
                (f for f, v in hf.items()
                 if v['type'] == 'one2many' and v.get('relation') == LINE_MODEL),
                None,
            ) or next(
                (f for f, v in hf.items() if v['type'] == 'one2many'),
                None,
            )
            if not line_o2m:
                return Response(
                    {"detail": f"Could not find one2many field on {HEADER_MODEL}. Fields: {list(hf.keys())}"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # ── Discover line fields ──────────────────────────────────────
            # Include 'string' so we can match by LABEL as well as field name —
            # Odoo Studio auto-generates names like x_studio_boolean_c that don't
            # contain keywords like "week", but their string label does.
            lf = kw(LINE_MODEL, 'fields_get', [], {'attributes': ['type', 'relation', 'store', 'string']})

            def _lbl(v):
                return v.get('string', '').lower()

            # All x_* many2one fields that don't link back to the parent header model.
            # We'll detect the employee per-record by value rather than by field name,
            # avoiding fragile metadata-based detection that fails on Studio auto-names.
            x_m2o_cands = sorted(
                f for f, v in lf.items()
                if v['type'] == 'many2one'
                and f.startswith('x_')
                and v.get('relation', '') != HEADER_MODEL
            )

            wr_field = next(
                (f for f, v in lf.items()
                 if v['type'] == 'boolean'
                 and ('work' in f.lower() or 'work' in _lbl(v))),
                None,
            )
            ts_field = next(
                (f for f, v in lf.items()
                 if v['type'] == 'boolean'
                 and ('time' in f.lower() or 'time' in _lbl(v))),
                None,
            )
            wk_field = next(
                (f for f, v in lf.items()
                 if v['type'] == 'boolean'
                 and ('week' in f.lower() or 'week' in _lbl(v))),
                None,
            )
            commit_field = next(
                (f for f, v in lf.items()
                 if 'commit' in f.lower() or 'commit' in _lbl(v)),
                None,
            )

            line_fetch_fields = list(dict.fromkeys(
                x_m2o_cands
                + ([wr_field]     if wr_field     else [])
                + ([ts_field]     if ts_field     else [])
                + ([wk_field]     if wk_field     else [])
                + ([commit_field] if commit_field else [])
                + ['x_name']
            ))

            # ── Fetch header records for the month ───────────────────────
            tasks = kw(
                HEADER_MODEL, 'search_read',
                [[
                    [date_field, '>=', month_start],
                    [date_field, '<',  month_end],
                ]],
                {'fields': [date_field, line_o2m], 'order': f'{date_field} asc'},
            )

            # ── Fetch all line items in one call ─────────────────────────
            all_line_ids = [lid for t in tasks for lid in (t.get(line_o2m) or [])]
            lines = []
            if all_line_ids:
                lines = kw(
                    LINE_MODEL, 'read',
                    [all_line_ids],
                    {'fields': line_fetch_fields},
                )

        except xmlrpc.client.Fault as e:
            return Response(
                {"detail": f"Odoo error: {e.faultString}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except (ValueError, socket.gaierror, ConnectionRefusedError, OSError) as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_502_BAD_GATEWAY)

        line_by_id = {ln['id']: ln for ln in lines}

        days_in_month = calendar.monthrange(y, m)[1]
        day_meta = [
            {'day': d, 'weekend': date_cls(y, m, d).weekday() >= 5}
            for d in range(1, days_in_month + 1)
        ]

        emp_names_ordered = []
        emp_seen = set()
        data = {}

        for t in tasks:
            day_str = t.get(date_field, '')
            try:
                day_int = int(str(day_str).split('-')[2])
            except (IndexError, ValueError):
                continue
            for lid in (t.get(line_o2m) or []):
                ln = line_by_id.get(lid)
                if not ln:
                    continue
                # Detect employee name per-record: first x_ many2one that returns [id, name]
                emp_name = None
                for f in x_m2o_cands:
                    val = ln.get(f)
                    if (isinstance(val, (list, tuple))
                            and len(val) == 2
                            and isinstance(val[1], str)
                            and val[1]):
                        emp_name = val[1]
                        break
                if not emp_name:
                    emp_name = ln.get('x_name') or 'Unknown'
                if emp_name not in emp_seen:
                    emp_seen.add(emp_name)
                    emp_names_ordered.append(emp_name)
                    data[emp_name] = {}
                data[emp_name][day_int] = {
                    'work_report':   bool(ln.get(wr_field))   if wr_field     else False,
                    'timesheet':     bool(ln.get(ts_field))   if ts_field     else False,
                    'weekly_report': bool(ln.get(wk_field))   if wk_field     else False,
                    'commit_id':     ln.get(commit_field) or '' if commit_field else '',
                }

        return Response({
            'month':     month_str,
            'employees': sorted(emp_names_ordered),
            'day_meta':  day_meta,
            'data':      data,
        })

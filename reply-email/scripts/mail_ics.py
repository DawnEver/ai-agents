#!/usr/bin/env python3
"""Build an iCalendar (.ics) file from the `event.*` frontmatter keys.

Default output is a **personal appointment**: a bare `VEVENT` with no `METHOD` and no
`ORGANIZER`, so double-clicking it adds the event to the reader's own calendar and sends
nothing to anyone. Setting `event.method: request` upgrades it to a real meeting request.

Times are emitted in UTC with no `VTIMEZONE` block - a hand-rolled VTIMEZONE is where
calendar generators usually go wrong, and UTC is unambiguous without one.

Usage:
    from mail_ics import build_ics
    text, warnings = build_ics(event={"title": "Kick-off", ...}, slug="my-round", now=dt)
"""

from __future__ import annotations

import hashlib
import re
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from mail_frontmatter import split_addresses

PRODID = "-//mail-build//reply-email//EN"
DOMAIN = "local"  # deliberately neutral: the project this lives in may be renamed
FOLD_LIMIT = 75

_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
_DATETIME = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$")
_UTC_SUFFIX = re.compile(r"Z$", re.IGNORECASE)


class EventError(ValueError):
    """A problem that must stop the build rather than produce a wrong calendar entry."""


def escape_text(value: str) -> str:
    """Escape a TEXT value per RFC 5545. Colons are not special and stay as-is."""
    out = value.replace("\\", "\\\\")
    out = out.replace(";", "\\;").replace(",", "\\,")
    return out.replace("\r\n", "\\n").replace("\n", "\\n").replace("\r", "\\n")


def fold_line(line: str, limit: int = FOLD_LIMIT) -> list[str]:
    """Fold a content line at `limit` octets without splitting a multi-byte character.

    A naive character-count fold corrupts CJK and accented text; a naive byte slice can
    cut a UTF-8 sequence in half. Continuation lines begin with one space, and that space
    counts toward the limit.
    """
    lines: list[str] = []
    current = b""
    for char in line:
        chunk = char.encode("utf-8")
        if current and len(current) + len(chunk) > limit:
            lines.append(current.decode("utf-8"))
            current = b" " + chunk
        else:
            current += chunk
    lines.append(current.decode("utf-8"))
    return lines


def _parse_date(value: str) -> date:
    match = _DATE.match(value.strip())
    if not match:
        raise EventError(f"not a YYYY-MM-DD date: {value!r}")
    return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))


def _parse_datetime(value: str) -> datetime:
    match = _DATETIME.match(value.strip())
    if not match:
        raise EventError(f"not a 'YYYY-MM-DD HH:MM' datetime: {value!r}")
    year, month, day, hour, minute, second = match.groups()
    return datetime(
        int(year), int(month), int(day), int(hour), int(minute), int(second or 0)
    )


def parse_start(value: str) -> tuple[date | datetime, bool]:
    """Parse `event.start`, returning the value and whether it is all-day."""
    if _DATE.match(value.strip()):
        return _parse_date(value), True
    return _parse_datetime(value), False


def to_utc(moment: datetime, tz_name: str) -> datetime:
    """Convert a naive wall-clock time in `tz_name` to UTC, DST included."""
    try:
        zone = ZoneInfo(tz_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise EventError(
            f"unknown timezone {tz_name!r} - use an IANA name like 'Europe/Berlin', "
            f"or give event.utc instead"
        ) from exc
    return moment.replace(tzinfo=zone).astimezone(timezone.utc)


def _parse_utc(value: str) -> datetime:
    raw = _UTC_SUFFIX.sub("", value.strip())
    moment = _parse_datetime(raw)
    return moment.replace(tzinfo=timezone.utc)


def _stamp(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _date_stamp(value: date) -> str:
    return value.strftime("%Y%m%d")


def make_uid(slug: str, title: str, domain: str = DOMAIN) -> str:
    """A UID that survives editing, renaming and moving the round.

    Derived from the round slug plus the normalised title - never the file path or the
    start time, because archiving renames the file, moves the folder, and a reschedule
    must update the existing entry rather than create a second one.
    """
    identity = f"{slug}\x00{title.strip().lower()}"
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:32]
    return f"{digest}@{domain}"


def build_ics(
    *,
    event: dict[str, str],
    slug: str,
    now: datetime,
    domain: str = DOMAIN,
) -> tuple[str, list[str]]:
    """Render a VCALENDAR for `event`. Raises `EventError` on anything unsafe to guess."""
    warnings: list[str] = []
    title = event.get("title", "").strip()
    if not title:
        raise EventError("event.title is required to build a calendar entry")

    start_raw = event.get("start", "").strip()
    if not start_raw:
        raise EventError("event.start is required to build a calendar entry")

    start, all_day = parse_start(start_raw)
    tz_name = event.get("timezone", "").strip()
    utc_raw = event.get("utc", "").strip()

    if all_day:
        start_date = start if isinstance(start, date) else start.date()
        end_raw = event.get("end", "").strip()
        if end_raw:
            end_date = _parse_date(end_raw)
            # RFC 5545 DTEND is exclusive; a user writing the last day of the event would
            # silently lose it, so say what the file actually means.
            warnings.append(
                f"all-day DTEND is exclusive: '{end_raw}' means the event ends before that "
                f"day, so the last day included is {(end_date - timedelta(days=1)).isoformat()}"
            )
        else:
            end_date = start_date + timedelta(days=1)
        if end_date <= start_date:
            raise EventError(
                f"event.end ({end_date.isoformat()}) must be after event.start "
                f"({start_date.isoformat()})"
            )
        dt_start = f"DTSTART;VALUE=DATE:{_date_stamp(start_date)}"
        dt_end = f"DTEND;VALUE=DATE:{_date_stamp(end_date)}"
    else:
        start_dt = start if isinstance(start, datetime) else datetime.combine(start, time())
        if utc_raw:
            start_utc = _parse_utc(utc_raw)
        elif tz_name:
            start_utc = to_utc(start_dt, tz_name)
        else:
            raise EventError(
                "a timed event needs event.timezone (an IANA name) or event.utc - "
                "guessing would put the entry at the wrong hour"
            )

        end_raw = event.get("end", "").strip()
        if end_raw:
            if _DATE.match(end_raw):
                raise EventError(
                    f"event.start has a time but event.end ({end_raw!r}) does not - "
                    f"give both a time or neither"
                )
            end_naive = _parse_datetime(end_raw)
            if utc_raw:
                # event.utc sets the frame for the whole event, so event.end is UTC too.
                end_utc = end_naive.replace(tzinfo=timezone.utc)
            else:
                # Convert each end independently from the wall clock: an event spanning a
                # DST change has a different offset at each end, so start + duration is wrong.
                end_utc = to_utc(end_naive, tz_name)
        else:
            end_utc = start_utc + timedelta(hours=1)
            warnings.append("event.end not given - defaulted to one hour after the start")

        if end_utc <= start_utc:
            raise EventError(
                f"event.end ({end_utc.isoformat()}) must be after event.start "
                f"({start_utc.isoformat()})"
            )
        dt_start = f"DTSTART:{_stamp(start_utc)}"
        dt_end = f"DTEND:{_stamp(end_utc)}"

    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", f"PRODID:{PRODID}", "CALSCALE:GREGORIAN"]

    method = event.get("method", "").strip().upper()
    organizer = event.get("organizer", "").strip()
    attendees = split_addresses(event.get("attendees", ""))
    if method:
        if method != "REQUEST":
            raise EventError(f"unsupported event.method {method!r} - only 'request' is supported")
        if not organizer:
            raise EventError(
                "event.method: request needs event.organizer - RFC 5546 requires ORGANIZER, "
                "and guessing one produces an invitation the client will reject"
            )
        lines.append("METHOD:REQUEST")

    lines.append("BEGIN:VEVENT")
    lines.append(f"UID:{event.get('uid', '').strip() or make_uid(slug, title, domain)}")
    lines.append(f"DTSTAMP:{_stamp(now)}")
    lines.append(dt_start)
    lines.append(dt_end)
    lines.append(f"SUMMARY:{escape_text(title)}")
    if event.get("location", "").strip():
        lines.append(f"LOCATION:{escape_text(event['location'].strip())}")
    if event.get("description", "").strip():
        lines.append(f"DESCRIPTION:{escape_text(event['description'].strip())}")
    lines.append("TRANSP:OPAQUE")
    if organizer:
        lines.append(f"ORGANIZER;CN={escape_text(organizer)}:mailto:{organizer}")
    for attendee in attendees:
        lines.append(f"ATTENDEE;CN={escape_text(attendee)};RSVP=TRUE:mailto:{attendee}")
    lines.append("END:VEVENT")
    lines.append("END:VCALENDAR")

    folded: list[str] = []
    for line in lines:
        folded.extend(fold_line(line))
    return "\r\n".join(folded) + "\r\n", warnings

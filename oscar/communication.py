"""Explicit communication requests compile into the existing account-bound Fabric/runtime."""

import base64
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import getaddresses
from typing import TYPE_CHECKING, Any

from .contracts import Capability
from .jev import Intent

if TYPE_CHECKING:
    from .harness import Harness


@dataclass(frozen=True)
class PreparedCommunication:
    capability: Capability
    intent: Intent
    review: dict[str, Any]


def _instant(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("explicit time zone offset required")
    return parsed.astimezone(UTC)


def _addresses(value: str) -> list[str]:
    addresses = value.split(",")
    if (
        not 1 <= len(addresses) <= 16
        or any(
            not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,63}", a)
            or len(a) > 254
            for a in addresses
        )
        or len(set(addresses)) != len(addresses)
    ):
        raise ValueError("explicit comma-separated email addresses required")
    return addresses


def prepare(harness: "Harness", text: str) -> PreparedCommunication | None:
    """No model infers account, recipient, body or time; an ambiguous request has no effects."""
    request = re.sub(r"^please ", "", text.strip(), count=1, flags=re.IGNORECASE)
    if not re.match(
        r"(?:(?:draft|send|list|read) email\b|create calendar event\b|"
        r"create task\b|list task lists\b|list tasks\b)",
        request,
        re.IGNORECASE,
    ):
        return None
    if len(text) > 4096:
        raise ValueError("communication request exceeds the native review bound")
    quoted = r'("(?:[^"\\]|\\.)*")'
    mail = re.fullmatch(
        r"(draft|send) email using (\S+) to (\S+) subject " + quoted + " body " + quoted,
        request,
        re.IGNORECASE,
    )
    listing = re.fullmatch(r"list email using (\S+)", request, re.IGNORECASE)
    reading = re.fullmatch(
        r"read email ([A-Za-z0-9_=-]{1,500}) using (\S+)", request, re.IGNORECASE
    )
    event = re.fullmatch(
        r"create calendar event using (\S+) titled "
        + quoted
        + r" from (\S+) to (\S+)(?: with (\S+))?",
        request,
        re.IGNORECASE,
    )
    identifier = r"([A-Za-z0-9_=@+-]{1,500})"
    task = re.fullmatch(
        r"create task using (\S+) in list "
        + identifier
        + " titled "
        + quoted
        + r" due (\d{4}-\d{2}-\d{2}) notes "
        + quoted,
        request,
        re.IGNORECASE,
    )
    task_lists = re.fullmatch(r"list task lists using (\S+)", request, re.IGNORECASE)
    task_listing = re.fullmatch(
        r"list tasks using (\S+) in list " + identifier, request, re.IGNORECASE
    )
    if not any((mail, listing, reading, event, task, task_lists, task_listing)):
        raise ValueError(
            "Specify account and exact mail fields, event offset times, "
            "or task list/title/date/notes"
        )
    if mail:
        alias = mail[2]
    elif listing:
        alias = listing[1]
    elif reading:
        alias = reading[2]
    elif event:
        alias = event[1]
    else:
        selected_task = task or task_lists or task_listing
        assert selected_task is not None
        alias = selected_task[1]
    accounts = [
        a
        for a in harness.accounts.list_accounts()
        if a.status == "connected"
        and (a.id == alias or a.alias == alias)
        and a.provider in {"google", "microsoft"}
    ]
    if len(accounts) != 1:
        raise ValueError("select an unambiguous connected account ID or alias")
    account = accounts[0]
    google = account.provider == "google"
    prefix = "google.gmail" if google else "microsoft.mail"
    parameters: dict[str, Any] = {"path": {"userId": "me"}} if google else {"path": {}}
    expected: dict[str, Any] = {}
    if task or task_lists or task_listing:
        prefix = "google.tasks" if google else "microsoft.todo"
        parameters = {"path": {}}
        if task or task_listing:
            selected_list = task or task_listing
            assert selected_list is not None
            parameters["path"]["tasklist" if google else "listId"] = selected_list[2]
        if task:
            title, notes = json.loads(task[3]), json.loads(task[5])
            if not title or len(title) > 200 or any(ord(c) < 32 for c in title):
                raise ValueError("single-line bounded task title required")
            if len(notes) > 3000 or "\x00" in notes or "\r" in notes:
                raise ValueError("bounded task notes with LF line endings required")
            due = date.fromisoformat(task[4]).isoformat()
            expected = {"title": title, "notes": notes, "due": due}
            parameters["body"] = (
                {"title": title, "notes": notes, "due": due + "T00:00:00Z", "status": "needsAction"}
                if google
                else {
                    "title": title,
                    "body": {"contentType": "text", "content": notes},
                    "dueDateTime": {"dateTime": due + "T00:00:00", "timeZone": "UTC"},
                    "status": "notStarted",
                }
            )
            name = prefix + (".create" if google else ".tasks.create")
        else:
            name = prefix + (".lists" if task_lists else ".list" if google else ".tasks.list")
            parameters["query"] = {"maxResults": "10"} if google else {"$top": "10"}
    elif mail:
        operation = mail[1].lower()
        recipients = _addresses(mail[3])
        subject, body = json.loads(mail[4]), json.loads(mail[5])
        if not subject or len(subject) > 200 or any(ord(c) < 32 for c in subject):
            raise ValueError("single-line bounded subject required")
        if not body or len(body) > 3000 or "\x00" in body or "\r" in body:
            raise ValueError("bounded plain text body with LF line endings required")
        expected = {"to": recipients, "subject": subject, "body": body}
        if google:
            message = EmailMessage(policy=policy.SMTP)
            message["To"], message["Subject"] = ", ".join(recipients), subject
            message.set_content(body)
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
            parameters["body"] = {"message": {"raw": raw}} if operation == "draft" else {"raw": raw}
        else:
            message_body = {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": a}} for a in recipients],
            }
            parameters["body"] = (
                message_body
                if operation == "draft"
                else {"message": message_body, "saveToSentItems": True}
            )
        name = prefix + "." + operation
    elif listing:
        name = prefix + (".search" if google else ".list")
        parameters["query"] = (
            {"maxResults": "10"}
            if google
            else {"$top": "10", "$select": "id,subject,from,receivedDateTime,isRead"}
        )
    elif reading:
        name = prefix + ".read"
        parameters["path"]["id"] = reading[1]
        if google:
            parameters["query"] = {"format": "full"}
    else:
        assert event is not None
        title = json.loads(event[2])
        if not title or len(title) > 200 or any(ord(c) < 32 for c in title):
            raise ValueError("single-line bounded event title required")
        start, end = _instant(event[3]), _instant(event[4])
        if not 0 < (end - start).total_seconds() <= 604800:
            raise ValueError("event end must follow start within seven days")
        attendees = _addresses(event[5]) if event[5] else []
        expected = {
            "title": title,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "attendees": attendees,
        }
        name = ("google.calendar" if google else "microsoft.calendar") + ".events.create"
        parameters = {"path": {"calendarId": "primary"}} if google else {"path": {}}
        if google:
            parameters["query"] = {"sendUpdates": "all" if attendees else "none"}
            parameters["body"] = {
                "summary": title,
                "start": {"dateTime": start.isoformat()},
                "end": {"dateTime": end.isoformat()},
                **({"attendees": [{"email": a} for a in attendees]} if attendees else {}),
            }
        else:
            parameters["body"] = {
                "subject": title,
                "start": {"dateTime": start.replace(tzinfo=None).isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end.replace(tzinfo=None).isoformat(), "timeZone": "UTC"},
                **(
                    {
                        "attendees": [
                            {"emailAddress": {"address": a}, "type": "required"} for a in attendees
                        ]
                    }
                    if attendees
                    else {}
                ),
            }
    mount = harness.ensure_connections()
    capability = mount.capability(name, account_id=account.id)
    if harness.connectors.secrets.redact(text) != text:
        raise ValueError("credential material cannot enter communication content")
    instance_id = capability.id.split(":", 1)[0]
    criterion = (
        {
            "kind": "connector_communication",
            "instance_id": instance_id,
            "expected": expected,
            "operation": name,
        }
        if expected
        else {"kind": "unavailable"}
    )
    criterion["connector_account"] = {"id": account.id, "generation": account.generation}
    review = {
        "account_id": account.id,
        "account_generation": account.generation,
        "capability": capability.name,
        "parameters": parameters,
    }
    if (
        len(text.encode()) > 8192
        or len((json.dumps(review, ensure_ascii=False) + text).encode()) > 24000
    ):
        raise ValueError("exact communication review exceeds the native display bound")
    reference = harness.connectors.stage(parameters)
    return PreparedCommunication(
        capability,
        Intent(
            text,
            "capability",
            capability_kind=capability.input_kind,
            parameters={"request_ref": reference},
            criterion=criterion,
        ),
        review,
    )


def matches(name: str, payload: dict[str, Any], expected: dict[str, Any]) -> bool:
    """Prove the saved provider resource, never delivery to another person's inbox."""
    if name == "google.tasks.create":
        return bool(
            payload.get("title") == expected["title"]
            and payload.get("notes", "") == expected["notes"]
            and _instant(payload["due"]).date().isoformat() == expected["due"]
            and payload.get("status") == "needsAction"
            and payload.get("deleted") is not True
            and payload.get("hidden") is not True
        )
    if name == "microsoft.todo.tasks.create":
        due = payload["dueDateTime"]
        instant = datetime.fromisoformat(due["dateTime"].replace("Z", "+00:00"))
        if instant.tzinfo is None:
            instant = instant.replace(tzinfo=UTC)
        return bool(
            payload.get("title") == expected["title"]
            and payload.get("body", {}).get("contentType", "").lower() == "text"
            and payload["body"]["content"].replace("\r\n", "\n") == expected["notes"]
            and due.get("timeZone") in {"UTC", "Etc/UTC"}
            and instant == _instant(expected["due"] + "T00:00:00Z")
            and payload.get("status") == "notStarted"
        )
    if name.startswith("google.gmail."):
        message_data = payload["message"] if name.endswith("draft") else payload
        if name.endswith("send") and "SENT" not in message_data.get("labelIds", []):
            return False
        raw = message_data["raw"]
        message = BytesParser(policy=policy.default).parsebytes(
            base64.b64decode(raw + "=" * (-len(raw) % 4), altchars=b"-_", validate=True)
        )
        content = message.get_content()
        return bool(
            not message.defects
            and not message.is_multipart()
            and message.get_content_type() == "text/plain"
            and len(message.get_all("Subject", [])) == 1
            and len(message.get_all("To", [])) == 1
            and not message.get_all("Cc")
            and not message.get_all("Bcc")
            and sorted(a for _, a in getaddresses(message.get_all("To", [])))
            == sorted(expected["to"])
            and str(message["Subject"]) == expected["subject"]
            and content.replace("\r\n", "\n") == expected["body"].removesuffix("\n") + "\n"
        )
    if name == "microsoft.mail.draft":
        return bool(
            payload.get("isDraft") is True
            and payload.get("subject") == expected["subject"]
            and payload.get("body", {}).get("contentType", "").lower() == "text"
            and payload["body"]["content"].replace("\r\n", "\n") == expected["body"]
            and sorted(a["emailAddress"]["address"] for a in payload.get("toRecipients", []))
            == sorted(expected["to"])
            and not payload.get("ccRecipients")
            and not payload.get("bccRecipients")
        )
    google = name.startswith("google.")
    if name.endswith(".events.create"):

        def event_time(key: str) -> datetime:
            point = payload[key]
            value = point["dateTime"]
            if not google and point.get("timeZone") in {"UTC", "Etc/UTC"}:
                parsed = datetime.fromisoformat(value)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=UTC)
            return _instant(value)

        attendees = [
            a["email"] if google else a["emailAddress"]["address"]
            for a in payload.get("attendees", [])
        ]
        return bool(
            payload.get("summary" if google else "subject") == expected["title"]
            and payload.get("status") != "cancelled"
            and payload.get("isCancelled") is not True
            and event_time("start") == _instant(expected["start"])
            and event_time("end") == _instant(expected["end"])
            and sorted(attendees) == sorted(expected["attendees"])
        )
    return False

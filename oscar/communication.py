"""Explicit communication requests compile into the existing account-bound Fabric/runtime."""

import base64
import html
import json
import re
from dataclasses import dataclass
from datetime import UTC, date, datetime
from email import policy
from email.message import EmailMessage
from email.parser import BytesParser
from email.utils import getaddresses
from html.parser import HTMLParser
from typing import TYPE_CHECKING, Any

from .contracts import Capability
from .jev import Intent

if TYPE_CHECKING:
    from .harness import Harness


_CALENDAR_MUTATIONS = {
    "google.calendar.events.create",
    "google.calendar.events.update",
    "microsoft.calendar.events.create",
    "microsoft.calendar.events.update",
}

_TASK_UPDATES = {
    "google.tasks.update": {"needsAction", "completed"},
    "microsoft.todo.tasks.update": {
        "notStarted",
        "inProgress",
        "completed",
        "waitingOnOthers",
        "deferred",
    },
}


def task_notes(body: dict[str, Any]) -> str:
    """Read literal notes only; unsupported rich markup cannot become verified text."""
    content = body["content"]
    if not isinstance(content, str) or len(content) > 24000:
        raise ValueError("bounded task notes required")
    if not isinstance(body["contentType"], str):
        raise ValueError("task note content type unavailable")
    if body["contentType"].lower() == "text":
        return content.replace("\r\n", "\n")
    if body["contentType"].lower() != "html":
        raise ValueError("task note content type unavailable")

    class Notes(HTMLParser):
        def __init__(self) -> None:
            super().__init__(convert_charrefs=True)
            self.parts: list[str] = []
            self.stack: list[str] = []
            self.block = False

        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if attrs or tag not in {"html", "body", "div", "p", "br"}:
                raise ValueError("unsupported task note markup")
            if tag == "br":
                self.parts.append("\n")
                return
            if tag in {"div", "p"}:
                if self.block:
                    raise ValueError("multiple task note blocks require separate comparison")
                self.block = True
            self.stack.append(tag)

        def handle_endtag(self, tag: str) -> None:
            if not self.stack or self.stack.pop() != tag:
                raise ValueError("unbalanced task note markup")

        def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag != "br":
                raise ValueError("unsupported task note markup")
            self.handle_starttag(tag, attrs)

        def handle_data(self, data: str) -> None:
            self.parts.append(data)

        def handle_comment(self, data: str) -> None:
            raise ValueError("unsupported task note markup")

        def handle_decl(self, decl: str) -> None:
            raise ValueError("unsupported task note markup")

        def handle_pi(self, data: str) -> None:
            raise ValueError("unsupported task note markup")

        def unknown_decl(self, data: str) -> None:
            raise ValueError("unsupported task note markup")

    parser = Notes()
    try:
        parser.feed(content)
        parser.close()
    except AssertionError:
        raise ValueError("unsupported task note markup") from None
    if parser.stack:
        raise ValueError("unbalanced task note markup")
    return "".join(parser.parts).replace("\r\n", "\n")


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
        r"create task\b|list task lists\b|list tasks\b|list contacts\b|read contact\b|"
        r"create meet space\b|read meet space\b|(?:create|read|list) gitlab (?:issue|project))",
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
    contacts = re.fullmatch(r"list contacts using (\S+)", request, re.IGNORECASE)
    contact = re.fullmatch(
        r"read contact ((?:people/)?[A-Za-z0-9_=-]{1,500}) using (\S+)",
        request,
        re.IGNORECASE,
    )
    meet_create = re.fullmatch(
        r"create meet space using (\S+) access restricted", request, re.IGNORECASE
    )
    meet_read = re.fullmatch(
        r"read meet space ([A-Za-z0-9_-]{1,128}) using (\S+)", request, re.IGNORECASE
    )
    gitlab_create = re.fullmatch(
        r"create gitlab issue using (\S+) in project ([1-9][0-9]{0,17}) titled "
        + quoted
        + " body "
        + quoted
        + r" visibility (project|confidential)",
        request,
        re.IGNORECASE,
    )
    gitlab_read = re.fullmatch(
        r"read gitlab issue ([1-9][0-9]{0,17}) using (\S+) in project ([1-9][0-9]{0,17})",
        request,
        re.IGNORECASE,
    )
    gitlab_list = re.fullmatch(
        r"list gitlab issues using (\S+) in project ([1-9][0-9]{0,17})(?: page ([1-9][0-9]{0,4}))?",
        request,
        re.IGNORECASE,
    )
    gitlab_projects = re.fullmatch(
        r"list gitlab projects using (\S+)(?: page ([1-9][0-9]{0,4}))?", request, re.IGNORECASE
    )
    if not any(
        (
            mail,
            listing,
            reading,
            event,
            task,
            task_lists,
            task_listing,
            contacts,
            contact,
            meet_create,
            meet_read,
            gitlab_create,
            gitlab_read,
            gitlab_list,
            gitlab_projects,
        )
    ):
        raise ValueError(
            "Specify account and exact mail fields, event offset times, "
            "task list/title/date/notes, contact ID, or restricted Meet space"
        )
    gitlab = gitlab_create or gitlab_read or gitlab_list or gitlab_projects
    if gitlab_read:
        alias = gitlab_read[2]
    elif gitlab:
        alias = gitlab[1]
    elif meet_create:
        alias = meet_create[1]
    elif meet_read:
        alias = meet_read[2]
    elif mail:
        alias = mail[2]
    elif listing:
        alias = listing[1]
    elif reading:
        alias = reading[2]
    elif event:
        alias = event[1]
    elif contacts:
        alias = contacts[1]
    elif contact:
        alias = contact[2]
    else:
        selected_task = task or task_lists or task_listing
        assert selected_task is not None
        alias = selected_task[1]
    accounts = [
        a
        for a in harness.accounts.list_accounts()
        if a.status == "connected"
        and (a.id == alias or a.alias == alias)
        and a.provider in {"google", "microsoft", "gitlab"}
    ]
    if len(accounts) != 1:
        raise ValueError("select an unambiguous connected account ID or alias")
    account = accounts[0]
    if (account.provider == "gitlab") != bool(gitlab):
        raise ValueError("GitLab requests require the selected connected GitLab account")
    google = account.provider == "google"
    prefix = "google.gmail" if google else "microsoft.mail"
    parameters: dict[str, Any] = {"path": {"userId": "me"}} if google else {"path": {}}
    expected: dict[str, Any] = {}
    if gitlab:
        parameters = {"path": {}}
        if gitlab_projects:
            name = "gitlab.projects.list"
            parameters["query"] = {
                "membership": True,
                "per_page": 10,
                "page": int(gitlab_projects[2] or 1),
            }
        else:
            project = gitlab_read[3] if gitlab_read else gitlab[2]
            parameters["path"]["project"] = project
            if gitlab_create:
                title, description = json.loads(gitlab_create[3]), json.loads(gitlab_create[4])
                if not title or len(title) > 200 or any(ord(c) < 32 for c in title):
                    raise ValueError("single-line bounded issue title required")
                if len(description) > 3000 or "\x00" in description or "\r" in description:
                    raise ValueError("bounded issue body with LF line endings required")
                confidential = gitlab_create[5].lower() == "confidential"
                parameters["body"] = {
                    "title": title,
                    "description": description,
                    "confidential": confidential,
                }
                expected = {**parameters["body"], "project_id": int(project)}
                name = "gitlab.issues.create"
            elif gitlab_read:
                name = "gitlab.issues.get"
                parameters["path"]["issue"] = gitlab_read[1]
            else:
                name = "gitlab.issues.list"
                assert gitlab_list is not None
                parameters["query"] = {
                    "state": "opened",
                    "per_page": 10,
                    "page": int(gitlab_list[3] or 1),
                }
    elif meet_create or meet_read:
        if not google:
            raise ValueError("Meet requires the selected connected Google account")
        name = "google.meet." + ("create" if meet_create else "get")
        parameters = {"path": {}}
        if meet_create:
            parameters["body"] = {"config": {"accessType": "RESTRICTED"}}
            expected = {"accessType": "RESTRICTED"}
        else:
            assert meet_read is not None
            parameters["path"]["space"] = meet_read[1]
    elif contacts or contact:
        prefix = "google.contacts" if google else "microsoft.contacts"
        name = prefix + (".read" if contact else ".list")
        parameters = {"path": {}}
        parameters["query"] = (
            {"personFields": "names,emailAddresses,phoneNumbers"}
            if google
            else {"$select": "id,displayName,emailAddresses,businessPhones,homePhones,mobilePhone"}
        )
        if contact:
            resource_id = contact[1]
            if google:
                resource_id = resource_id.split("/")[-1]
            elif "/" in resource_id:
                raise ValueError("select the exact provider contact ID")
            parameters["path"]["resourceId" if google else "id"] = resource_id
        else:
            parameters["query"]["pageSize" if google else "$top"] = "10"
    elif task or task_lists or task_listing:
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
                    "body": {
                        "contentType": "html",
                        "content": "<div>" + html.escape(notes).replace("\n", "<br>") + "</div>",
                    },
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


def task_expectation(name: str, parameters: dict[str, Any]) -> dict[str, Any] | None:
    """Recognize native saved-resource contracts, never model-supplied success criteria."""
    if name in _CALENDAR_MUTATIONS:
        return calendar_expectation(name, parameters)
    if name in _TASK_UPDATES:
        body = parameters.get("body")
        if (
            set(parameters) == {"path", "body"}
            and isinstance(body, dict)
            and set(body) == {"status"}
            and isinstance(body["status"], str)
            and body["status"] in _TASK_UPDATES[name]
        ):
            return {"status": body["status"]}
        return None
    if name not in {"google.tasks.create", "microsoft.todo.tasks.create"}:
        return None
    try:
        if set(parameters) != {"path", "body"}:
            return None
        body = parameters["body"]
        if name == "google.tasks.create":
            if (
                set(body) - {"title", "notes", "due", "status"}
                or body.get("status", "needsAction") != "needsAction"
            ):
                return None
            notes, due = body.get("notes", ""), body["due"]
        else:
            if (
                set(body) != {"title", "body", "dueDateTime", "status"}
                or body["status"] != "notStarted"
            ):
                return None
            if set(body["body"]) != {"contentType", "content"} or body["body"][
                "contentType"
            ].lower() not in {"text", "html"}:
                return None
            point = body["dueDateTime"]
            if set(point) != {"dateTime", "timeZone"} or point["timeZone"] != "UTC":
                return None
            notes, due = task_notes(body["body"]), point["dateTime"] + "Z"
        title = body["title"]
        if (
            not isinstance(title, str)
            or not 1 <= len(title) <= 200
            or any(ord(c) < 32 for c in title)
            or not isinstance(notes, str)
            or len(notes) > 3000
            or "\r" in notes
            or "\x00" in notes
            or not isinstance(due, str)
            or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T00:00:00(?:Z|\+00:00)", due)
        ):
            return None
        return {"title": title, "notes": notes, "due": _instant(due).date().isoformat()}
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def calendar_expectation(name: str, parameters: dict[str, Any]) -> dict[str, Any] | None:
    """Recognize literal timed events or time-only moves; other bodies remain partial."""
    if name not in _CALENDAR_MUTATIONS:
        return None
    try:
        google = name.startswith("google.")
        create = name.endswith(".create")
        if set(parameters) - {"path", "body", "query"}:
            return None
        query = parameters.get("query", {})
        if (
            not isinstance(query, dict)
            or query
            and (
                not google
                or set(query) != {"sendUpdates"}
                or query["sendUpdates"] not in {"all", "none", "externalOnly"}
            )
        ):
            return None
        body = parameters["body"]
        title_key = "summary" if google else "subject"
        allowed = {title_key, "start", "end", "attendees"} if create else {"start", "end"}
        if set(body) - allowed or not create and set(body) != allowed:
            return None
        times = {}
        for key in ("start", "end"):
            point = body[key]
            if set(point) != ({"dateTime"} if google else {"dateTime", "timeZone"}):
                return None
            value = point["dateTime"]
            if not google:
                if point["timeZone"] != "UTC" or datetime.fromisoformat(value).tzinfo is not None:
                    return None
                value += "Z"
            times[key] = _instant(value)
        if not 0 < (times["end"] - times["start"]).total_seconds() <= 7 * 86400:
            return None
        expected: dict[str, Any] = {key: value.isoformat() for key, value in times.items()}
        if create:
            title = body[title_key]
            if (
                not isinstance(title, str)
                or not 1 <= len(title) <= 200
                or any(ord(c) < 32 for c in title)
            ):
                return None
            if (
                not isinstance(body.get("attendees", []), list)
                or len(body.get("attendees", [])) > 16
            ):
                return None
            attendees = []
            for attendee in body.get("attendees", []):
                if google:
                    if set(attendee) != {"email"}:
                        return None
                    attendees.append(attendee["email"])
                else:
                    if (
                        set(attendee) != {"emailAddress", "type"}
                        or attendee["type"] != "required"
                        or set(attendee["emailAddress"]) != {"address"}
                    ):
                        return None
                    attendees.append(attendee["emailAddress"]["address"])
            if attendees:
                _addresses(",".join(attendees))
            expected.update(title=title, attendees=attendees)
        return expected
    except (KeyError, TypeError, ValueError, AttributeError):
        return None


def matches(name: str, payload: dict[str, Any], expected: dict[str, Any]) -> bool:
    """Prove the saved provider resource, never delivery to another person's inbox."""
    if name in _TASK_UPDATES:
        return bool(
            set(expected) == {"status"}
            and payload.get("status") == expected["status"]
            and payload.get("deleted") is not True
            and payload.get("hidden") is not True
        )
    if name == "gitlab.issues.create":
        return bool(
            payload.get("title") == expected["title"]
            and payload.get("description", "") == expected["description"]
            and payload.get("confidential") is expected["confidential"]
            and type(payload.get("project_id")) is int
            and payload["project_id"] == expected["project_id"]
            and payload.get("state") == "opened"
        )
    if name == "google.meet.create":
        code = payload.get("meetingCode")
        config = payload.get("config")
        return bool(
            isinstance(code, str)
            and re.fullmatch(r"[a-z]+-[a-z]+-[a-z]+", code)
            and len(code) <= 128
            and payload.get("meetingUri") == "https://meet.google.com/" + code
            and isinstance(config, dict)
            and config.get("accessType") == expected["accessType"]
        )
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
            and task_notes(payload["body"]) == expected["notes"]
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
    if name in _CALENDAR_MUTATIONS:

        def event_time(key: str) -> datetime:
            point = payload[key]
            value = point["dateTime"]
            if not google and point.get("timeZone") in {"UTC", "Etc/UTC"}:
                parsed = datetime.fromisoformat(value)
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=UTC)
            return _instant(value)

        times_match = bool(
            payload.get("status") != "cancelled"
            and payload.get("isCancelled") is not True
            and event_time("start") == _instant(expected["start"])
            and event_time("end") == _instant(expected["end"])
        )
        if name.endswith(".events.update"):
            return times_match
        attendees = [
            a["email"] if google else a["emailAddress"]["address"]
            for a in payload.get("attendees", [])
        ]
        return bool(
            times_match
            and payload.get("summary" if google else "subject") == expected["title"]
            and sorted(attendees) == sorted(expected["attendees"])
        )
    return False

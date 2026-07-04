"""Tool: a fake ticketing system.

Simulates reading a ticket and writing back a resolution or an escalation. In a
real deployment this is where you would touch Zendesk, Jira, an internal queue,
etc. Here it is an in-memory store so the demo has a realistic 'update the ticket'
side effect without any external dependency.
"""

from __future__ import annotations

from typing import Any

# In-memory record of what the system did to each ticket during a run.
_UPDATES: dict[str, dict[str, Any]] = {}


def read_ticket(ticket: dict[str, Any]) -> dict[str, Any]:
    """Return the ticket as the system sees it (identity here; a hook in reality)."""
    return dict(ticket)


def update_ticket(ticket_id: str, *, status: str, resolution: str) -> dict[str, Any]:
    """Record a status change and resolution note for a ticket."""
    record = {"ticket_id": ticket_id, "status": status, "resolution": resolution}
    _UPDATES[ticket_id] = record
    return record


def get_update(ticket_id: str) -> dict[str, Any] | None:
    return _UPDATES.get(ticket_id)

"""Tests for the audit log module."""
import pytest
from utils.audit_log import AuditLog


class FakeUser:
    def __init__(self, id, email):
        self.id = id
        self.email = email


class FakeTarget:
    def __init__(self, id):
        self.id = id


class InMemoryDB:
    def __init__(self):
        self.rows = []

    def insert(self, table, row):
        self.rows.append(row)

    def query(self, sql, params=None):
        return list(self.rows)


def test_log_event_with_user():
    db = InMemoryDB()
    audit = AuditLog(db)
    user = FakeUser(id=42, email="alice@example.com")
    target = FakeTarget(id=1)
    audit.log_event(user, "test_action", target)
    assert db.rows[0]["actor_id"] == 42
    assert db.rows[0]["actor_email"] == "alice@example.com"


def test_log_event_with_metadata():
    db = InMemoryDB()
    audit = AuditLog(db)
    user = FakeUser(id=7, email="bob@example.com")
    target = FakeTarget(id=99)
    audit.log_event(user, "charge", target, metadata={"amount": 100})
    assert db.rows[0]["metadata"] == {"amount": 100}


# NOTE: There is intentionally no test for actor=None. AuditLog has never
# supported that case directly. The only caller that needs to log without
# an actor (auth/login.py) uses a try/except workaround.

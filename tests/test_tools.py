"""Guardrail tests. These run without an API key."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import store  # noqa: E402
from tools import ToolContext, needs_approval, run_tool  # noqa: E402


@pytest.fixture
def db(tmp_path):
    path = str(tmp_path / "test.db")
    store.seed(path)
    return path


def ctx(db, email):
    return ToolContext(db_path=db, customer_email=email)


def test_small_refund_goes_through(db):
    out, status = run_tool("issue_refund", {"order_id": "1001", "amount": 79, "reason": "defect"},
                           ctx(db, "maya.chen@example.com"))
    assert status == "ok" and out["refunded"] == 79


def test_cannot_refund_twice(db):
    c = ctx(db, "maya.chen@example.com")
    run_tool("issue_refund", {"order_id": "1001", "amount": 79, "reason": "defect"}, c)
    out, status = run_tool("issue_refund", {"order_id": "1001", "amount": 79, "reason": "again"}, c)
    assert status == "blocked" and "already been refunded" in out["error"]


def test_large_refund_needs_approval(db):
    c = ctx(db, "jordan.lee@example.com")
    args = {"order_id": "1042", "amount": 149, "reason": "damaged"}
    assert needs_approval("issue_refund", args)
    out, status = run_tool("issue_refund", args, c)
    assert status == "blocked" and "approval" in out["error"]
    out, status = run_tool("issue_refund", args, c, approved=True)
    assert status == "ok"


def test_cannot_touch_another_customers_order(db):
    out, status = run_tool("issue_refund", {"order_id": "1042", "amount": 149, "reason": "x"},
                           ctx(db, "sam.rivera@example.com"), approved=True)
    assert status == "blocked" and "not found" in out["error"]
    out, status = run_tool("get_order", {"order_id": "1042"}, ctx(db, "sam.rivera@example.com"))
    assert status == "blocked"


def test_outside_refund_window(db):
    out, _ = run_tool("check_refund_eligibility", {"order_id": "1077"},
                      ctx(db, "priya.patel@example.com"))
    assert out["eligible"] is False and "outside" in out["reason"]


def test_cannot_refund_more_than_paid(db):
    out, status = run_tool("issue_refund", {"order_id": "1001", "amount": 500, "reason": "x"},
                           ctx(db, "maya.chen@example.com"), approved=True)
    assert status == "blocked"


def test_undelivered_order_not_refundable(db):
    out, _ = run_tool("check_refund_eligibility", {"order_id": "1043"},
                      ctx(db, "jordan.lee@example.com"))
    assert out["eligible"] is False


def test_help_center_search(db):
    out, status = run_tool("search_help_center", {"query": "damaged item refund"},
                           ctx(db, "maya.chen@example.com"))
    assert status == "ok" and any("Damaged" in r or "Refund" in r for r in out["results"])

"""The actions the support agent can take, and the rules around them.

Guardrails live here in code, not just in the prompt, so they hold even if
the model is tricked:
- The agent can only see and act on orders owned by the customer who wrote in.
- Refunds follow the store policy (delivered, within 30 days, once per order).
- Refunds over APPROVAL_THRESHOLD need a human to approve them.
"""
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import store

APPROVAL_THRESHOLD = 100.00
REFUND_WINDOW_DAYS = 30
POLICY_FILE = Path(__file__).parent / "policies.md"


@dataclass
class ToolContext:
    db_path: str
    customer_email: str  # the verified sender of the ticket


# ---------- Tool definitions sent to Claude ----------
TOOLS = [
    {
        "name": "get_customer",
        "description": "Get the profile of the customer who sent this ticket.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_orders",
        "description": "List all orders for the customer who sent this ticket.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_order",
        "description": "Get details and shipping status for one order.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string", "description": "For example, 1042"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "check_refund_eligibility",
        "description": "Check whether an order can be refunded under store policy, and the maximum amount.",
        "input_schema": {
            "type": "object",
            "properties": {"order_id": {"type": "string"}},
            "required": ["order_id"],
        },
    },
    {
        "name": "issue_refund",
        "description": (
            "Refund an order. Always check eligibility first. "
            f"Refunds over ${APPROVAL_THRESHOLD:.0f} are paused for a human to approve."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string"},
                "amount": {"type": "number", "description": "Amount in US dollars"},
                "reason": {"type": "string"},
            },
            "required": ["order_id", "amount", "reason"],
        },
    },
    {
        "name": "search_help_center",
        "description": "Search store policies (refunds, shipping, damaged items, security).",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "escalate_to_human",
        "description": "Hand the ticket to a human teammate when policy doesn't allow you to resolve it.",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "normal", "high"]},
            },
            "required": ["summary", "priority"],
        },
    },
]


# ---------- Helpers ----------
def _own_order(ctx, order_id):
    """Return the order only if it belongs to the ticket's customer."""
    rows = store.query(
        ctx.db_path,
        "SELECT * FROM orders WHERE order_id = ? AND customer_email = ?",
        (str(order_id).lstrip("#"), ctx.customer_email),
    )
    return rows[0] if rows else None


def _not_found(order_id):
    # Same message whether the order doesn't exist or belongs to someone else,
    # so the agent can't be used to probe other customers' orders.
    return {"error": f"Order {order_id} was not found on this customer's account."}


def _eligibility(order):
    remaining = round(order["total"] - order["refunded_amount"], 2)
    if order["status"] != "delivered":
        return {"eligible": False, "reason": f"Order is '{order['status']}', not delivered yet."}
    if order["refunded_amount"] > 0:
        return {"eligible": False, "reason": "This order has already been refunded."}
    days = (date.today() - date.fromisoformat(order["delivered_on"])).days
    if days > REFUND_WINDOW_DAYS:
        return {"eligible": False,
                "reason": f"Delivered {days} days ago, outside the {REFUND_WINDOW_DAYS}-day window."}
    return {"eligible": True, "max_refund": remaining, "days_since_delivery": days,
            "needs_human_approval": remaining > APPROVAL_THRESHOLD}


def needs_approval(name, tool_input):
    """True when an action must wait for a human."""
    if name != "issue_refund":
        return False
    try:
        return float(tool_input.get("amount", 0)) > APPROVAL_THRESHOLD
    except (TypeError, ValueError):
        return False


def search_policies(query, top_n=2):
    text = POLICY_FILE.read_text()
    sections = [s.strip() for s in text.split("## ")[1:]]
    words = set(re.findall(r"[a-z]+", query.lower()))
    scored = []
    for section in sections:
        section_words = set(re.findall(r"[a-z]+", section.lower()))
        scored.append((len(words & section_words), section))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [section for score, section in scored[:top_n] if score > 0]


# ---------- Running a tool ----------
def run_tool(name, tool_input, ctx, approved=False):
    """Run one tool. Returns (output_dict, status).

    status is "ok", "blocked" (a guardrail stopped it) or "error".
    """
    try:
        if name == "get_customer":
            rows = store.query(ctx.db_path, "SELECT * FROM customers WHERE email = ?",
                               (ctx.customer_email,))
            return (rows[0], "ok") if rows else ({"error": "Customer not found."}, "error")

        if name == "list_orders":
            rows = store.query(
                ctx.db_path,
                "SELECT order_id, product, total, status, delivered_on, estimated_delivery,"
                " refunded_amount FROM orders WHERE customer_email = ? ORDER BY order_id",
                (ctx.customer_email,),
            )
            return {"orders": rows}, "ok"

        if name in ("get_order", "check_refund_eligibility", "issue_refund"):
            order_id = str(tool_input.get("order_id", ""))
            order = _own_order(ctx, order_id)
            if order is None:
                return _not_found(order_id), "blocked"

            if name == "get_order":
                return {k: v for k, v in order.items() if k != "customer_email"}, "ok"

            check = _eligibility(order)
            if name == "check_refund_eligibility":
                return check, "ok"

            # issue_refund
            amount = round(float(tool_input.get("amount", 0)), 2)
            if not check["eligible"]:
                return {"error": f"Refund not allowed: {check['reason']}"}, "blocked"
            if amount <= 0 or amount > check["max_refund"]:
                return {"error": f"Amount must be between $0.01 and ${check['max_refund']:.2f}."}, "blocked"
            if amount > APPROVAL_THRESHOLD and not approved:
                return {"error": "Refunds over $100 need human approval."}, "blocked"
            store.execute(ctx.db_path,
                          "UPDATE orders SET refunded_amount = refunded_amount + ? WHERE order_id = ?",
                          (amount, order["order_id"]))
            store.execute(
                ctx.db_path,
                "INSERT INTO refunds (order_id, amount, reason, approved_by, created_on)"
                " VALUES (?, ?, ?, ?, ?)",
                (order["order_id"], amount, tool_input.get("reason", ""),
                 "human reviewer" if approved else "auto (under limit)", date.today().isoformat()),
            )
            return {"refunded": amount, "order_id": order["order_id"],
                    "message": "Refund issued. It arrives in 5 to 7 business days."}, "ok"

        if name == "search_help_center":
            results = search_policies(tool_input.get("query", ""))
            return {"results": results or ["No matching policy found."]}, "ok"

        if name == "escalate_to_human":
            store.execute(
                ctx.db_path,
                "INSERT INTO escalations (customer_email, summary, priority, created_on)"
                " VALUES (?, ?, ?, ?)",
                (ctx.customer_email, tool_input.get("summary", ""),
                 tool_input.get("priority", "normal"), date.today().isoformat()),
            )
            return {"escalated": True, "message": "A teammate will follow up within 1 business day."}, "ok"

        return {"error": f"Unknown tool: {name}"}, "error"
    except Exception as error:  # never let a tool crash the agent
        return {"error": f"Tool failed: {error}"}, "error"

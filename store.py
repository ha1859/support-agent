"""A small demo store (Juniper Supply Co.) kept in SQLite.

All customers and orders are fictional. Dates are set relative to today,
so the 30-day refund window always behaves the same in demos.
"""
import sqlite3
from datetime import date, timedelta
from pathlib import Path

CUSTOMERS = [
    ("maya.chen@example.com", "Maya Chen", "Gold"),
    ("jordan.lee@example.com", "Jordan Lee", "Standard"),
    ("priya.patel@example.com", "Priya Patel", "Standard"),
    ("sam.rivera@example.com", "Sam Rivera", "Gold"),
]

# (order_id, customer_email, product, total, status, days_since_delivery_or_eta, refunded_amount)
ORDERS = [
    ("1001", "maya.chen@example.com", "Wireless Headphones", 79.00, "delivered", 10, 0),
    ("1002", "maya.chen@example.com", "Insulated Water Bottle", 24.00, "delivered", 50, 0),
    ("1042", "jordan.lee@example.com", "Laptop Stand Pro", 149.00, "delivered", 5, 0),
    ("1043", "jordan.lee@example.com", "USB-C Hub", 59.00, "in_transit", -3, 0),
    ("1077", "priya.patel@example.com", "Standing Desk Mat", 89.00, "delivered", 95, 0),
    ("1080", "priya.patel@example.com", "Ergonomic Chair", 420.00, "processing", None, 0),
    ("1101", "sam.rivera@example.com", "Mechanical Keyboard", 129.00, "delivered", 3, 0),
    ("1102", "sam.rivera@example.com", "Monitor Light Bar", 45.00, "delivered", 20, 45.00),
]


def connect(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def seed(db_path):
    """Create (or reset) the demo database."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    today = date.today()
    with connect(db_path) as conn:
        conn.executescript(
            """
            DROP TABLE IF EXISTS customers;
            DROP TABLE IF EXISTS orders;
            DROP TABLE IF EXISTS refunds;
            DROP TABLE IF EXISTS escalations;
            CREATE TABLE customers (email TEXT PRIMARY KEY, name TEXT, tier TEXT);
            CREATE TABLE orders (
                order_id TEXT PRIMARY KEY, customer_email TEXT, product TEXT, total REAL,
                status TEXT, delivered_on TEXT, estimated_delivery TEXT, refunded_amount REAL
            );
            CREATE TABLE refunds (
                id INTEGER PRIMARY KEY AUTOINCREMENT, order_id TEXT, amount REAL,
                reason TEXT, approved_by TEXT, created_on TEXT
            );
            CREATE TABLE escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT, customer_email TEXT, summary TEXT,
                priority TEXT, created_on TEXT
            );
            """
        )
        conn.executemany("INSERT INTO customers VALUES (?, ?, ?)", CUSTOMERS)
        for order_id, email, product, total, status, days, refunded in ORDERS:
            delivered_on = estimated = None
            if status == "delivered":
                delivered_on = (today - timedelta(days=days)).isoformat()
            elif status == "in_transit":
                estimated = (today - timedelta(days=days)).isoformat()
            conn.execute(
                "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (order_id, email, product, total, status, delivered_on, estimated, refunded),
            )


def query(db_path, sql, params=()):
    with connect(db_path) as conn:
        return [dict(row) for row in conn.execute(sql, params).fetchall()]


def execute(db_path, sql, params=()):
    with connect(db_path) as conn:
        conn.execute(sql, params)

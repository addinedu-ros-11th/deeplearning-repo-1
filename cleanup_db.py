#!/usr/bin/env python3
import pymysql

# DB connection info (loaded from project config / .env)
import os

try:
    # Prefer the project config (configs/db_config.yaml uses ${VAR} substitution)
    from src.common.config import config  # works when running from repo root
except Exception:
    config = None


def _get_db_config():
    """
    Load DB config from `config.db.aws_rds` (preferred) or fallback to environment variables.
    Raises RuntimeError if required values are missing.
    """
    host = port = user = password = database = None

    if config and getattr(config, "db", None) and getattr(config.db, "aws_rds", None):
        aws = config.db.aws_rds
        host = aws.get("host")
        port = aws.get("port")
        user = aws.get("user")
        password = aws.get("password")
        database = aws.get("database")

    # Fallback to environment variables
    host = host or os.getenv("DB_HOST")
    port = port or os.getenv("DB_PORT")
    user = user or os.getenv("DB_USER")
    password = password or os.getenv("DB_PASSWORD")
    database = database or os.getenv("DB_NAME")

    if port is not None:
        try:
            port = int(port)
        except ValueError:
            raise RuntimeError("DB_PORT must be an integer")

    missing = [
        name
        for name, val in (
            ("DB_HOST", host),
            ("DB_PORT", port),
            ("DB_USER", user),
            ("DB_PASSWORD", password),
            ("DB_NAME", database),
        )
        if not val
    ]
    if missing:
        raise RuntimeError(f"Missing DB configuration for: {', '.join(missing)}")

    return host, port, user, password, database


DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME = _get_db_config()

conn = pymysql.connect(
    host=DB_HOST,
    port=DB_PORT,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME,
    cursorclass=pymysql.cursors.DictCursor,
)

cursor = conn.cursor()

print("=== Before Cleanup ===")
tables = ["shopping_sessions", "cart_items", "orders", "order_details", "obstacle_logs"]
for table in tables:
    cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
    count = cursor.fetchone()["cnt"]
    print(f"  {table}: {count} rows")

print("\n🧹 Cleaning transaction data...")

cursor.execute("DELETE FROM order_details")
print("  ✅ order_details cleared")

cursor.execute("DELETE FROM orders")
print("  ✅ orders cleared")

cursor.execute("DELETE FROM cart_items")
print("  ✅ cart_items cleared")

cursor.execute("DELETE FROM obstacle_logs")
print("  ✅ obstacle_logs cleared")

cursor.execute("DELETE FROM shopping_sessions")
print("  ✅ shopping_sessions cleared")

conn.commit()

print("\n=== After Cleanup ===")
for table in tables:
    cursor.execute(f"SELECT COUNT(*) as cnt FROM {table}")
    count = cursor.fetchone()["cnt"]
    print(f"  {table}: {count} rows")

# Check master data (should remain)
print("\n=== Master Data (Preserved) ===")
cursor.execute("SELECT COUNT(*) as cnt FROM products")
print(f'  products: {cursor.fetchone()["cnt"]} rows')
cursor.execute("SELECT COUNT(*) as cnt FROM categories")
print(f'  categories: {cursor.fetchone()["cnt"]} rows')
cursor.execute("SELECT COUNT(*) as cnt FROM carts")
print(f'  carts: {cursor.fetchone()["cnt"]} rows')

conn.close()
print("\n✅ Database cleanup complete!")

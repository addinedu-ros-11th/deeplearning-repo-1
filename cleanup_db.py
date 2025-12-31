#!/usr/bin/env python3
import pymysql

# DB connection info from .env
DB_HOST = "database-1.chu0kq8imwi9.ap-northeast-2.rds.amazonaws.com"
DB_PORT = 3306
DB_USER = "root"
DB_PASSWORD = "Q!w2e3r4t5"
DB_NAME = "smart_cart_db"

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

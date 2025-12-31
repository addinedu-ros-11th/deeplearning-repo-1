#!/usr/bin/env python3
"""
Fix duplicate cart items issue
Run this script to consolidate duplicate cart items and add unique constraint
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from database.db_handler import DBHandler
from common.config import config


def main():
    print("=" * 60)
    print("Fixing Duplicate Cart Items Issue")
    print("=" * 60)

    if not config:
        print("❌ Failed to load configuration")
        return 1

    try:
        db = DBHandler(config.db.aws_rds)
        print("✓ Connected to database")

        # Read SQL script
        sql_file = Path(__file__).parent / "fix_duplicate_cart_items.sql"
        with open(sql_file, "r", encoding="utf-8") as f:
            sql_script = f.read()

        print("\n📝 Analyzing current cart_items...")

        # Check for duplicates first
        check_sql = """
        SELECT 
            session_id,
            product_id,
            COUNT(*) as count
        FROM cart_items
        GROUP BY session_id, product_id
        HAVING COUNT(*) > 1
        """
        duplicates = db.fetch_all(check_sql)

        if duplicates:
            print(f"  ⚠ Found {len(duplicates)} product(s) with duplicate entries")
            for dup in duplicates[:5]:  # Show first 5
                print(
                    f"    - Session {dup['session_id']}, Product {dup['product_id']}: {dup['count']} rows"
                )
            if len(duplicates) > 5:
                print(f"    ... and {len(duplicates) - 5} more")
        else:
            print("  ✓ No duplicates found")

        # Check if constraint exists
        constraint_check = """
        SELECT COUNT(*) as count
        FROM INFORMATION_SCHEMA.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
        AND TABLE_NAME = 'cart_items'
        AND INDEX_NAME = 'unique_session_product'
        """
        constraint_result = db.fetch_one(constraint_check)
        constraint_exists = (
            constraint_result["count"] > 0 if constraint_result else False
        )

        if constraint_exists:
            print("  ℹ Unique constraint already exists")
        else:
            print("  ⚠ Unique constraint missing - will be added")

        # Execute migration if needed
        if duplicates or not constraint_exists:
            print("\n📝 Executing migration...")

            # Get connection from DBHandler
            conn = db._get_connection()

            try:
                with conn.cursor() as cursor:
                    # Execute the script statement by statement
                    statements = []
                    current_statement = []

                    for line in sql_script.split("\n"):
                        line = line.strip()

                        # Skip empty lines and comments
                        if not line or line.startswith("--"):
                            continue

                        current_statement.append(line)

                        # If line ends with semicolon, it's end of statement
                        if line.endswith(";"):
                            full_statement = " ".join(current_statement)
                            statements.append(full_statement)
                            current_statement = []

                    # Execute each statement
                    for i, statement in enumerate(statements, 1):
                        try:
                            cursor.execute(statement)
                            print(f"  ✓ Step {i} completed")
                        except Exception as e:
                            error_msg = str(e).lower()
                            if (
                                "already exists" in error_msg
                                or "duplicate key name" in error_msg
                            ):
                                print(f"  ℹ Step {i}: Already exists - skipped")
                            else:
                                print(f"  ⚠ Step {i} warning: {e}")

                conn.commit()
                print("  ✓ Migration executed successfully")

            except Exception as e:
                print(f"  ❌ Migration error: {e}")
                conn.rollback()
                raise
        else:
            print("\n✓ No migration needed - database is already clean")

        print("\n" + "=" * 60)
        print("✅ Migration completed successfully!")
        print("=" * 60)
        print("\nChanges made:")
        print("  1. Consolidated duplicate cart items by product_id")
        print("  2. Added UNIQUE constraint on (session_id, product_id)")
        print("  3. Future cart item additions will use ON DUPLICATE KEY UPDATE")
        print("\nYou can now run the system without duplicate item issues.")

        return 0

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

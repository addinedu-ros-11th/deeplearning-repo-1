-- Fix duplicate cart items and add unique constraint
-- Run this script to resolve the duplicate cart items issue
-- Compatible with the actual DB schema (bigint IDs)

-- Note: Replace 'smart_cart_db' with your actual database name if different
USE smart_cart_db;

-- Step 1: Check if unique constraint already exists
SET @constraint_exists = (
    SELECT COUNT(*)
    FROM INFORMATION_SCHEMA.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'cart_items'
    AND INDEX_NAME = 'unique_session_product'
);

-- Step 2: Consolidate duplicate cart items by merging quantities
-- Only proceed if there are duplicates
CREATE TEMPORARY TABLE IF NOT EXISTS temp_cart_items AS
SELECT 
    session_id,
    product_id,
    SUM(quantity) as total_quantity,
    MIN(added_at) as earliest_added_at,
    MIN(item_id) as keep_item_id
FROM cart_items
GROUP BY session_id, product_id
HAVING COUNT(*) > 1 OR @constraint_exists = 0;

-- Step 3: For each duplicate group, delete all rows and re-insert consolidated version
-- This ensures we have clean data before adding the constraint
DELETE ci FROM cart_items ci
INNER JOIN temp_cart_items t 
    ON ci.session_id = t.session_id 
    AND ci.product_id = t.product_id;

-- Step 4: Insert consolidated items
INSERT INTO cart_items (session_id, product_id, quantity, added_at)
SELECT session_id, product_id, total_quantity, earliest_added_at
FROM temp_cart_items;

-- Step 5: Add unique constraint to prevent future duplicates (if not exists)
SET @sql = IF(
    @constraint_exists = 0,
    'ALTER TABLE cart_items ADD UNIQUE KEY unique_session_product (session_id, product_id)',
    'SELECT "Unique constraint already exists - skipping" AS status'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Step 6: Clean up
DROP TEMPORARY TABLE IF EXISTS temp_cart_items;

-- Final verification
SELECT 
    'Migration completed!' as status,
    COUNT(*) as total_cart_items,
    COUNT(DISTINCT CONCAT(session_id, '-', product_id)) as unique_combinations
FROM cart_items;

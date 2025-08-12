#!/usr/bin/env python3
"""
Script to update the database schema to match the latest code.
"""

import sqlite3
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_db_schema():
    """Update the database schema to match the latest code"""
    # Get database path
    current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_dir = os.path.join(current_dir, "database")
    db_path = os.path.join(db_dir, "paper_trading.db")
    
    logger.info(f"Updating database schema at: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if we need to update the schema
        cursor.execute("PRAGMA table_info(paper_portfolio)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Check if we need to rename usdt_balance to usdc_balance
        if "usdt_balance" in columns and "usdc_balance" not in columns:
            logger.info("Renaming usdt_balance to usdc_balance")
            cursor.execute("ALTER TABLE paper_portfolio RENAME COLUMN usdt_balance TO usdc_balance")

        # Check if we need to add usdt_balance
        if "usdt_balance" not in columns:
            logger.info("Adding usdt_balance column")
            cursor.execute("ALTER TABLE paper_portfolio ADD COLUMN usdt_balance REAL DEFAULT 0.0")
        
        # Check if we need to add eth_balance
        if "eth_balance" not in columns:
            logger.info("Adding eth_balance column")
            cursor.execute("ALTER TABLE paper_portfolio ADD COLUMN eth_balance REAL DEFAULT 0.0")
        
        # Check if we need to add sol_balance
        if "sol_balance" not in columns:
            logger.info("Adding sol_balance column")
            cursor.execute("ALTER TABLE paper_portfolio ADD COLUMN sol_balance REAL DEFAULT 0.0")
        
        # Commit changes
        conn.commit()
        logger.info("✅ Database schema updated successfully")
        
        # Verify the schema
        cursor.execute("PRAGMA table_info(paper_portfolio)")
        columns = [column[1] for column in cursor.fetchall()]
        logger.info(f"Updated paper_portfolio columns: {columns}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error updating database schema: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    update_db_schema()

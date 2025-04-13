# utils.py - Utility functions for the Medical Report Extractor

import sqlite3
import os
import logging
from typing import Optional, Dict, Any # Added Dict, Any
from datetime import datetime
from src import config

logger = logging.getLogger(__name__) # Use module-specific logger

# Get the file paths from the configuration file.
CPT_DB_PATH = config.CPT_DB_PATH
ICD10_DB_PATH = config.ICD10_DB_PATH

# --- Database Functions ---

def create_connection(db_path: str): # Modified to accept path
    """ Create a database connection to the SQLite database specified by db_path """
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        # logger.info(f"Successfully connected to database: {db_path}") # Log might be too verbose here
        # Enable foreign keys for every connection
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except sqlite3.Error as e:
        logger.error(f"Database connection error to '{db_path}': {e}")
    return conn

def get_cpt_description(conn, cpt_code: Optional[str]) -> Optional[str]:
    """ Query Procedures table for a CPT code, return description if found.
        Assumes conn is connected to the CPT Database (MedicalCoding.db).
    """
    if not conn or not cpt_code:
        logger.debug("Skipping CPT validation: No connection or CPT code provided.")
        return None # Cannot validate without connection or code

    clean_cpt_code = cpt_code.strip()
    if not clean_cpt_code:
        logger.debug("Skipping CPT validation: CPT code is empty after stripping.")
        return None

    # Assuming the CPT DB has a 'Procedures' table with 'Code' and 'Description' columns [cite: 55]
    sql = ''' SELECT Description FROM Procedures WHERE Code = ? '''
    cur = None # Initialize cursor
    description = None
    try:
        cur = conn.cursor()
        cur.execute(sql, (clean_cpt_code,)) # Use tuple for parameter
        result = cur.fetchone() # fetchone() gets the first row or None
        if result:
            description = result[0] # Get the first column (Description)
            logger.debug(f"CPT '{clean_cpt_code}' found in CPT DB. Description: '{description}'")
        else:
             logger.debug(f"CPT '{clean_cpt_code}' not found in CPT Procedures table.")

    except sqlite3.Error as e:
        logger.error(f"Error during CPT query for code '{clean_cpt_code}': {e}")
    finally:
        if cur:
            cur.close() # Close cursor

    return description

# --- NEW FUNCTION for ICD-10 Lookup ---
def get_icd10_details(conn, icd_code: Optional[str]) -> Optional[Dict[str, Any]]:
    """
    Query the 'diagnoses' table in the ICD-10 database for a code.
    Returns a dictionary with code details if found, otherwise None.
    Assumes conn is connected to the ICD-10 Database (icd10cm_database.db).
    """
    if not conn or not icd_code:
        logger.debug("Skipping ICD-10 lookup: No connection or ICD code provided.")
        return None

    clean_icd_code = icd_code.strip().upper() # Standardize to upper case maybe?
    if not clean_icd_code:
         logger.debug("Skipping ICD-10 lookup: ICD code is empty after stripping.")
         return None

    # Query the 'diagnoses' table created earlier
    sql = ''' SELECT code, description, is_leaf_node FROM diagnoses WHERE code = ? '''
    cur = None
    details = None
    try:
        cur = conn.cursor()
        cur.execute(sql, (clean_icd_code,))
        result = cur.fetchone()
        if result:
            details = {
                'code': result[0],
                'description': result[1],
                'is_leaf_node': bool(result[2]) # Convert INTEGER back to Boolean
            }
            logger.debug(f"ICD-10 '{clean_icd_code}' found in ICD-10 DB. Details: {details}")
        else:
            logger.debug(f"ICD-10 '{clean_icd_code}' not found in ICD-10 diagnoses table.")

    except sqlite3.Error as e:
        logger.error(f"Error during ICD-10 query for code '{clean_icd_code}': {e}")
    finally:
        if cur:
            cur.close()

    return details

# --- Other Utility Functions ---

def validate_date(date_str: Optional[str]) -> bool:
    """Validate if a string is in a valid date format."""
    if not date_str:
        return False
    # Example formats, add others if needed
    date_formats = ["%m/%d/%y", "%m/%d/%Y"]
    for fmt in date_formats:
        try:
            datetime.strptime(date_str, fmt)
            return True
        except ValueError:
            continue
    return False

# Add other general utility functions here if needed in the future
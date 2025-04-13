import sqlite3
import os

# --- Configuration ---
db_filename = 'icd10cm_database.db'
# ---

def create_tables(db_file):
    """Creates the ICD-10 CM tables in the specified SQLite database file."""

    # Check if DB already exists, optionally skip creation or delete first
    # For simplicity, we'll just connect/create and assume we want tables created if missing
    # More robust logic could check if tables already exist

    conn = None # Initialize connection variable
    try:
        print(f"Connecting to database: {db_file}")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        print("Connection successful.")

        # --- Enable Foreign Key support ---
        # This is crucial for enforcing relationships
        cursor.execute("PRAGMA foreign_keys = ON;")
        print("Foreign key support enabled.")

        # --- Define CREATE TABLE statements ---

        # Chapters Table
        sql_create_chapters_table = """
        CREATE TABLE IF NOT EXISTS chapters (
            chapter_num TEXT PRIMARY KEY,
            description TEXT
        );"""

        # Sections Table
        sql_create_sections_table = """
        CREATE TABLE IF NOT EXISTS sections (
            section_id TEXT PRIMARY KEY,
            description TEXT,
            chapter_num TEXT,
            FOREIGN KEY (chapter_num) REFERENCES chapters (chapter_num)
                ON DELETE CASCADE ON UPDATE CASCADE
        );""" # Added ON DELETE/UPDATE CASCADE for demo, adjust as needed

        # Diagnoses Table
        sql_create_diagnoses_table = """
        CREATE TABLE IF NOT EXISTS diagnoses (
            code TEXT PRIMARY KEY,
            description TEXT,
            section_id TEXT,
            parent_code TEXT,
            is_leaf_node INTEGER DEFAULT 1,
            placeholder INTEGER DEFAULT 0,
            category TEXT,
            first_letter TEXT,
            FOREIGN KEY (section_id) REFERENCES sections (section_id)
                ON DELETE SET NULL ON UPDATE CASCADE,
            FOREIGN KEY (parent_code) REFERENCES diagnoses (code)
                ON DELETE SET NULL ON UPDATE CASCADE
        );""" # Used INTEGER for boolean flags, default placeholder=0

        # Notes Table
        sql_create_notes_table = """
        CREATE TABLE IF NOT EXISTS notes (
            note_id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            note_type TEXT,
            note_text TEXT,
            FOREIGN KEY (code) REFERENCES diagnoses (code)
                ON DELETE CASCADE ON UPDATE CASCADE
        );"""

        # --- Execute CREATE TABLE statements ---
        print("Creating table: chapters...")
        cursor.execute(sql_create_chapters_table)
        print("Creating table: sections...")
        cursor.execute(sql_create_sections_table)
        print("Creating table: diagnoses...")
        cursor.execute(sql_create_diagnoses_table)
        print("Creating table: notes...")
        cursor.execute(sql_create_notes_table)

        # --- Optionally create Indexes here (or after population) ---
        # Example: cursor.execute("CREATE INDEX IF NOT EXISTS idx_diag_category ON diagnoses(category);")
        # Example: cursor.execute("CREATE INDEX IF NOT EXISTS idx_notes_code ON notes(code);")
        # It's often better to create indexes *after* bulk data loading for performance.

        # --- Commit changes ---
        conn.commit()
        print("Tables created successfully (if they didn't already exist).")

    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # --- Close connection ---
        if conn:
            conn.close()
            print("Database connection closed.")

# --- Main execution ---
if __name__ == "__main__":
    create_tables(db_filename)
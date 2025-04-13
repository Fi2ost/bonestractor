import sqlite3
import os
import sys

# Try to import lxml.etree
try:
    from lxml import etree as ET
    print("Using lxml parser.")
except ImportError:
    print("ERROR: lxml library not found.")
    print("Please install it using 'pip install lxml' before running this script.")
    sys.exit(1)

# --- Configuration ---
db_filename = 'icd10cm_database.db' # The database file created previously
xml_file_path = 'icd10cm_tabular_2025.xml' # Your XML data file
# ---

# --- Helper Function ---
def get_text(element, tag_name):
    """Safely gets stripped text content of a direct child tag."""
    child = element.find(tag_name)
    if child is not None and child.text:
        return child.text.strip()
    return None

# --- Core Processing Functions ---

def process_notes(cursor, diag_code, diag_element):
    """Finds and inserts all note types associated with a diagnosis."""
    note_tags = [
        'inclusionTerm', 'sevenChrNote', 'includes', 'excludes1',
        'excludes2', 'codeFirst', 'useAdditionalCode', 'codeAlso',
        'notes', 'instruction' # Add any other relevant note-like tags
    ]
    notes_to_insert = []
    for note_type in note_tags:
        # Find all elements of this note type directly under the diag element
        for note_element in diag_element.findall(note_type):
            # Some note tags (like includes, excludes1 etc.) contain child <note> tags
            # Others might have text directly or nested structure.
            # This logic handles notes nested within <note> tags common in the schema.
            for actual_note in note_element.findall('note'):
                 if actual_note.text:
                    note_text = actual_note.text.strip()
                    if note_text:
                        notes_to_insert.append((diag_code, note_type, note_text))
            # Handle cases where the note text might be directly in the element (less common for these tags)
            # Or handle other complex note structures if needed based on XSD/XML review

    if notes_to_insert:
        try:
            sql = "INSERT INTO notes (code, note_type, note_text) VALUES (?, ?, ?)"
            cursor.executemany(sql, notes_to_insert)
            # print(f"  Inserted {len(notes_to_insert)} notes for code {diag_code}")
        except sqlite3.Error as e:
            print(f"  ERROR inserting notes for code {diag_code}: {e}")


def process_diag(cursor, diag_element, section_id, parent_code):
    """
    Processes a <diag> element, inserts it, handles notes, and recurses for children.
    Returns the code of the processed diagnosis.
    """
    code = get_text(diag_element, 'name')
    description = get_text(diag_element, 'desc')

    if not code:
        # print("  Skipping diag element with no code.")
        return None # Cannot process without a code

    # Derive other fields
    first_letter = code[0] if code else None
    category = code[:3] if code and len(code) >= 3 else code
    placeholder_attr = diag_element.get('placeholder') # Get attribute value
    placeholder = 1 if placeholder_attr and placeholder_attr.lower() == 'true' else 0

    # Check for child <diag> elements to determine if it's a leaf node
    child_diags = diag_element.findall('diag')
    is_leaf_node = 0 if child_diags else 1

    try:
        sql = """
        INSERT INTO diagnoses
        (code, description, section_id, parent_code, is_leaf_node, placeholder, category, first_letter)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (code, description, section_id, parent_code, is_leaf_node, placeholder, category, first_letter))
        # print(f" Processed diag: {code} - {description[:30]}...")
    except sqlite3.IntegrityError:
        print(f"  WARNING: Code {code} already exists or other integrity error. Skipping insert.")
        # If duplicates are expected and okay, could use INSERT OR IGNORE or handle differently
        return code # Still return code so children can be processed if needed
    except sqlite3.Error as e:
        print(f"  ERROR inserting diag {code}: {e}")
        return None # Stop processing this branch on error

    # Process associated notes for this diagnosis code
    process_notes(cursor, code, diag_element)

    # Recursively process child diagnoses
    if not is_leaf_node:
        for child_diag_element in child_diags:
            process_diag(cursor, child_diag_element, section_id, code) # Pass current code as parent_code

    return code

def process_section(cursor, section_element, chapter_num):
    """Processes a <section>, inserts it, and processes its child diagnoses."""
    section_id = section_element.get('id') # Get 'id' attribute
    description = get_text(section_element, 'desc')

    if not section_id:
        print("  Skipping section with no id attribute.")
        return None

    try:
        sql = "INSERT INTO sections (section_id, description, chapter_num) VALUES (?, ?, ?)"
        cursor.execute(sql, (section_id, description, chapter_num))
        # print(f"  Processed section: {section_id} - {description[:30]}...")
    except sqlite3.IntegrityError:
         print(f"  WARNING: Section {section_id} already exists or other integrity error. Skipping insert.")
         # Allow processing children even if section exists
    except sqlite3.Error as e:
        print(f"  ERROR inserting section {section_id}: {e}")
        return None # Stop processing this section on error

    # Process direct child <diag> elements within this section
    for diag_element in section_element.findall('diag'):
        process_diag(cursor, diag_element, section_id, None) # No parent_code for top-level diags in section

    return section_id

def process_chapter(cursor, chapter_element):
    """Processes a <chapter>, inserts it, and processes its child sections/diagnoses."""
    chapter_num = get_text(chapter_element, 'name')
    description = get_text(chapter_element, 'desc')

    if not chapter_num:
        print("Skipping chapter with no name tag.")
        return None

    try:
        sql = "INSERT INTO chapters (chapter_num, description) VALUES (?, ?)"
        cursor.execute(sql, (chapter_num, description))
        print(f"Processing chapter: {chapter_num} - {description[:40]}...")
    except sqlite3.IntegrityError:
         print(f"  WARNING: Chapter {chapter_num} already exists or other integrity error. Skipping insert.")
         # Allow processing children even if chapter exists
    except sqlite3.Error as e:
        print(f"  ERROR inserting chapter {chapter_num}: {e}")
        return None # Stop processing this chapter on error

    # Process child <section> elements
    for section_element in chapter_element.findall('section'):
        process_section(cursor, section_element, chapter_num)

    # Process any direct child <diag> elements (if schema allows)
    # (Check XSD - usually diags are within sections, but handle just in case)
    for diag_element in chapter_element.findall('diag'):
         print(f"  Found direct diag {get_text(diag_element, 'name')} under chapter {chapter_num}. Processing...")
         process_diag(cursor, diag_element, None, None) # No section_id or parent_code

    return chapter_num


def populate_database(db_file, xml_file):
    """Parses the XML and populates the SQLite database tables."""
    if not os.path.exists(xml_file):
        print(f"ERROR: XML file not found at '{xml_file}'")
        return
    if not os.path.exists(db_file):
        print(f"ERROR: Database file not found at '{db_file}'. Run the creation script first.")
        return

    conn = None
    try:
        print(f"Connecting to database: {db_file}")
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        print("Connection successful.")

        # Enable Foreign Keys
        cursor.execute("PRAGMA foreign_keys = ON;")
        print("Foreign key support enabled.")

        print(f"Starting XML parsing: {xml_file}")
        # Use iterparse for potentially large files, but parse() is simpler for moderate size
        # For potentially very large files, iterparse might be better for memory.
        tree = ET.parse(xml_file)
        root = tree.getroot()
        print("XML parsed. Starting data population...")

        # Find all <chapter> elements directly under the root
        chapters = root.findall('chapter')
        if not chapters:
             print("ERROR: No <chapter> elements found directly under the root.")
             # Maybe the structure is different? Check root tag: root.tag
             # If root tag is different, adjust findall accordingly. e.g. root.findall('.//chapter')
             return

        for chapter_element in chapters:
            process_chapter(cursor, chapter_element)

        # --- Commit all changes ---
        print("Committing changes to database...")
        conn.commit()
        print("Data population completed successfully.")

    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        if conn:
            conn.rollback() # Rollback any partial changes on error
    except sqlite3.Error as e:
        print(f"Database error during population: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"An unexpected error occurred during population: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

# --- Main execution ---
if __name__ == "__main__":
    populate_database(db_filename, xml_file_path)
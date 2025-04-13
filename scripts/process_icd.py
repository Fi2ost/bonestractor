import pandas as pd
import os
import sys # To check Python version if needed, and exit

# Try to import lxml.etree
try:
    from lxml import etree as ET
    print("Using lxml parser.")
except ImportError:
    print("ERROR: lxml library not found.")
    print("Please install it using 'pip install lxml' before running this script.")
    sys.exit(1) # Exit if lxml is required and not found

# --- Configuration ---
# *** Corrected filename extension to .xml ***
xml_file_path = 'icd10cm_tabular_2025.xml'
# ---

def extract_icd_data_to_dataframe(filename):
    """
    Parses the ICD-10-CM XML file and extracts diagnosis codes,
    descriptions, first letter, and 3-char category into a pandas DataFrame.
    """
    if not os.path.exists(filename):
        print(f"ERROR: File not found at '{filename}'")
        print("Please ensure the file exists in the same directory as the script,")
        print("or update the 'xml_file_path' variable in the script.")
        return None

    print(f"Parsing XML file: {filename}...")
    data_rows = []

    try:
        # Parse the entire XML file using lxml
        tree = ET.parse(filename)
        root = tree.getroot()

        # Use XPath to find all 'diag' elements anywhere in the tree
        all_diag_elements = root.xpath('.//diag')
        print(f"Found {len(all_diag_elements)} <diag> elements. Processing...")

        processed_count = 0
        for diag_element in all_diag_elements:
            # Find direct child 'name' and 'desc' elements
            name_el = diag_element.find('name')
            desc_el = diag_element.find('desc')

            code = name_el.text.strip() if name_el is not None and name_el.text else None
            desc = desc_el.text.strip() if desc_el is not None and desc_el.text else None

            # Only include rows that have a code
            if code:
                first_letter = code[0]
                # Get category (first 3 chars), handle codes potentially shorter than 3
                category = code[:3] if len(code) >= 3 else code

                data_rows.append({
                    'code': code,
                    'description': desc,
                    'first_letter': first_letter,
                    'category': category
                })
                processed_count += 1

        print(f"Successfully processed {processed_count} codes.")

    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred during parsing: {e}")
        return None

    # Create pandas DataFrame
    if data_rows:
        print("Creating pandas DataFrame...")
        df = pd.DataFrame(data_rows)
        return df
    else:
        print("No data rows were extracted.")
        return None

# --- Main execution ---
# --- Keep the imports and the extract_icd_data_to_dataframe function ---
# ... (lxml, pandas imports, function definition) ...

# --- Main execution ---
if __name__ == "__main__":
    icd_dataframe = extract_icd_data_to_dataframe(xml_file_path)

    if icd_dataframe is not None:
        print("DataFrame created successfully. Launching PandasGUI...")

        # --- NEW PART: Launch PandasGUI ---
        try:
            from pandasgui import show
            # This will open the GUI in a separate window
            show(icd_dataframe)
            print("PandasGUI window opened. Close the GUI window to end the script.")
        except ImportError:
            print("\nERROR: pandasgui library not found or import failed.")
            print("Please ensure it is installed correctly ('pip install pandasgui').")
        except Exception as e:
            print(f"\nAn error occurred launching PandasGUI: {e}")
        # --- End of NEW PART ---

    else:
        print("\nFailed to create DataFrame.")
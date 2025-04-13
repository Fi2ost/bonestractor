import os

# Define the base directory for data
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')

# Define paths to specific data files
ICD10_XML_FILE = os.path.join(DATA_DIR, 'icd10cm_tabular_2025.xml')
CPT_DB_PATH = os.path.join(DATA_DIR, 'cpt.db')
ICD10_DB_PATH = os.path.join(DATA_DIR, 'icd10.db')
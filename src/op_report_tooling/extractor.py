# extractor.py - Core extraction logic for the Medical Report Extractor

import re
import logging
from typing import Optional, List # Make sure List is imported if needed elsewhere

# Import necessary components from other modules
# Import the NEW ProcessedDiagnosis structure along with others
from data_models import (
    OperativeReport, ProcedureInfo, PatientInfo, AdmissionInfo,
    ProviderInfo, DiagnosisInfo, ProcessedDiagnosis # Added ProcessedDiagnosis
)
from patterns import RegexPatterns
from config import CPT_DB_PATH, ICD10_DB_PATH
# Import BOTH database paths and the modified connection function,
# plus BOTH lookup functions
from utils import (
    create_connection, get_cpt_description, get_icd10_details

    #CPT_DB_PATH, ICD10_DB_PATH # Import path constants
)


logger = logging.getLogger(__name__)

# --- Define a simple regex pattern for potential ICD-10 codes ---
# This is basic: Letter (except U), Digit, Digit/Letter, optional dot and more chars.
# Needs refinement for more accuracy (e.g., handling specific chapter rules/lengths).
ICD10_CODE_PATTERN = r'\b([A-TV-Z][0-9][A-Z0-9](?:\.[A-Z0-9]{1,4})?)\b'
# ---

class MedicalReportExtractor:
    """Class to extract structured data from medical reports."""

    def __init__(self, report_text: str):
        """Initialize with the report text to parse."""
        self.report_text = report_text
        # Initialize with the new DiagnosisInfo structure
        self.report = OperativeReport(diagnoses=DiagnosisInfo(processed_diagnoses=[]))


    def extract_all(self) -> OperativeReport:
        """Extract all data, connecting to and using both databases."""
        cpt_conn = None # Connection for CPT DB
        icd10_conn = None # Connection for ICD-10 DB

        try:
            # --- Create connections to BOTH databases ---
            logger.info(f"Attempting to connect to CPT DB: {CPT_DB_PATH}")
            cpt_conn = create_connection(CPT_DB_PATH)
            logger.info(f"Attempting to connect to ICD-10 DB: {ICD10_DB_PATH}")
            icd10_conn = create_connection(ICD10_DB_PATH)
            # ---

            # Check if connections were successful before proceeding
            if cpt_conn is None:
                 logger.warning("Could not connect to CPT DB. CPT validation will be skipped.")
            if icd10_conn is None:
                 logger.warning("Could not connect to ICD-10 DB. ICD-10 validation will be skipped.")


            # Run all extraction methods, passing the appropriate connection
            self.extract_patient_info()
            self.extract_insurance_info() # Placeholder
            self.extract_admission_info()
            self.extract_provider_info()
            # Pass the ICD-10 connection to extract_diagnoses
            self.extract_diagnoses(icd10_conn=icd10_conn) # Pass ICD-10 conn
            # Pass the CPT connection to extract_procedures
            self.extract_procedures(cpt_conn=cpt_conn) # Pass CPT conn
            self.extract_misc_info()

            return self.report
        except Exception as e:
            logger.error(f"Error during main extraction process: {str(e)}", exc_info=True)
            raise
        finally:
            # --- Ensure BOTH connections are closed ---
            if cpt_conn:
                cpt_conn.close()
                logger.info("CPT Database connection closed.")
            if icd10_conn:
                icd10_conn.close()
                logger.info("ICD-10 Database connection closed.")
            # ---

    def extract_with_pattern(self, pattern: str, group_name: str = None) -> Optional[str]:
        """Extract data using a regex pattern (no changes needed here)."""
        # ... (keep existing implementation) ...
        try:
            match = re.search(pattern, self.report_text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
            if match:
                if group_name:
                    return match.group(group_name).strip() if group_name in match.groupdict() else None
                elif match.groups():
                    return match.group(1).strip()
                else:
                    return match.group(0).strip() # Return the whole match if no groups
            return None
        except Exception as e:
            logger.warning(f"Error extracting with pattern '{pattern}': {str(e)}")
            return None

    # --- Methods for patient, insurance, admission, provider, misc (no changes needed) ---
    def extract_patient_info(self) -> None:
        """Extract patient demographic information."""
        # ... (keep existing implementation) ...
        logger.info("Extracting patient information")
        self.report.patient = PatientInfo()
        name_match = self.extract_with_pattern(RegexPatterns.PATIENT_NAME, "name")
        if name_match:
            name_parts = name_match.split(',')
            self.report.patient.last_name = name_parts[0].strip() if len(name_parts) > 0 else None
            if len(name_parts) > 1:
                first_middle = name_parts[1].strip().split()
                self.report.patient.first_name = first_middle[0] if first_middle else None
                self.report.patient.middle_name = ' '.join(first_middle[1:]) if len(first_middle) > 1 else None
        self.report.patient.gender = self.extract_with_pattern(RegexPatterns.GENDER, "gender")
        self.report.patient.date_of_birth = self.extract_with_pattern(RegexPatterns.DOB, "dob")
        self.report.patient.unit_number = self.extract_with_pattern(RegexPatterns.UNIT_NUMBER, "unit")
        self.report.patient.account_number = self.extract_with_pattern(RegexPatterns.ACCOUNT_NUMBER, "account")


    def extract_insurance_info(self) -> None:
         """Extract insurance information (placeholder)."""
         logger.info("Insurance information extraction skipped (no patterns).")
         pass

    def extract_admission_info(self) -> None:
        """Extract admission, surgery, and status information."""
        # ... (keep existing implementation) ...
        logger.info("Extracting admission and surgery information")
        self.report.admission = AdmissionInfo()
        self.report.admission.date_of_admission = self.extract_with_pattern(RegexPatterns.ADMISSION_DATE, "date")
        self.report.admission.date_of_surgery = self.extract_with_pattern(RegexPatterns.SURGERY_DATE, "date")
        self.report.admission.status = self.extract_with_pattern(RegexPatterns.REPORT_STATUS, "status")
        venue_match = re.match(r"^([^\n]+)", self.report_text)
        if venue_match:
            self.report.admission.surgery_venue = venue_match.group(1).strip()
        injury_context = re.search(r"Indications:.*?sustained.*?after\s+(.*?)\.", self.report_text, re.IGNORECASE | re.DOTALL)
        if injury_context:
            injury_desc = injury_context.group(1).strip()
            self.report.admission.date_of_injury = f"Inferred from context: '{injury_desc}'"


    def extract_provider_info(self) -> None:
        """Extract provider information."""
        # ... (keep existing implementation) ...
        logger.info("Extracting provider information")
        self.report.provider = ProviderInfo()
        self.report.provider.surgeon = self.extract_with_pattern(RegexPatterns.SURGEON, "surgeon")
        self.report.provider.first_assistant = self.extract_with_pattern(RegexPatterns.FIRST_ASSISTANT, "assistant")
        self.report.provider.attending_physician = self.extract_with_pattern(RegexPatterns.ATTENDING, "attending")


    # --- MODIFIED extract_diagnoses ---
    def extract_diagnoses(self, icd10_conn) -> None: # Accepts ICD-10 DB connection
        """
        Extracts diagnoses, attempts to identify ICD-10 codes, validates
        against the ICD-10 DB, and stores structured results.
        """
        logger.info("Extracting and validating diagnoses using ICD-10 DB")
        # Initialize with the new DiagnosisInfo structure
        self.report.diagnoses = DiagnosisInfo(processed_diagnoses=[])

        # Use DOTALL flag in regex search for multi-line diagnoses section
        diagnoses_section_match = re.search(
            RegexPatterns.PRE_DIAGNOSIS, self.report_text,
            re.IGNORECASE | re.DOTALL
        )

        if not diagnoses_section_match:
            logger.warning("No pre-procedure diagnosis section found.")
            return # Exit if no section found

        diagnoses_text = diagnoses_section_match.group("diagnoses").strip()
        # Split by newline, strip whitespace, filter empty lines
        raw_lines = [line.strip() for line in diagnoses_text.split('\n') if line.strip()]

        if not raw_lines:
            logger.warning("Pre-procedure diagnosis section found but contained no text lines.")
            return

        logger.info(f"Processing {len(raw_lines)} raw diagnosis lines...")

        processed_list: List[ProcessedDiagnosis] = [] # Use the defined TypedDict

        for line in raw_lines:
            original_text = line
            # Simple cleanup: remove leading digits/periods/spaces (optional)
            cleaned_text = re.sub(r"^\s*\d+\.?\s*", "", original_text).strip()

            identified_code: Optional[str] = None
            is_valid: bool = False
            db_description: Optional[str] = None
            is_leaf: Optional[bool] = None

            # Attempt to find an ICD-10 code pattern in the cleaned text
            # Find *all* potential matches in the line
            potential_codes = re.findall(ICD10_CODE_PATTERN, cleaned_text)

            # Use the first found potential code for validation (or refine logic)
            if potential_codes:
                code_to_check = potential_codes[0] # Using the first match
                identified_code = code_to_check
                logger.debug(f"Potential ICD-10 code '{identified_code}' found in line: '{original_text}'")

                # Validate against DB if connection is available
                if icd10_conn:
                    icd10_details = get_icd10_details(icd10_conn, identified_code)
                    if icd10_details:
                        is_valid = True
                        db_description = icd10_details.get('description')
                        is_leaf = icd10_details.get('is_leaf_node')
                        logger.info(f"  Code '{identified_code}' validated. DB Desc: '{db_description}'")
                    else:
                        logger.warning(f"  Code '{identified_code}' NOT found in ICD-10 database.")
                else:
                     logger.warning("  ICD-10 DB connection not available, skipping validation.")
            else:
                 logger.debug(f"No ICD-10 code pattern matched in line: '{original_text}'")


            # Store the processed result
            processed_entry: ProcessedDiagnosis = {
                'original_text': original_text,
                'identified_code': identified_code,
                'is_valid_icd10': is_valid,
                'icd10_description': db_description,
                'is_leaf_node': is_leaf
            }
            processed_list.append(processed_entry)

        # Update the report object
        self.report.diagnoses.processed_diagnoses = processed_list
        logger.info(f"Finished processing diagnoses. Stored {len(processed_list)} entries.")


    # --- MODIFIED extract_procedures ---
    def extract_procedures(self, cpt_conn) -> None: # Renamed db_conn to cpt_conn
        """
        Extracts procedures information including CPT codes and validates
        CPT codes against the CPT DB.
        """
        logger.info("Extracting procedures and validating CPT codes using CPT DB")
        self.report.procedures = [] # Initialize procedures list

        procedures_section = re.search(
             r"Procedures performed:\s*(.*?)(?=\n\s*(?:Primary Surgeon:|Technique/Procedure:|Complications:|Estimated blood loss|Implants|Recommendations)|$)",
             self.report_text,
             re.DOTALL | re.IGNORECASE
         )

        if procedures_section:
            procedures_text = procedures_section.group(1).strip()
            procedures_raw = [line.strip() for line in procedures_text.split('\n') if line.strip()]

            for proc_line in procedures_raw:
                proc = re.sub(r"^\s*\d+\.?\s*", "", proc_line).strip()
                if not proc: continue

                proc_obj = ProcedureInfo()
                cpt_match = re.search(r"(.*?)\s+(\d{5})$", proc)
                extracted_name = None

                if cpt_match:
                    extracted_name = cpt_match.group(1).strip()
                    proc_obj.cpt_code = cpt_match.group(2).strip()
                    logger.debug(f"Potential CPT code '{proc_obj.cpt_code}' found for procedure: '{extracted_name}'")

                    # *** CPT Validation Call (Uses CPT DB connection) ***
                    if cpt_conn and proc_obj.cpt_code:
                        authoritative_desc = get_cpt_description(cpt_conn, proc_obj.cpt_code) # Uses cpt_conn
                        if authoritative_desc is not None:
                            logger.info(f"CPT {proc_obj.cpt_code}: Validated. Using DB description.")
                            proc_obj.name = authoritative_desc # Overwrite name if validated
                        else:
                            logger.warning(f"CPT {proc_obj.cpt_code}: Not found in CPT DB. Keeping originally extracted name: '{extracted_name}'")
                            proc_obj.name = extracted_name # Keep original if not validated
                    else:
                         # No connection or no CPT code, keep original name
                         proc_obj.name = extracted_name
                         if not cpt_conn: logger.warning(" CPT DB connection not available, skipping CPT validation.")
                    # **************************************************

                else:
                    # No CPT code pattern matched, use whole line as name
                    proc_obj.name = proc
                    proc_obj.cpt_code = None
                    logger.debug(f"No CPT code pattern matched for procedure line: '{proc}'")

                # Determine side/region based on the final name
                proc_obj.side = self.determine_side(proc_obj.name if proc_obj.name else proc)
                proc_obj.region = self.determine_region(proc_obj.name if proc_obj.name else proc)

                self.report.procedures.append(proc_obj)

            logger.info(f"Processed {len(self.report.procedures)} procedures.")
        else:
            logger.warning("No procedures section found or matched in the report.")

    # --- Methods for determine_side, determine_region, extract_misc_info (no changes needed) ---
    def determine_side(self, text: str) -> Optional[str]:
        """Determine the side (left/right/bilateral) from text."""
        # ... (keep existing implementation) ...
        if not text: return None
        text_lower = text.lower()
        if "bilateral" in text_lower: return "Bilateral"
        if "left" in text_lower: return "Left"
        if "right" in text_lower: return "Right"
        return None

    def determine_region(self, text: str) -> Optional[str]:
        """Determine the anatomical region from text."""
        # ... (keep existing implementation, possibly refine later) ...
        if not text: return None
        text_lower = text.lower()
        regions = { "shoulder": "Shoulder", "clavicle": "Shoulder", "sternoclavicular": "Shoulder", "acromioclavicular": "Shoulder", "humerus": "Humerus", "elbow": "Elbow", "radius": "Forearm", "ulna": "Forearm", "forearm": "Forearm", "wrist": "Wrist", "carpal": "Wrist", "hand": "Hand", "hip": "Hip", "femur": "Femur", "femoral": "Femur", "knee": "Knee", "patella": "Knee", "tibia": "Tibia/Fibula", "tibial": "Tibia/Fibula", "fibula": "Tibia/Fibula", "ankle": "Ankle", "foot": "Foot", "tarsal": "Foot", "metatarsal": "Foot", "spine": "Spine", "vertebra": "Spine", "pelvis": "Pelvis", "skin": "Skin", "nerve": "Misc Nerve" }
        for key, region in regions.items():
            if key in text_lower:
                return region
        if "humerus" in text_lower:
            if "proximal" in text_lower or "head" in text_lower or "tuberosity" in text_lower: return "Shoulder"
            elif "distal" in text_lower or "supracondylar" in text_lower: return "Elbow"
            else: return "Humerus"
        return None

    def extract_misc_info(self) -> None:
        """Extract other miscellaneous information."""
        # ... (keep existing implementation) ...
        logger.info("Extracting miscellaneous information")
        self.report.complications = self.extract_with_pattern(RegexPatterns.COMPLICATIONS, "complications")
        self.report.estimated_blood_loss = self.extract_with_pattern(RegexPatterns.BLOOD_LOSS, "ebl")
        implant_match = re.search(RegexPatterns.IMPLANTS, self.report_text, re.IGNORECASE | re.DOTALL)
        self.report.implants = implant_match.group("implants").strip() if implant_match else None
        recommendations_match = re.search(RegexPatterns.RECOMMENDATIONS, self.report_text, re.IGNORECASE | re.DOTALL)
        self.report.recommendations = recommendations_match.group("recommendations").strip() if recommendations_match else None
# patterns.py - Contains regex patterns for data extraction

class RegexPatterns:
    """Class containing regex patterns for data extraction."""
    # Patient patterns
    PATIENT_NAME = r"^PATIENT:\s*(?P<name>[^\n\t]+?)\s*(?:UNIT|$)"
    GENDER = r"SEX:\s*(?P<gender>\w+)"
    DOB = r"DOB:\s*(?P<dob>[\d/]+)"
    UNIT_NUMBER = r"UNIT #:\s*(?P<unit>[^\n\t]+)"
    ACCOUNT_NUMBER = r"ACCOUNT#:\s*(?P<account>[^\n\t]+)"

    # Admission patterns
    ADMISSION_DATE = r"ADM DT:\s*(?P<date>[\d/]+)"
    SURGERY_DATE = r"^Start date:\s*(?P<date>[\d/]+)"
    SURGERY_TIME = r"^Start time:\s*(?P<time>\d+)"
    REPORT_STATUS = r"REPORT STATUS:\s*(?P<status>\w+)"

    # Provider patterns
    SURGEON = r"^(?:Primary Surgeon|AUTHOR):\s*(?P<surgeon>[^\n]+?)(?:\s+MD|$)"
    FIRST_ASSISTANT = r"Assistant\(s\):\s*(?P<assistant>[^\n]+)"
    ATTENDING = r"ATTEND:\s*(?P<attending>[^\n]+?)(?:\s+MD|$)"

    # Diagnosis patterns
    PRE_DIAGNOSIS = r"Pre-procedure diagnosis:\s*(?P<diagnoses>.*?)(?=Post-procedure diagnosis:|Procedures performed:|$)"

    # Procedure patterns
    PROCEDURES = r"Procedures performed:\s*(?P<procedures>.*?)(?=Technique/Procedure:|$)"
    CPT_CODE = r"(?P<procedure_name>.*?)\s+(?P<cpt>\d{5})\s*$"

    # Other patterns
    COMPLICATIONS = r"Complications:\s*(?P<complications>.*?)(?=\n)"
    BLOOD_LOSS = r"Estimated blood loss in ml's:\s*(?P<ebl>\d+)"
    IMPLANTS = r"Implant\(s\):\s*(?P<implants>.*?)(?=\n)"
    RECOMMENDATIONS = r"Recommendations:\s*(?P<recommendations>.*?)(?=\n\n|$)"
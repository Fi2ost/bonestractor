# models.py - Contains data structures for the Medical Report Extractor

from dataclasses import dataclass, field, asdict
# Make sure to import List, Optional, Dict, Any if not already imported
from typing import Optional, List, Dict, Any, TypedDict # Added TypedDict

@dataclass
class PatientInfo:
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    middle_name: Optional[str] = None
    gender: Optional[str] = None
    date_of_birth: Optional[str] = None
    unit_number: Optional[str] = None
    account_number: Optional[str] = None

@dataclass
class InsuranceInfo:
    primary_insurance: Optional[str] = None
    secondary_insurance: Optional[str] = None

@dataclass
class AdmissionInfo:
    date_of_admission: Optional[str] = None
    date_of_surgery: Optional[str] = None
    date_of_injury: Optional[str] = None
    place_of_injury: Optional[str] = None
    status: Optional[str] = None
    surgery_venue: Optional[str] = None
    global_period: Optional[str] = None
    global_ends: Optional[str] = None

@dataclass
class ProviderInfo:
    surgeon: Optional[str] = None
    first_assistant: Optional[str] = None
    e_and_m: Optional[str] = None
    date_of_consultation: Optional[str] = None
    attending_physician: Optional[str] = None

# --- NEW: Define structure for processed diagnosis ---
class ProcessedDiagnosis(TypedDict):
    original_text: str          # The raw line extracted from the report
    identified_code: Optional[str] # The potential ICD-10 code found
    is_valid_icd10: bool        # Flag indicating if code was found in our DB
    icd10_description: Optional[str] # Description from our DB if found
    is_leaf_node: Optional[bool] # From our DB if found
# --- END NEW ---

@dataclass
class DiagnosisInfo:
    # Store the processed list instead of just raw strings
    processed_diagnoses: List[ProcessedDiagnosis] = field(default_factory=list)
    # You could optionally keep the raw list too if needed elsewhere
    # raw_diagnoses: List[str] = field(default_factory=list)

@dataclass
class ProcedureInfo:
    name: Optional[str] = None
    cpt_code: Optional[str] = None # Will only contain CPT if found, name not overwritten unless CPT validated
    side: Optional[str] = None
    region: Optional[str] = None

@dataclass
class OperativeReport:
    patient: PatientInfo = field(default_factory=PatientInfo)
    insurance: InsuranceInfo = field(default_factory=InsuranceInfo)
    admission: AdmissionInfo = field(default_factory=AdmissionInfo)
    provider: ProviderInfo = field(default_factory=ProviderInfo)
    diagnoses: DiagnosisInfo = field(default_factory=DiagnosisInfo) # Will now hold ProcessedDiagnosis list
    procedures: List[ProcedureInfo] = field(default_factory=list)
    complications: Optional[str] = None
    estimated_blood_loss: Optional[str] = None
    implants: Optional[str] = None
    recommendations: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the report object to a dictionary for JSON serialization."""
        # Note: asdict might need adjustment if TypedDict causes issues,
        # but should work for basic structure.
        return asdict(self)
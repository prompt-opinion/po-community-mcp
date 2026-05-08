"""
State-specific Medicaid postpartum coverage policy database.
Data reflects policies as of 2026, incorporating ARPA 12-month extension adoptions.

Key fields per state:
  - arpa: bool — whether the state adopted the ARPA 12-month postpartum extension
  - months: int — extension duration (12 for ARPA states, 2 for 60-day-only states)
  - agency: str — state Medicaid agency name
  - phone: str — public helpline number
  - website: str — agency website
  - form: str — extension form name
  - form_number: str | None — official form number if available
  - fax: str | None — fax number for form submission
  - notes: str — policy nuances / caveats
"""

from typing import TypedDict


class StateMedicaidPolicy(TypedDict):
    name: str
    arpa: bool
    months: int
    agency: str
    phone: str
    website: str
    form: str
    form_number: str | None
    fax: str | None
    notes: str


# fmt: off
STATE_POLICIES: dict[str, StateMedicaidPolicy] = {
    "AL": {"name": "Alabama", "arpa": True, "months": 12, "agency": "Alabama Medicaid Agency", "phone": "1-800-362-1504", "website": "https://medicaid.alabama.gov", "form": "Alabama Medicaid Postpartum Coverage Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted effective 2022."},
    "AK": {"name": "Alaska", "arpa": True, "months": 12, "agency": "Alaska Division of Public Assistance", "phone": "1-800-478-7778", "website": "https://health.alaska.gov/dsds/Pages/medicaid", "form": "Alaska Medicaid Postpartum Coverage Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "AZ": {"name": "Arizona", "arpa": True, "months": 12, "agency": "Arizona Health Care Cost Containment System (AHCCCS)", "phone": "1-855-432-7587", "website": "https://www.healthearizonaplus.gov", "form": "AHCCCS Postpartum Medicaid Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "AR": {"name": "Arkansas", "arpa": True, "months": 12, "agency": "Arkansas Department of Human Services", "phone": "1-800-482-8988", "website": "https://humanservices.arkansas.gov", "form": "Arkansas Medicaid Postpartum Extension Request", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "CA": {"name": "California", "arpa": True, "months": 12, "agency": "California Department of Health Care Services (Medi-Cal)", "phone": "1-800-541-5555", "website": "https://www.dhcs.ca.gov", "form": "Medi-Cal Postpartum Period Extension", "form_number": None, "fax": None, "notes": "Medi-Cal provides 12-month postpartum coverage automatically in most counties."},
    "CO": {"name": "Colorado", "arpa": True, "months": 12, "agency": "Colorado Department of Health Care Policy and Financing", "phone": "1-800-221-3943", "website": "https://hcpf.colorado.gov", "form": "Colorado Medicaid Postpartum Coverage Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "CT": {"name": "Connecticut", "arpa": True, "months": 12, "agency": "Connecticut Department of Social Services", "phone": "1-800-842-1508", "website": "https://portal.ct.gov/dss", "form": "HUSKY Health Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "DE": {"name": "Delaware", "arpa": True, "months": 12, "agency": "Delaware Division of Medicaid and Medical Assistance", "phone": "1-800-372-2022", "website": "https://www.dhss.delaware.gov/dhss/dmma", "form": "Delaware Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "DC": {"name": "District of Columbia", "arpa": True, "months": 12, "agency": "DC Department of Health Care Finance", "phone": "(202) 442-9050", "website": "https://dhcf.dc.gov", "form": "DC Medicaid Postpartum Coverage Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "FL": {"name": "Florida", "arpa": False, "months": 2, "agency": "Florida Agency for Health Care Administration (AHCA)", "phone": "1-888-419-3456", "website": "https://www.flmedicaidmanagedcare.com", "form": "Florida Medicaid Redetermination Request", "form_number": None, "fax": None, "notes": "CRITICAL: Florida has NOT adopted ARPA 12-month extension. Coverage ends 60 days postpartum. Immediate escalation and legal aid referral recommended."},
    "GA": {"name": "Georgia", "arpa": True, "months": 12, "agency": "Georgia Department of Community Health (DCH)", "phone": "1-800-869-1150", "website": "https://medicaid.georgia.gov", "form": "Georgia Medicaid 12-Month Postpartum Extension Request", "form_number": "DCH-1040", "fax": "404-463-5720", "notes": "Georgia adopted ARPA 12-month postpartum extension effective April 1, 2022. Patients must apply before the 60-day original coverage expiration date."},
    "HI": {"name": "Hawaii", "arpa": True, "months": 12, "agency": "Hawaii Med-QUEST Division", "phone": "1-800-316-8005", "website": "https://medquest.hawaii.gov", "form": "Hawaii Med-QUEST Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "ID": {"name": "Idaho", "arpa": True, "months": 12, "agency": "Idaho Department of Health and Welfare", "phone": "1-877-456-1233", "website": "https://www.healthandwelfare.idaho.gov", "form": "Idaho Medicaid Postpartum Coverage Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "IL": {"name": "Illinois", "arpa": True, "months": 12, "agency": "Illinois Department of Healthcare and Family Services", "phone": "1-800-843-6154", "website": "https://www.illinois.gov/hfs", "form": "Illinois Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "IN": {"name": "Indiana", "arpa": True, "months": 12, "agency": "Indiana Family and Social Services Administration (FSSA)", "phone": "1-800-403-0864", "website": "https://www.in.gov/fssa", "form": "Indiana Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "IA": {"name": "Iowa", "arpa": True, "months": 12, "agency": "Iowa Department of Health and Human Services", "phone": "1-800-338-8366", "website": "https://hhs.iowa.gov", "form": "Iowa Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "KS": {"name": "Kansas", "arpa": False, "months": 2, "agency": "Kansas Department of Health and Environment (KanCare)", "phone": "1-800-792-4884", "website": "https://www.kancare.ks.gov", "form": "KanCare Medicaid Redetermination", "form_number": None, "fax": None, "notes": "CRITICAL: Kansas has NOT adopted ARPA 12-month extension. Coverage ends 60 days postpartum. Immediate escalation recommended."},
    "KY": {"name": "Kentucky", "arpa": True, "months": 12, "agency": "Kentucky Cabinet for Health and Family Services", "phone": "1-855-459-6328", "website": "https://chfs.ky.gov/agencies/dms", "form": "Kentucky Medicaid Postpartum Extension Request", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "LA": {"name": "Louisiana", "arpa": True, "months": 12, "agency": "Louisiana Department of Health (Medicaid)", "phone": "1-888-342-6207", "website": "https://ldh.la.gov/medicaid", "form": "Louisiana Medicaid Postpartum Coverage Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "ME": {"name": "Maine", "arpa": True, "months": 12, "agency": "Maine Department of Health and Human Services (MaineCare)", "phone": "1-800-977-6740", "website": "https://www.maine.gov/dhhs/ofi/programs-services/mainecare", "form": "MaineCare Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "MD": {"name": "Maryland", "arpa": True, "months": 12, "agency": "Maryland Department of Health (HealthChoice)", "phone": "1-800-226-2142", "website": "https://health.maryland.gov/mmcp", "form": "Maryland Medicaid Postpartum Coverage Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "MA": {"name": "Massachusetts", "arpa": True, "months": 12, "agency": "Massachusetts MassHealth", "phone": "1-800-841-2900", "website": "https://www.mass.gov/masshealth", "form": "MassHealth Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "MI": {"name": "Michigan", "arpa": True, "months": 12, "agency": "Michigan Department of Health and Human Services", "phone": "1-800-642-3195", "website": "https://www.michigan.gov/mdhhs", "form": "Michigan Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "MN": {"name": "Minnesota", "arpa": True, "months": 12, "agency": "Minnesota Department of Human Services (Medical Assistance)", "phone": "1-800-657-3739", "website": "https://mn.gov/dhs", "form": "Minnesota Medical Assistance Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "MS": {"name": "Mississippi", "arpa": True, "months": 12, "agency": "Mississippi Division of Medicaid", "phone": "1-800-421-2408", "website": "https://medicaid.ms.gov", "form": "Mississippi Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "MO": {"name": "Missouri", "arpa": True, "months": 12, "agency": "Missouri Department of Social Services (MO HealthNet)", "phone": "1-800-392-2161", "website": "https://dss.mo.gov/mhd", "form": "MO HealthNet Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "MT": {"name": "Montana", "arpa": True, "months": 12, "agency": "Montana Department of Public Health and Human Services", "phone": "1-800-362-8312", "website": "https://dphhs.mt.gov/MontanaHealthcarePrograms", "form": "Montana Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "NE": {"name": "Nebraska", "arpa": True, "months": 12, "agency": "Nebraska Division of Medicaid and Long-Term Care", "phone": "1-855-632-7633", "website": "https://dhhs.ne.gov/Pages/Medicaid.aspx", "form": "Nebraska Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "NV": {"name": "Nevada", "arpa": True, "months": 12, "agency": "Nevada Division of Health Care Financing and Policy", "phone": "1-800-992-0900", "website": "https://dhcfp.nv.gov", "form": "Nevada Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "NH": {"name": "New Hampshire", "arpa": True, "months": 12, "agency": "New Hampshire Department of Health and Human Services", "phone": "1-800-852-3345", "website": "https://www.dhhs.nh.gov/programs-services/medicaid", "form": "NH Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "NJ": {"name": "New Jersey", "arpa": True, "months": 12, "agency": "New Jersey Division of Medical Assistance and Health Services (NJ FamilyCare)", "phone": "1-800-356-1561", "website": "https://www.state.nj.us/humanservices/dmahs/home", "form": "NJ FamilyCare Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "NM": {"name": "New Mexico", "arpa": True, "months": 12, "agency": "New Mexico Human Services Department (Centennial Care)", "phone": "1-800-283-4465", "website": "https://www.hsd.state.nm.us/mad", "form": "New Mexico Centennial Care Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "NY": {"name": "New York", "arpa": True, "months": 12, "agency": "New York State Department of Health (Medicaid)", "phone": "1-800-541-2831", "website": "https://www.health.ny.gov/health_care/medicaid", "form": "NY Medicaid Postpartum Coverage Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "NC": {"name": "North Carolina", "arpa": True, "months": 12, "agency": "NC Medicaid (NCDHHS)", "phone": "1-888-245-0179", "website": "https://medicaid.ncdhhs.gov", "form": "NC Medicaid Postpartum Coverage Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "ND": {"name": "North Dakota", "arpa": True, "months": 12, "agency": "North Dakota Department of Human Services (Medicaid)", "phone": "1-800-755-2604", "website": "https://www.hhs.nd.gov/healthcare/medicaid", "form": "North Dakota Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "OH": {"name": "Ohio", "arpa": True, "months": 12, "agency": "Ohio Department of Medicaid", "phone": "1-800-324-8680", "website": "https://medicaid.ohio.gov", "form": "Ohio Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "OK": {"name": "Oklahoma", "arpa": True, "months": 12, "agency": "Oklahoma Health Care Authority (SoonerCare)", "phone": "1-800-987-7767", "website": "https://oklahoma.gov/ohca", "form": "SoonerCare Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "OR": {"name": "Oregon", "arpa": True, "months": 12, "agency": "Oregon Health Authority (Oregon Health Plan)", "phone": "1-800-699-9075", "website": "https://www.oregon.gov/oha/HSD/OHP", "form": "Oregon Health Plan Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "PA": {"name": "Pennsylvania", "arpa": True, "months": 12, "agency": "Pennsylvania Department of Human Services (Medical Assistance)", "phone": "1-800-692-7462", "website": "https://www.dhs.pa.gov", "form": "PA Medical Assistance Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "RI": {"name": "Rhode Island", "arpa": True, "months": 12, "agency": "Rhode Island Executive Office of Health and Human Services", "phone": "1-855-697-4347", "website": "https://eohhs.ri.gov/consumer-information/medicaid", "form": "Rhode Island Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "SC": {"name": "South Carolina", "arpa": True, "months": 12, "agency": "South Carolina Department of Health and Human Services", "phone": "1-888-549-0820", "website": "https://www.scdhhs.gov", "form": "SC Medicaid Postpartum Extension Request", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "SD": {"name": "South Dakota", "arpa": True, "months": 12, "agency": "South Dakota Department of Social Services (Medicaid)", "phone": "1-800-597-1603", "website": "https://dss.sd.gov/medicaid", "form": "South Dakota Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "TN": {"name": "Tennessee", "arpa": True, "months": 12, "agency": "Tennessee Department of Finance and Administration (TennCare)", "phone": "1-800-669-1851", "website": "https://www.tn.gov/tenncare", "form": "TennCare Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "TX": {"name": "Texas", "arpa": True, "months": 12, "agency": "Texas Health and Human Services (Medicaid)", "phone": "1-800-252-8263", "website": "https://www.hhs.texas.gov/medicaid", "form": "Texas Medicaid Postpartum Extension Request", "form_number": None, "fax": None, "notes": "Texas adopted ARPA 12-month extension effective 2023."},
    "UT": {"name": "Utah", "arpa": True, "months": 12, "agency": "Utah Department of Health and Human Services (Medicaid)", "phone": "1-800-662-9651", "website": "https://medicaid.utah.gov", "form": "Utah Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "VT": {"name": "Vermont", "arpa": True, "months": 12, "agency": "Vermont Department of Vermont Health Access (Green Mountain Care)", "phone": "1-800-250-8427", "website": "https://dvha.vermont.gov", "form": "Vermont Green Mountain Care Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "VA": {"name": "Virginia", "arpa": True, "months": 12, "agency": "Virginia Department of Medical Assistance Services (DMAS)", "phone": "1-800-552-8627", "website": "https://www.dmas.virginia.gov", "form": "Virginia Medicaid Postpartum Coverage Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "WA": {"name": "Washington", "arpa": True, "months": 12, "agency": "Washington State Health Care Authority (Apple Health)", "phone": "1-800-562-3022", "website": "https://www.hca.wa.gov/apple-health-medicaid", "form": "Apple Health Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "WV": {"name": "West Virginia", "arpa": True, "months": 12, "agency": "West Virginia Department of Human Services (Medicaid)", "phone": "1-800-642-8589", "website": "https://dhhr.wv.gov/bms", "form": "WV Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "WI": {"name": "Wisconsin", "arpa": True, "months": 12, "agency": "Wisconsin Department of Health Services (BadgerCare Plus)", "phone": "1-800-362-3002", "website": "https://www.dhs.wisconsin.gov/badgercareplus", "form": "BadgerCare Plus Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
    "WY": {"name": "Wyoming", "arpa": True, "months": 12, "agency": "Wyoming Department of Health (Medicaid)", "phone": "1-800-251-1269", "website": "https://health.wyo.gov/healthcarefin/medicaid", "form": "Wyoming Medicaid Postpartum Extension", "form_number": None, "fax": None, "notes": "12-month extension adopted."},
}
# fmt: on

DEFAULT_POLICY: StateMedicaidPolicy = {
    "name": "Unknown State",
    "arpa": False,
    "months": 2,
    "agency": "State Medicaid Agency",
    "phone": "1-877-267-2323 (Federal Medicaid Helpline)",
    "website": "https://www.medicaid.gov",
    "form": "State Medicaid Postpartum Extension — Contact state agency for correct form",
    "form_number": None,
    "fax": None,
    "notes": "State policy could not be determined. Defaulting to 60-day cliff. Contact federal helpline or state agency directly.",
}


def get_state_policy(state_code: str) -> StateMedicaidPolicy:
    """Return the Medicaid policy for the given 2-letter state code (case-insensitive)."""
    return STATE_POLICIES.get(state_code.upper(), DEFAULT_POLICY)


def get_non_arpa_states() -> list[str]:
    """Return a list of state codes that have NOT adopted the ARPA 12-month extension."""
    return [code for code, policy in STATE_POLICIES.items() if not policy["arpa"]]

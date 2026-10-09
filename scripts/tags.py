"""Explicit tag map for kept spend rows. Built after reviewing the Service x Expenditure category x
Narrative aggregate of the May-Jul 2026 workbooks. Rules are applied in PRIORITY order; the first
match wins, so every row gets exactly one tag."""

PRIORITY = ["agency_staff", "grant", "premises", "care_education_placement", "general_procurement"]

TAG_MAP = {
    "agency_staff": {
        "narrative_in": ["Agency & Temporary Staff"],
    },
    "grant": {
        "narrative_in": ["Grants"],
        "note": "Rules 1.6.2 treat a grant as a contract, so grants stay in the population.",
    },
    "premises": {
        "expenditure_category_in": ["Premises"],
    },
    "care_education_placement": {
        "narrative_in_any_service": [
            "Allowances for provision care",
            "Adult Placement Allowances",
            "Direct Payment",
            "Payments to Carers",
        ],
        "narrative_in_when_service_in": {
            "narratives": [
                "Private Contractors",
                "Private Contractors Additional Cost",
                "Payment to contractor",
                "Other agencies",
                "Voluntary Associations",
            ],
            "services": [
                "Adult Social Care",
                "Adult Social Care - Transformation Projects",
                "Children's Social Care",
                "Education & SEND",
                "Education (DSG Funded) & Other Education Grants",
                "Executive Director People - Children's Services",
                "Executive Director People - Adult Social Care & Public Health",
            ],
        },
        "note": "Care/placement allowances anywhere, plus contractor, agency or voluntary-sector "
                "narratives under a social care, SEND or education Service (placements, packages, "
                "early-years and SEN provider payments).",
    },
    "general_procurement": {
        "default": True,
        "note": "Everything else, e.g. Environment contractors, Transport Hire (incl. SEND home-to-school "
                "transport), IT, professional fees, minor works.",
    },
}


def tag_row(service, category, narrative) -> str:
    service = "" if service is None else str(service).strip()
    category = "" if category is None else str(category).strip()
    narrative = "" if narrative is None else str(narrative).strip()
    if narrative in TAG_MAP["agency_staff"]["narrative_in"]:
        return "agency_staff"
    if narrative in TAG_MAP["grant"]["narrative_in"]:
        return "grant"
    if category in TAG_MAP["premises"]["expenditure_category_in"]:
        return "premises"
    care = TAG_MAP["care_education_placement"]
    if narrative in care["narrative_in_any_service"]:
        return "care_education_placement"
    cs = care["narrative_in_when_service_in"]
    if narrative in cs["narratives"] and service in cs["services"]:
        return "care_education_placement"
    return "general_procurement"

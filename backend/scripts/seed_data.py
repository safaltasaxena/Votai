"""
backend/scripts/seed_data.py — Seeds Firestore with realistic, neutral election and party data.
"""

import sys
import os
from datetime import datetime

# Add project root to path so we can import backend modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from data.firestore_client import set_document

# ── Regions ───────────────────────────────────────────────────────────────────

REGIONS = [
    {"id": "IN-MH", "name": "Maharashtra"},
    {"id": "IN-DL", "name": "Delhi"},
    {"id": "IN-KA", "name": "Karnataka"},
    {"id": "IN-UP", "name": "Uttar Pradesh"},
    {"id": "IN-TN", "name": "Tamil Nadu"}
]

# ── Election Data ─────────────────────────────────────────────────────────────

def seed_elections():
    print("Seeding elections...")
    for reg in REGIONS:
        data = {
            "state": reg["name"],
            "election_date": "2026-11-15",
            "registration_deadline": "2026-09-30",
            "verification_deadline": "2026-10-20",
            "process_steps": [
                "1. Verify eligibility",
                "2. Register at voterportal.eci.gov.in",
                "3. Verify name in draft electoral roll",
                "4. Check polling booth location",
                "5. Vote on election day"
            ],
            "official_portal": "https://voters.eci.gov.in",
            "last_updated": datetime.now().isoformat(),
            "polling_info": {
                "how_to_find_booth": "Use the Electoral Search portal or 'Voter Helpline' app.",
                "required_documents": "Voter ID (EPIC), Aadhaar, PAN, or Passport.",
                "voting_hours": "07:00 AM - 06:00 PM"
            }
        }
        set_document("elections", reg["id"], data)
        print(f"  - Seeded election for {reg['name']}")

# ── Party Data ───────────────────────────────────────────────────────────────

def seed_parties():
    print("Seeding parties...")
    party_types = [
        {
            "suffix": "DPP",
            "name_prefix": "Democratic Progressive",
            "focus": ["Education", "Healthcare", "Urban Infrastructure", "Digital Literacy", "Youth Employment"],
            "policies": [
                "Increase public education budget by 12%.",
                "Expansion of primary healthcare centres in every district.",
                "Development of high-speed fibre networks in rural areas.",
                "Incentives for startups creating technology-based jobs.",
                "Modernization of urban sewage and waste management systems."
            ],
            "work": [
                "Built 500 new community colleges.",
                "Launched 'Health For All' mobile clinic initiative.",
                "Completed the Regional Digital Highway project.",
                "Established 20 incubation hubs for young entrepreneurs.",
                "Renovated 30 major city transit stations."
            ]
        },
        {
            "suffix": "UEP",
            "name_prefix": "Unity & Equality",
            "focus": ["Agriculture", "Rural Growth", "Social Safety Net", "Small Industry", "Clean Water"],
            "policies": [
                "Guaranteed Minimum Support Price for all seasonal crops.",
                "Direct benefit transfers for small-scale artisans.",
                "Subsidised electricity for rural cottage industries.",
                "Construction of climate-resilient village roads.",
                "Tap water connectivity to 100% of rural households."
            ],
            "work": [
                "Implemented the Krishi Support Scheme for farmers.",
                "Provided vocational training to 1 million rural workers.",
                "Subsidised 200,000 solar pumps for agriculture.",
                "Achieved 90% completion of the Rural Connectivity project.",
                "Restored 5,000 traditional water bodies and ponds."
            ]
        },
        {
            "suffix": "GFA",
            "name_prefix": "Green Future",
            "focus": ["Environment", "Renewable Energy", "Public Transit", "Waste to Wealth", "Forestry"],
            "policies": [
                "Targeting 100% renewable energy grid by 2045.",
                "Subsidies for electric public transport conversion.",
                "Mandatory rainwater harvesting for all new buildings.",
                "Reforestation of 1 million hectares of degraded land.",
                "Zero-waste certification for industrial zones."
            ],
            "work": [
                "Commissioned the country's largest solar park.",
                "Converted 50% of city buses to electric power.",
                "Planted 100 million trees in high-deforestation zones.",
                "Established 5 major bio-methanation plants.",
                "Implemented plastic-free zones in ecological hotspots."
            ]
        }
    ]

    for reg in REGIONS:
        for p_type in party_types:
            p_id = f"{reg['id']}-{p_type['suffix']}"
            data = {
                "party_id": p_id,
                "name": f"{reg['name']} {p_type['name_prefix']} Party",
                "region_id": reg["id"],
                "focus_areas": p_type["focus"],
                "key_policies": p_type["policies"],
                "past_work": p_type["work"]
            }
            set_document("parties", p_id, data)
        print(f"  - Seeded 3 parties for {reg['name']}")

# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    seed_elections()
    seed_parties()
    print("\n✅ Seed complete. Database is demo-ready.")

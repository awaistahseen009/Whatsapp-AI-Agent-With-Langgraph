"""
Seed script: generates 600+ realistic Florida property listings
and inserts them into the property table.

Fixes vs original:
- Price can never be 0: minimum floor enforced after rounding
- Gainesville price_mult corrected (was erroneously 1.65, a college city should be ~0.85)
- Richer, more diverse feature sets per property type
- Broader city/area coverage (20 Florida cities)
- More varied bedroom/bathroom combos
- Realistic developer name distribution
- Consistent use of BIGINT-safe integer prices
- created_at / updated_at explicitly set so batch inserts don't rely solely on server default

Usage:
    .\\venv\\Scripts\\Activate.ps1
    python seed_properties.py
"""

import asyncio
import sys
import random
import uuid
from datetime import datetime, timezone, timedelta

from sqlmodel import SQLModel
from src.app.models.property import Property, PropertyType, ListingType
from src.app.models.client_property_views import ClientPropertyViews  # noqa: F401
from src.app.models.client import Client  # noqa: F401
from src.db.session import get_async_session


# ─── Florida Cities & Areas ───────────────────────────────────────────────────
# price_mult: multiplier applied on top of base price ranges.
# Anchored so that 1.0 == Orlando median.

CITIES = {
    "Miami": {
        "areas": [
            "Brickell", "Wynwood", "Coconut Grove", "Coral Gables", "Little Havana",
            "Edgewater", "Midtown Miami", "Design District", "South Beach",
            "North Miami Beach", "Aventura", "Doral", "Hialeah", "Kendall",
        ],
        "price_mult": 1.45,
        "zip_prefix": "331",
    },
    "Fort Lauderdale": {
        "areas": [
            "Las Olas", "Victoria Park", "Rio Vista", "Flagler Village",
            "Harbor Beach", "Lauderdale Beach", "Wilton Manors", "Plantation",
            "Pompano Beach", "Deerfield Beach",
        ],
        "price_mult": 1.18,
        "zip_prefix": "333",
    },
    "Orlando": {
        "areas": [
            "Downtown Orlando", "Winter Park", "College Park", "Lake Nona",
            "Dr. Phillips", "Baldwin Park", "Thornton Park", "Windermere",
            "Celebration", "MetroWest", "Oviedo", "Altamonte Springs",
        ],
        "price_mult": 1.00,
        "zip_prefix": "328",
    },
    "Tampa": {
        "areas": [
            "Downtown Tampa", "Hyde Park", "Seminole Heights", "Channelside",
            "Westshore", "Davis Islands", "Harbour Island", "Ybor City",
            "Carrollwood", "New Tampa", "Brandon", "Temple Terrace",
        ],
        "price_mult": 1.08,
        "zip_prefix": "336",
    },
    "Jacksonville": {
        "areas": [
            "Riverside", "San Marco", "Avondale", "Springfield",
            "Mandarin", "Southside", "Jacksonville Beach", "Town Center",
            "Ponte Vedra", "Fleming Island", "Orange Park",
        ],
        "price_mult": 0.78,
        "zip_prefix": "322",
    },
    "St. Petersburg": {
        "areas": [
            "Downtown St. Pete", "Old Northeast", "Kenwood", "Historic Uptown",
            "Snell Isle", "Shore Acres", "Coquina Key", "Gulfport",
            "Pinellas Park", "Clearwater Beach",
        ],
        "price_mult": 1.02,
        "zip_prefix": "337",
    },
    "Sarasota": {
        "areas": [
            "Downtown Sarasota", "Siesta Key", "Lido Key", "Longboat Key",
            "Lakewood Ranch", "Palmer Ranch", "Gulf Gate", "Osprey",
            "Venice", "North Port",
        ],
        "price_mult": 1.22,
        "zip_prefix": "342",
    },
    "Naples": {
        "areas": [
            "Old Naples", "Pelican Bay", "Park Shore", "Vanderbilt Beach",
            "Grey Oaks", "Pine Ridge", "Golden Gate Estates",
            "Marco Island", "Bonita Springs", "Estero",
        ],
        "price_mult": 1.55,
        "zip_prefix": "341",
    },
    "West Palm Beach": {
        "areas": [
            "Downtown WPB", "Flamingo Park", "Northwood Village", "El Cid",
            "Palm Beach Gardens", "Jupiter", "Royal Palm Beach",
            "Wellington", "Boynton Beach", "Delray Beach",
        ],
        "price_mult": 1.28,
        "zip_prefix": "334",
    },
    "Gainesville": {
        "areas": [
            "Downtown Gainesville", "Haile Plantation", "Duck Pond District",
            "Tioga Town Center", "Newberry", "Alachua", "Archer Road Corridor",
        ],
        "price_mult": 0.85,   # ← corrected from 1.65 (college city, lower COL)
        "zip_prefix": "326",
    },
    "Tallahassee": {
        "areas": [
            "Downtown Tallahassee", "Midtown Tallahassee", "Killearn Estates",
            "SouthWood", "Betton Hills", "Lafayette Park", "Waverly Hills",
        ],
        "price_mult": 0.82,
        "zip_prefix": "323",
    },
    "Pensacola": {
        "areas": [
            "Downtown Pensacola", "East Hill", "North Hill", "Gulf Breeze",
            "Pensacola Beach", "Perdido Key", "Ferry Pass", "Cantonment",
        ],
        "price_mult": 0.90,
        "zip_prefix": "325",
    },
    "Fort Myers": {
        "areas": [
            "Downtown Fort Myers", "Cape Coral", "Sanibel Island", "Captiva",
            "Gateway", "Lehigh Acres", "Estero", "Bonita Springs",
        ],
        "price_mult": 1.05,
        "zip_prefix": "339",
    },
    "Daytona Beach": {
        "areas": [
            "Daytona Beach Shores", "Port Orange", "Ormond Beach",
            "Holly Hill", "South Daytona", "New Smyrna Beach",
        ],
        "price_mult": 0.88,
        "zip_prefix": "321",
    },
    "Boca Raton": {
        "areas": [
            "Downtown Boca Raton", "Mizner Park", "Royal Palm Yacht",
            "Boca West", "Broken Sound", "East Boca", "Delray Beach",
        ],
        "price_mult": 1.38,
        "zip_prefix": "334",
    },
    "Clearwater": {
        "areas": [
            "Clearwater Beach", "Downtown Clearwater", "Safety Harbor",
            "Dunedin", "Palm Harbor", "Countryside", "East Clearwater",
        ],
        "price_mult": 1.05,
        "zip_prefix": "337",
    },
    "Melbourne": {
        "areas": [
            "Downtown Melbourne", "Suntree", "Viera", "Rockledge",
            "Palm Bay", "Indialantic", "Indian Harbour Beach",
        ],
        "price_mult": 0.92,
        "zip_prefix": "329",
    },
    "Ocala": {
        "areas": [
            "Downtown Ocala", "SE Ocala", "Silver Springs Shores",
            "On Top of the World", "Dunnellon", "Belleview",
        ],
        "price_mult": 0.72,
        "zip_prefix": "344",
    },
    "Key West": {
        "areas": [
            "Old Town Key West", "Duval Street Corridor", "Truman Annex",
            "New Town", "Stock Island", "Key Largo", "Islamorada",
        ],
        "price_mult": 2.10,   # highest COL in FL
        "zip_prefix": "330",
    },
    "Palm Beach": {
        "areas": [
            "Palm Beach Island", "Worth Avenue District", "Mid-Island",
            "North Palm Beach", "Lake Worth Beach", "Lantana",
        ],
        "price_mult": 2.20,
        "zip_prefix": "334",
    },
}


# ─── Street names ─────────────────────────────────────────────────────────────

STREET_NAMES = [
    "Ocean Dr", "Palm Ave", "Bayshore Blvd", "Sunset Rd", "Hibiscus Ln",
    "Magnolia St", "Flamingo Way", "Coral Way", "Biscayne Blvd", "Gulf Blvd",
    "Harbour Dr", "Marina Way", "Pelican Dr", "Mangrove Ln", "Cypress St",
    "Royal Palm Dr", "Jasmine Ave", "Orchid Blvd", "Banyan Rd", "Seagrape Ln",
    "Coconut Palm Rd", "Oleander Dr", "Poinciana Ave", "Tamarind St", "Live Oak Ln",
    "Sand Dollar Ct", "Starfish Way", "Manatee Blvd", "Dolphin Dr", "Heron Rd",
    "Sunrise Blvd", "Trade Winds Ave", "Fairway Dr", "Lakeside Dr", "Riviera Blvd",
    "Citrus Park Rd", "Sago Palm Ln", "Cattail Ct", "Blue Heron Blvd", "Key Lime Dr",
    "Waterview Ter", "Egret Crossing", "Sandpiper Cir", "Winding Creek Rd",
    "Mossy Oak Dr", "Creekside Ln", "Lakefront Blvd", "Bayside Ct", "Coral Reef Dr",
    "Tropic Isle Dr", "Windmill Pt", "Seabreeze Ave", "Harbor View Dr", "Inlet Way",
]

UNIT_SUFFIXES = ["A", "B", "C", "D", "E", "F", "G", "H"]


# ─── Developers ───────────────────────────────────────────────────────────────

DEVELOPERS = [
    "Riley Estate Developments",
    "Sunshine Realty Group",
    "Coastal Living Builders",
    "Palm Horizon Properties",
    "Azure Bay Developers",
    "Emerald Coast Homes",
    "Tropical Breeze Construction",
    "Gulf Stream Residences",
    "Oceanview Partners",
    "Florida Prime Builders",
    "Evergreen Estates Inc.",
    "Sandcastle Development Co.",
    "Bay Vista Group",
    "Pinnacle Homes FL",
    "Island Living Developers",
    "Suncoast Builders LLC",
    "Brickell Luxury Homes",
    "Lakeland Communities",
    "Heritage Homes of Florida",
    "IntraCoastal Development Group",
    "First Coast Construction",
    "Wavecrest Properties",
    "Palmetto Bay Homes",
    "Floridian Living Group",
    "Tropic Wind Developers",
    "SunState Realty Corp",
    "Manatee Construction Co.",
    "Seaside Heights Builders",
    "Golden Gate Developments",
    "Horizon Bay Properties",
]

# Weight toward None so ~30 % of properties have no developer listed
DEVELOPER_POOL = DEVELOPERS + [None] * 13


# ─── Property style labels ─────────────────────────────────────────────────────

HOUSE_STYLES = [
    "Mediterranean", "Colonial", "Ranch-Style", "Craftsman", "Modern Contemporary",
    "Florida Cracker", "Key West Style", "Spanish Revival", "Mid-Century Modern",
    "Cape Cod", "Farmhouse", "Tuscan-Inspired", "Coastal Cottage",
    "Traditional Two-Story", "Old Florida Bungalow", "Prairie Style",
    "Contemporary Waterfront", "New Construction",
]

APARTMENT_STYLES = [
    "Luxury High-Rise", "Boutique Mid-Rise", "Garden-Style", "Loft-Style",
    "Penthouse", "Studio", "Waterfront", "Urban Contemporary",
    "Historic Conversion", "Upscale Condo", "Senior Living", "Student Housing",
]

VILLA_STYLES = [
    "Beachfront Villa", "Lakefront Villa", "Gated Community Villa",
    "Golf Course Villa", "Private Estate Villa", "Tropical Resort Villa",
    "Mediterranean Villa", "Modern Waterfront Villa", "Old-Money Estate",
]

COMMERCIAL_STYLES = [
    "Retail Strip", "Office Suite", "Mixed-Use Building", "Warehouse/Flex Space",
    "Medical Office", "Restaurant/Bar Space", "Corner Storefront",
    "Business Park Unit", "Live-Work Loft",
]


# ─── Feature pools ────────────────────────────────────────────────────────────

FEATURES_POOL = {
    "house": [
        "private pool", "heated pool", "spa/hot tub", "two-car garage",
        "three-car garage", "boat storage", "RV hookup", "fenced yard",
        "smart home system", "solar panels", "hurricane shutters", "impact windows",
        "gourmet kitchen", "granite countertops", "quartz countertops",
        "marble floors", "hardwood floors", "tile roof", "metal roof",
        "screened lanai", "outdoor kitchen", "summer kitchen", "fireplace",
        "walk-in closets", "laundry room", "home office", "wine cellar",
        "fruit trees", "sprinkler system", "security system", "EV charger",
        "crown molding", "vaulted ceilings", "open floor plan", "guest suite",
        "mother-in-law suite", "bonus room", "loft", "butler's pantry",
        "mudroom", "whole-house generator", "tankless water heater",
        "central vacuum", "intercom system", "landscape lighting",
        "paver driveway", "circular driveway", "private dock", "canal access",
        "lake frontage", "no HOA", "low HOA", "gated community",
    ],
    "apartment": [
        "balcony", "private terrace", "wrap-around balcony",
        "city view", "ocean view", "bay view", "pool view", "garden view",
        "concierge service", "24/7 security", "valet parking",
        "rooftop pool", "resort-style pool", "gym/fitness center",
        "spa and sauna", "coworking lounge", "business center",
        "package lockers", "in-unit washer/dryer", "stainless appliances",
        "quartz countertops", "walk-in closet", "custom cabinetry",
        "EV charging station", "dog park", "pet spa", "bike storage",
        "smart locks", "keyless entry", "floor-to-ceiling windows",
        "dual sinks", "soaking tub", "rainfall shower", "storage unit",
        "assigned parking", "covered parking", "garage parking",
        "club room", "game room", "movie theater room", "children's playroom",
        "on-site management", "gated entry", "controlled access lobby",
    ],
    "villa": [
        "private pool", "infinity pool", "heated pool", "private beach access",
        "deeded beach access", "boat dock", "deep-water dock",
        "chef's kitchen", "butler's pantry", "catering kitchen",
        "home theater", "wine cellar", "cigar room",
        "elevator", "private elevator lobby",
        "guest house", "carriage house", "staff quarters",
        "tropical landscaping", "outdoor shower", "pool bath",
        "smart home automation", "Crestron system", "Lutron lighting",
        "security gate", "guardhouse", "CCTV surveillance",
        "marble flooring", "imported stone", "impact glass throughout",
        "generator", "whole-house audio", "temperature-controlled garage",
        "golf cart garage", "tennis court", "basketball court",
        "putting green", "private garden", "courtyard fountain",
    ],
    "commercial": [
        "open floor plan", "reception area", "multiple conference rooms",
        "server/IT room", "loading dock", "drive-through",
        "ample surface parking", "covered parking", "ADA compliant",
        "fiber-optic internet", "security cameras", "alarm system",
        "elevator access", "freight elevator", "backup generator",
        "HVAC zones", "drop ceilings", "exposed concrete", "polished floors",
        "high ceilings (14 ft+)", "mezzanine level", "roll-up doors",
        "sprinkler system", "fire suppression", "kitchenette", "break room",
        "separate utility meters", "signage rights", "corner visibility",
        "high daily traffic count", "near major interchange",
    ],
    "plot": [
        "cleared lot", "partially cleared", "heavily wooded",
        "waterfront", "lakefront", "canalfront", "oceanfront",
        "corner lot", "cul-de-sac lot", "oversized lot",
        "zoned residential (R-1)", "zoned residential (R-2)",
        "zoned mixed-use", "zoned commercial",
        "all utilities at lot line", "water & sewer connected",
        "well & septic in place", "paved road frontage", "private road",
        "mature oak trees", "tropical landscaping", "lake view",
        "canal access", "no HOA restrictions", "subdivision approved",
        "survey on file", "soil test completed", "environmental survey done",
        "platted lot", "buildable immediately",
    ],
}


# ─── Price ranges (base USD, before city multiplier) ─────────────────────────
# Expanded to reflect realistic FL market spread.

PRICE_RANGES = {
    "house": {
        "sale": {"min": 175_000,   "max": 2_200_000},
        "rent": {"min": 1_600,     "max": 14_000},
    },
    "apartment": {
        "sale": {"min": 110_000,   "max": 1_100_000},
        "rent": {"min": 1_050,     "max": 7_500},
    },
    "villa": {
        "sale": {"min": 480_000,   "max": 6_500_000},
        "rent": {"min": 3_500,     "max": 30_000},
    },
    "commercial": {
        "sale": {"min": 200_000,   "max": 4_000_000},
        "rent": {"min": 2_000,     "max": 22_000},
    },
    "plot": {
        "sale": {"min": 45_000,    "max": 1_200_000},
        "rent": {"min": 600,       "max": 4_000},
    },
}

# Price floors after rounding — ensures we never land on 0.
PRICE_FLOORS = {
    "house":      {"sale": 100_000, "rent": 800},
    "apartment":  {"sale": 80_000,  "rent": 700},
    "villa":      {"sale": 300_000, "rent": 2_000},
    "commercial": {"sale": 100_000, "rent": 1_000},
    "plot":       {"sale": 25_000,  "rent": 400},
}

SIZE_RANGES = {
    "house":      {"min": 1_100, "max": 6_500},
    "apartment":  {"min": 420,   "max": 2_500},
    "villa":      {"min": 2_200, "max": 9_500},
    "commercial": {"min": 600,   "max": 18_000},
    "plot":       {"min": 3_000, "max": 60_000},
}


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _round_price(price: float, listing_type: str) -> int:
    """Round price to a realistic multiple and enforce a minimum floor."""
    if listing_type == "sale":
        rounded = round(price / 5_000) * 5_000
    else:
        rounded = round(price / 50) * 50
    return max(rounded, 1)   # absolute safety: never 0


def _safe_price(ptype_key: str, ltype_key: str, mult: float) -> int:
    pr = PRICE_RANGES[ptype_key][ltype_key]
    base = random.randint(pr["min"], pr["max"])
    raw = base * mult
    rounded = _round_price(raw, ltype_key)
    floor = PRICE_FLOORS[ptype_key][ltype_key]
    return max(rounded, floor)


def _gen_address(area: str, city: str, zip_prefix: str) -> str:
    num = random.randint(100, 9999)
    street = random.choice(STREET_NAMES)
    zip_code = f"{zip_prefix}{random.randint(10, 99):02d}"
    has_unit = random.random() < 0.28
    unit = (
        f", Unit {random.choice(UNIT_SUFFIXES)}{random.randint(1, 25)}"
        if has_unit
        else ""
    )
    return f"{num} {street}{unit}, {area}, {city}, FL {zip_code}"


def _gen_description(
    prop_type: str, style: str,
    beds: int | None, baths: int | None,
    sqft: int, area: str, city: str,
    features: list[str],
    listing_type: str,
) -> str:
    action = "for sale" if listing_type == "sale" else "available for rent"
    feat_str = ", ".join(features[:5])

    if prop_type == "house":
        return (
            f"Charming {style} home {action} in the desirable {area} neighborhood of {city}. "
            f"This {beds}-bedroom, {baths}-bathroom residence spans {sqft:,} sq ft "
            f"and showcases {feat_str}. "
            f"Situated close to top-rated schools, vibrant dining, and convenient shopping. "
            f"A rare opportunity in one of {city}'s most sought-after communities."
        )
    elif prop_type == "apartment":
        return (
            f"{style} apartment {action} in the heart of {area}, {city}. "
            f"Offering {beds} bedroom(s) and {baths} bathroom(s) across {sqft:,} sq ft of thoughtfully "
            f"designed living space. Building highlights include {feat_str}. "
            f"Steps away from restaurants, nightlife, and public transit."
        )
    elif prop_type == "villa":
        return (
            f"Exceptional {style} {action} in the prestigious enclave of {area}, {city}. "
            f"This magnificent {beds}-bedroom, {baths}-bathroom estate spans {sqft:,} sq ft "
            f"and boasts {feat_str}. "
            f"An unparalleled luxury living experience — crafted for the most discerning buyer."
        )
    elif prop_type == "commercial":
        return (
            f"Prime {style} {action} in high-traffic {area}, {city}. "
            f"{sqft:,} sq ft of versatile space featuring {feat_str}. "
            f"Excellent visibility and easy access from major arterials. "
            f"Ideal for retail, professional services, or mixed-use operations."
        )
    else:  # plot
        return (
            f"Exceptional land opportunity {action} in {area}, {city}. "
            f"{sqft:,} sq ft lot — {feat_str}. "
            f"Ready to build your dream home, vacation retreat, or investment property. "
            f"Survey and environmental reports available on request."
        )


def _gen_title(
    prop_type: str, style: str,
    beds: int | None, area: str,
    listing_type: str,
) -> str:
    action = "for Sale" if listing_type == "sale" else "for Rent"
    if prop_type == "house":
        return f"{style} {beds}BR/{beds - 1 if beds and beds > 1 else 1}BA Home {action} – {area}"
    elif prop_type == "apartment":
        label = "Studio" if beds == 0 else f"{beds}BR"
        return f"{style} {label} Apartment {action} in {area}"
    elif prop_type == "villa":
        return f"{beds}BR {style} {action} – {area}"
    elif prop_type == "commercial":
        return f"{style} {action} – {area}"
    else:
        return f"Buildable Land / Lot {action} – {area}"


def _random_past_date(days_back: int = 365) -> datetime:
    """Return a random UTC datetime within the last `days_back` days."""
    delta = random.randint(0, days_back * 24 * 60)   # minutes
    return datetime.now(timezone.utc) - timedelta(minutes=delta)


# ─── Generator ───────────────────────────────────────────────────────────────

def generate_properties(count: int = 620) -> list[dict]:
    """
    Generate `count` realistic Florida property records.
    Distribution is weighted to reflect real market mix.
    """
    properties: list[dict] = []
    city_names = list(CITIES.keys())

    # Weighted type distribution
    TYPE_WEIGHTS = [
        (PropertyType.HOUSE,      0.34),
        (PropertyType.APARTMENT,  0.30),
        (PropertyType.VILLA,      0.10),
        (PropertyType.COMMERCIAL, 0.10),
        (PropertyType.PLOT,       0.16),
    ]
    LISTING_WEIGHTS = [
        (ListingType.SALE, 0.68),
        (ListingType.RENT, 0.32),
    ]

    # City weights: larger metros get more listings
    CITY_WEIGHTS = [
        6.0,   # Miami
        4.5,   # Fort Lauderdale
        5.0,   # Orlando
        4.8,   # Tampa
        3.5,   # Jacksonville
        2.8,   # St. Petersburg
        2.5,   # Sarasota
        2.0,   # Naples
        3.0,   # West Palm Beach
        1.5,   # Gainesville
        1.5,   # Tallahassee
        1.2,   # Pensacola
        2.0,   # Fort Myers
        1.2,   # Daytona Beach
        2.2,   # Boca Raton
        2.0,   # Clearwater
        1.2,   # Melbourne
        0.8,   # Ocala
        1.5,   # Key West
        1.3,   # Palm Beach
    ]

    for _ in range(count):
        # City
        city_name = random.choices(city_names, weights=CITY_WEIGHTS)[0]
        city_data = CITIES[city_name]
        area = random.choice(city_data["areas"])
        mult = city_data["price_mult"]
        zip_prefix = city_data["zip_prefix"]

        # Type & listing
        prop_type = random.choices(
            [t for t, _ in TYPE_WEIGHTS],
            weights=[w for _, w in TYPE_WEIGHTS],
        )[0]
        listing_type = random.choices(
            [t for t, _ in LISTING_WEIGHTS],
            weights=[w for _, w in LISTING_WEIGHTS],
        )[0]

        ptype_key = prop_type.value
        ltype_key = listing_type.value

        # Size (sq ft) — round to nearest 50
        sr = SIZE_RANGES[ptype_key]
        sqft = round(random.randint(sr["min"], sr["max"]) / 50) * 50
        sqft = max(sqft, 200)   # never 0

        # Price — always safe (>= floor)
        price = _safe_price(ptype_key, ltype_key, mult)

        # ── Beds / baths ────────────────────────────────────────────────────
        if ptype_key in ("commercial", "plot"):
            beds, baths = None, None

        elif ptype_key == "villa":
            beds = random.choices([3, 4, 5, 6, 7, 8], weights=[5, 20, 30, 25, 15, 5])[0]
            extra_baths = random.choice([0, 1, 1, 2])
            baths = beds + extra_baths

        elif ptype_key == "apartment":
            beds = random.choices(
                [0, 1, 2, 3, 4],
                weights=[8, 28, 38, 20, 6],
            )[0]
            if beds == 0:
                baths = 1
            elif beds == 1:
                baths = random.choice([1, 1, 2])
            elif beds == 2:
                baths = random.choice([1, 2, 2, 2])
            else:
                baths = random.choice([2, 2, 3])

        else:  # house
            beds = random.choices(
                [2, 3, 4, 5, 6, 7],
                weights=[8, 30, 32, 18, 8, 4],
            )[0]
            if beds <= 3:
                baths = random.choice([1, 2, 2, 3])
            elif beds == 4:
                baths = random.choice([2, 3, 3, 4])
            else:
                baths = random.choice([3, 4, 4, 5])

        # ── Floors ──────────────────────────────────────────────────────────
        if ptype_key == "apartment":
            total_floors = random.choices(
                [3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50],
                weights=[4, 6, 8, 8, 10, 12, 10, 10, 8, 8, 7, 5, 4],
            )[0]
            floor_number = random.randint(1, total_floors)
        elif ptype_key in ("house", "villa"):
            total_floors = random.choices([1, 2, 3], weights=[45, 45, 10])[0]
            floor_number = None
        else:
            total_floors = None
            floor_number = None

        # ── Style ───────────────────────────────────────────────────────────
        style_map = {
            "house":      HOUSE_STYLES,
            "apartment":  APARTMENT_STYLES,
            "villa":      VILLA_STYLES,
            "commercial": COMMERCIAL_STYLES,
            "plot":       [""],
        }
        style = random.choice(style_map[ptype_key])

        # ── Features ────────────────────────────────────────────────────────
        feat_pool = FEATURES_POOL[ptype_key]
        n_features = random.randint(4, min(10, len(feat_pool)))
        features = random.sample(feat_pool, n_features)

        # ── Timestamps ──────────────────────────────────────────────────────
        created_at = _random_past_date(days_back=730)   # up to 2 years old
        updated_at = created_at + timedelta(
            minutes=random.randint(0, 90 * 24 * 60)     # updated up to 90 days later
        )
        if updated_at > datetime.now(timezone.utc):
            updated_at = datetime.now(timezone.utc)

        # ── Availability ────────────────────────────────────────────────────
        # ~92 % available; 8 % recently sold/leased but kept for history
        available = random.choices([True, False], weights=[92, 8])[0]

        properties.append({
            "property_id":    uuid.uuid4(),
            "title":          _gen_title(ptype_key, style, beds, area, ltype_key),
            "description":    _gen_description(
                                  ptype_key, style, beds, baths,
                                  sqft, area, city_name, features, ltype_key,
                              ),
            "property_type":  prop_type,
            "listing_type":   listing_type,
            "location_area":  area,
            "location_city":  city_name,
            "address":        _gen_address(area, city_name, zip_prefix),
            "price":          price,
            "price_negotiable": random.choices(
                                    [True, False],
                                    weights=[72, 28],
                                )[0],
            "bedrooms":       beds,
            "bathrooms":      baths,
            "size_sqft":      sqft,
            "floor_number":   floor_number,
            "total_floors":   total_floors,
            "features":       {"list": features},
            "images":         [],
            "available":      available,
            "developer_name": random.choice(DEVELOPER_POOL),
            "created_at":     created_at,
            "updated_at":     updated_at,
        })

    return properties


# ─── DB seeder ────────────────────────────────────────────────────────────────

async def seed(count: int = 620, batch_size: int = 50) -> None:
    props = generate_properties(count)
    total = 0

    print(f"🌴  Seeding {len(props)} Florida properties across {len(CITIES)} cities…\n")

    for start in range(0, len(props), batch_size):
        batch = props[start : start + batch_size]
        async with get_async_session() as session:
            for p in batch:
                session.add(Property(**p))
            await session.commit()
            total += len(batch)
            pct = total / len(props) * 100
            print(f"  ✓ {total:>4}/{len(props)}  ({pct:.0f}%)  — batch inserted")

    # Summary
    city_counts: dict[str, int] = {}
    type_counts: dict[str, int] = {}
    zero_prices = 0
    for p in props:
        city_counts[p["location_city"]] = city_counts.get(p["location_city"], 0) + 1
        type_counts[p["property_type"].value] = type_counts.get(p["property_type"].value, 0) + 1
        if p["price"] == 0:
            zero_prices += 1

    print(f"\n{'─'*55}")
    print(f"✅  Done!  Seeded {total} properties")
    print(f"   Zero-price records: {zero_prices}  (should be 0)")
    print(f"\n   By city:")
    for city, n in sorted(city_counts.items(), key=lambda x: -x[1]):
        print(f"     {city:<25} {n:>4}")
    print(f"\n   By type:")
    for ptype, n in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"     {ptype:<15} {n:>4}")


if __name__ == "__main__":
    # asyncio.run() on Windows (Python ≤ 3.11) uses ProactorEventLoop, which
    # emits a harmless "Event loop is closed" RuntimeError during GC cleanup
    # of pipe transports. Switching to SelectorEventLoop suppresses it.
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(seed())
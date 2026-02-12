"""
Building Codes and Mappings for Kartverket Matrikkel API
=========================================================

This module contains all code mappings and helper functions for translating
between Kartverket's internal codes and official Norwegian standards.

Key Concepts:
    - Kartverket Internal IDs (0-127): Raw codes from the API
    - NS 3457/SSB Codes (111-999): Official building classification
    - The two systems need mapping because they use different numbering

Code Dictionaries:
    - INTERNAL_ID_TO_NS3457: Maps internal IDs to official codes
    - BUILDING_TYPE_CODES: Norwegian descriptions for all NS 3457 codes
    - BUILDING_STATUS_CODES: Building status descriptions
    - OWNERSHIP_TYPE_CODES: Ownership type descriptions

Functions:
    - get_building_type_hierarchy(): Get all three levels for a building type
    - get_building_type_name(): Get the most specific type name

Reference:
    SSB KLASS Version 64: https://www.ssb.no/klass/klassifikasjoner/64

Example:
    >>> from codes import get_building_type_hierarchy, INTERNAL_ID_TO_NS3457
    >>> internal_id = 104  # From API
    >>> ssb_code = INTERNAL_ID_TO_NS3457[internal_id]  # 671
    >>> level1, level2, level3 = get_building_type_hierarchy(internal_id)
    >>> print(f"{level1} > {level2} > {level3}")
    Kultur- og forskningsbygning > Bygning for religiøse aktiviteter > Kirke, kapell
"""

from typing import Any, Optional, Tuple


# =============================================================================
# Internal ID to NS 3457 Mapping
# =============================================================================

# Mapping from Kartverket internal building type IDs to NS 3457 codes
# The API returns internal IDs (0-127), which need to be converted to NS 3457 codes
#
# This mapping was derived by querying the Kartverket API's `findAlleBygningstypeKoder`
# method and extracting the `kodeverdi` field (which contains the NS 3457 code)
# for each internal ID.

INTERNAL_ID_TO_NS3457 = {
    0: None,  # Unknown/empty
    1: 111,
    2: 112,
    3: 113,
    4: 121,
    5: 122,
    6: 123,
    7: 124,
    8: 131,
    9: 133,
    10: 135,
    11: 136,
    12: 141,
    13: 142,
    14: 143,
    15: 144,
    16: 145,
    17: 146,
    18: 151,
    19: 152,
    20: 159,
    21: 161,
    22: 162,
    23: 163,
    24: 171,
    25: 172,
    26: 181,
    27: 182,
    28: 183,
    29: 193,
    30: 199,
    31: 211,
    32: 212,
    33: 214,
    34: 216,
    35: 219,
    36: 221,
    37: 223,
    38: 229,
    39: 231,
    40: 232,
    41: 233,
    42: 239,
    43: 241,
    44: 243,
    45: 244,
    46: 245,
    47: 248,
    48: 249,
    49: 311,
    50: 312,
    51: 313,
    52: 319,
    53: 321,
    54: 322,
    55: 323,
    56: 329,
    57: 330,
    58: 411,
    59: 412,
    60: 415,
    61: 416,
    62: 419,
    63: 429,
    64: 431,
    65: 439,
    66: 441,
    67: 449,
    68: 511,
    69: 512,
    70: 519,
    71: 521,
    72: 522,
    73: 523,
    74: 524,
    75: 529,
    76: 531,
    77: 532,
    78: 533,
    79: 539,
    80: 611,
    81: 612,
    82: 613,
    83: 614,
    84: 615,
    85: 616,
    86: 619,
    87: 621,
    88: 623,
    89: 629,
    90: 641,
    91: 642,
    92: 643,
    93: 649,
    94: 651,
    95: 652,
    96: 653,
    97: 654,
    98: 655,
    99: 659,
    100: 661,
    101: 662,
    102: 663,
    103: 669,
    104: 671,
    105: 672,
    106: 673,
    107: 674,
    108: 675,
    109: 679,
    110: 719,
    111: 721,
    112: 722,
    113: 723,
    114: 729,
    115: 731,
    116: 732,
    117: 739,
    118: 819,
    119: 821,
    120: 822,
    121: 823,
    122: 824,
    123: 825,
    124: 829,
    125: 830,
    126: 840,
    127: 999,
}


# =============================================================================
# Building Type Codes (NS 3457 / SSB Classification)
# =============================================================================

# Building type codes - Official SSB/NS 3457 classification
# Source: SSB (Statistics Norway) - https://www.ssb.no/klass/klassifikasjoner/64
#
# The classification has three levels:
#   Level 1 (codes 1-8): Hovedgruppe - Main category
#   Level 2 (codes 11-84): Bygningsgruppe - Building group
#   Level 3 (codes 111-999): Bygningstype - Specific building type

BUILDING_TYPE_CODES = {
    # -------------------------------------------------------------------------
    # Level 1 - Hovedgruppe (Main category)
    # -------------------------------------------------------------------------
    1: "Bolig",
    2: "Industri og lagerbygning",
    3: "Kontor- og forretningsbygning",
    4: "Samferdsels- og kommunikasjonsbygning",
    5: "Hotell- og restaurantbygning",
    6: "Kultur- og forskningsbygning",
    7: "Helsebygning",
    8: "Fengsel, beredskapsbygning mv.",

    # -------------------------------------------------------------------------
    # Level 2 - Bygningsgruppe (Building group)
    # -------------------------------------------------------------------------
    # Under 1: Bolig
    11: "Enebolig",
    12: "Tomannsbolig",
    13: "Rekkehus, kjedehus, andre småhus",
    14: "Store boligbygg",
    15: "Bygning for bofellesskap",
    16: "Fritidsbolig",
    17: "Koie, seterhus og lignende",
    18: "Garasje og uthus til bolig",
    19: "Annen boligbygning",

    # Under 2: Industri og lagerbygning
    21: "Industribygning",
    22: "Energiforsyningsbygning",
    23: "Lagerbygning",
    24: "Fiskeri- og landbruksbygning",

    # Under 3: Kontor- og forretningsbygning
    31: "Kontorbygning",
    32: "Forretningsbygning",

    # Under 4: Samferdsels- og kommunikasjonsbygning
    41: "Ekspedisjonsbygning, terminal",
    42: "Telekommunikasjonsbygning",
    43: "Garasje- og hangarbygning",
    44: "Veg- og trafikktilsynsbygning",

    # Under 5: Hotell- og restaurantbygning
    51: "Hotellbygning",
    52: "Bygning for overnatting",
    53: "Restaurantbygning",

    # Under 6: Kultur- og forskningsbygning
    61: "Skolebygning",
    62: "Universitets- og høgskolebygning",
    64: "Museums- og biblioteksbygning",
    65: "Idrettsbygning",
    66: "Kulturhus",
    67: "Bygning for religiøse aktiviteter",

    # Under 7: Helsebygning
    71: "Sykehus",
    72: "Sykehjem",
    73: "Primærhelsebygning",

    # Under 8: Fengsel, beredskapsbygning mv.
    81: "Fengselsbygning",
    82: "Beredskapsbygning",
    83: "Monument",
    84: "Offentlig toalett",

    # -------------------------------------------------------------------------
    # Level 3 - Bygningstype (Specific building type)
    # -------------------------------------------------------------------------
    # 11x: Enebolig
    111: "Enebolig",
    112: "Enebolig med hybelleilighet, sokkelleilighet o.l.",
    113: "Våningshus",

    # 12x: Tomannsbolig
    121: "Tomannsbolig, vertikaldelt",
    122: "Tomannsbolig, horisontaldelt",
    123: "Våningshus, tomannsbolig, vertikaldelt",
    124: "Våningshus, tomannsbolig, horisontaldelt",

    # 13x: Rekkehus, kjedehus, andre småhus
    131: "Rekkehus",
    133: "Kjedehus inkl. atriumhus",
    135: "Terrassehus",
    136: "Andre småhus med 3 boliger eller flere",

    # 14x: Store boligbygg
    141: "Store frittliggende boligbygg på 2 etasjer",
    142: "Store frittliggende boligbygg på 3 og 4 etasjer",
    143: "Store frittliggende boligbygg på 5 etasjer eller over",
    144: "Store sammenbygde boligbygg på 2 etasjer",
    145: "Store sammenbygde boligbygg på 3 og 4 etasjer",
    146: "Store sammenbygde boligbygg på 5 etasjer og over",

    # 15x: Bygning for bofellesskap
    151: "Bo- og servicesenter",
    152: "Studenthjem/studentboliger",
    159: "Annen bygning for bofellesskap",

    # 16x: Fritidsbolig
    161: "Fritidsbygning (hytter, sommerhus o.l.)",
    162: "Helårsbolig benyttet som fritidsbolig",
    163: "Våningshus benyttet som fritidsbolig",

    # 17x: Koie, seterhus og lignende
    171: "Seterhus, sel, rorbu o.l.",
    172: "Skogs- og utmarkskoie, gamme",

    # 18x: Garasje og uthus til bolig
    181: "Garasje, uthus, anneks knyttet til bolig",
    182: "Garasje, uthus, anneks knyttet til fritidsbolig",
    183: "Naust, båthus, sjøbu",

    # 19x: Annen boligbygning
    193: "Boligbrakker",
    199: "Annen boligbygning (f.eks. sekundærbolig reindrift)",

    # 21x: Industribygning
    211: "Fabrikkbygning",
    212: "Verkstedbygning",
    214: "Bygning for renseanlegg",
    216: "Bygning for vannforsyning, bl.a. pumpestasjon",
    219: "Annen industribygning",

    # 22x: Energiforsyningsbygning
    221: "Kraftstasjon (>15 000 kVA)",
    223: "Transformatorstasjon (>10 000 kVA)",
    229: "Annen energiforsyningsbygning",

    # 23x: Lagerbygning
    231: "Lagerhall",
    232: "Kjøle- og fryselager",
    233: "Silobygning",
    239: "Annen lagerbygning",

    # 24x: Fiskeri- og landbruksbygning
    241: "Hus for dyr, fôrlager, strølager, frukt- og grønnsakslager, landbrukssilo, høy-/korntørke",
    243: "Veksthus",
    244: "Driftsbygning for fiske og fangst, inkl. oppdrettsanlegg",
    245: "Naust/redskapshus for fiske",
    248: "Annen fiskeri- og fangstbygning",
    249: "Annen landbruksbygning",

    # 31x: Kontorbygning
    311: "Kontor- og administrasjonsbygning, rådhus",
    312: "Bankbygning, posthus",
    313: "Mediebygning",
    319: "Annen kontorbygning",

    # 32x: Forretningsbygning
    321: "Kjøpesenter, varehus",
    322: "Butikkbygning",
    323: "Bensinstasjon",
    329: "Annen forretningsbygning",
    330: "Messe- og kongressbygning",

    # 41x: Ekspedisjonsbygning, terminal
    411: "Ekspedisjonsbygning, flyterminal, kontrolltårn",
    412: "Jernbane- og T-banestasjon",
    415: "Godsterminal",
    416: "Postterminal",
    419: "Annen ekspedisjons- og terminalbygning",

    # 42x: Telekommunikasjonsbygning
    429: "Telekommunikasjonsbygning",

    # 43x: Garasje- og hangarbygning
    431: "Parkeringshus",
    439: "Annen garasje- hangarbygning",

    # 44x: Veg- og trafikktilsynsbygning
    441: "Trafikktilsynsbygning",
    449: "Annen veg- og trafikktilsynsbygning",

    # 51x: Hotellbygning
    511: "Hotellbygning",
    512: "Motellbygning",
    519: "Annen hotellbygning",

    # 52x: Bygning for overnatting
    521: "Hospits, pensjonat",
    522: "Vandrerhjem, feriehjem/-koloni, turisthytte",
    523: "Appartement",
    524: "Campinghytte/utleiehytte",
    529: "Annen bygning for overnatting",

    # 53x: Restaurantbygning
    531: "Restaurantbygning, kafébygning",
    532: "Sentralkjøkken, kantinebygning",
    533: "Gatekjøkken, kioskbygning",
    539: "Annen restaurantbygning",

    # 61x: Skolebygning
    611: "Lekepark",
    612: "Barnehage",
    613: "Barneskole",
    614: "Ungdomsskole",
    615: "Kombinert barne- og ungdomsskole",
    616: "Videregående skole",
    619: "Annen skolebygning",

    # 62x: Universitets- og høgskolebygning
    621: "Universitets- og høgskolebygning med integrerte funksjoner, auditorium, lesesal o.a.",
    623: "Laboratoriebygning",
    629: "Annen universitets-, høgskole- og forskningsbygning",

    # 64x: Museums- og biblioteksbygning
    641: "Museum, kunstgalleri",
    642: "Bibliotek, mediatek",
    643: "Zoologisk og botanisk hage",
    649: "Annen museums- og bibliotekbygning",

    # 65x: Idrettsbygning
    651: "Idrettshall",
    652: "Ishall",
    653: "Svømmehall",
    654: "Tribune og idrettsgarderobe",
    655: "Helsestudio",
    659: "Annen idrettsbygning",

    # 66x: Kulturhus
    661: "Kinobygning, teaterbygning, opera/konserthus",
    662: "Samfunnshus, grendehus",
    663: "Diskotek",
    669: "Annet kulturhus",

    # 67x: Bygning for religiøse aktiviteter
    671: "Kirke, kapell",
    672: "Bedehus, menighetshus",
    673: "Krematorium, gravkapell, bårehus",
    674: "Synagoge, moské",
    675: "Kloster",
    679: "Annen bygning for religiøse aktiviteter",

    # 71x: Sykehus
    719: "Sykehus",

    # 72x: Sykehjem
    721: "Sykehjem",
    722: "Bo- og behandlingssenter, aldershjem",
    723: "Rehabiliteringsinstitusjon, kurbad",
    729: "Annet sykehjem",

    # 73x: Primærhelsebygning
    731: "Klinikk, legekontor/-senter/-vakt",
    732: "Helse- og sosialsenter, helsestasjon",
    739: "Annen primærhelsebygning",

    # 81x: Fengselsbygning
    819: "Fengselsbygning",

    # 82x: Beredskapsbygning
    821: "Politistasjon",
    822: "Brannstasjon, ambulansestasjon",
    823: "Fyrstasjon, losstasjon",
    824: "Stasjon for radarovervåkning av fly- og/eller skipstrafikk",
    825: "Tilfluktsrom/bunker",
    829: "Annen beredskapsbygning",

    # 83x: Monument
    830: "Monument",

    # 84x: Offentlig toalett
    840: "Offentlig toalett",

    # 999: Unknown
    999: "Ukjent bygningstype",
}


# =============================================================================
# Building Status Codes
# =============================================================================
# Note: For now these are the codes that we want in our analysis.
# (keep: 2, 3, 4, 6, 7, 8, 13-18).

BUILDING_STATUS_CODES = {
    0: "Rammetillatelse",
    1: "Igangsettingstillatelse",
    2: "Midlertidig brukstillatelse",
    3: "Ferdigattest",
    4: "Tatt i bruk",
    5: "Meldingssak registrer tiltak",
    6: "Meldingssak tiltak fullført",
    7: "Tiltak unntatt fra byggesaksbehandling",
    8: "Bygning godkjent for riving/brenning",
    9: "Bygning revet/brent",
    10: "Bygging avlyst",
    11: "Bygning flyttet",
    12: "Bygningsnummer utgått",
    13: "Fritatt for søknadsplikt",
    14: "Endre bygningsdata",
    15: "Tilbygg opprettet som egen bygning",
    16: "Bygg etablert som tilbygg på annen bygning",
    17: "Splitt bygning",
    18: "Data fra bygningsendring overført",
}

# Status code groups used across Kartverket filtering and Gemini analysis.
EXCLUDED_BUILDING_STATUS_CODE_IDS = (0, 1, 5, 9, 10, 11, 12)
INCLUDED_BUILDING_STATUS_CODE_IDS = (2, 3, 4, 6, 7, 8, 13, 14, 15, 16, 17, 18)
EXCLUDED_BUILDING_STATUS_CODES = {
    code_id: BUILDING_STATUS_CODES[code_id]
    for code_id in EXCLUDED_BUILDING_STATUS_CODE_IDS
}
DEMOLITION_APPROVED_STATUS_CODE = 8
DEMOLITION_APPROVED_STATUS_NAME = BUILDING_STATUS_CODES[DEMOLITION_APPROVED_STATUS_CODE]


# =============================================================================
# Ownership Type Codes
# =============================================================================

# Ownership type codes (EierforholdKode)
# Based on Norwegian cadastral terminology

OWNERSHIP_TYPE_CODES = {
    0: "Hjemmelshaver",
    1: "Kommune/offentlig eier",
    11: "Fester",
    18: "Rettighetsforhold",
    19: "Annet tinglyst eierforhold",
}


# =============================================================================
# Helper Functions
# =============================================================================

def get_building_type_hierarchy(internal_id: Optional[int]) -> Tuple[str, str, str]:
    """
    Get the building type hierarchy (Level 1, 2, 3) from Kartverket's internal ID.

    The API returns internal IDs (0-127) which need to be converted to NS 3457 codes.
    NS 3457 codes have a hierarchical structure:
    - Level 1: 1-8 (main category / Hovedgruppe)
    - Level 2: 11-84 (building group / Bygningsgruppe)
    - Level 3: 111-999 (specific building type / Bygningstype)

    The hierarchy is derived from the code structure:
    - Code 671 -> Level 2 = 67 -> Level 1 = 6
    - Code 111 -> Level 2 = 11 -> Level 1 = 1

    Args:
        internal_id: Kartverket internal building type ID (0-127)

    Returns:
        Tuple of (level1_name, level2_name, level3_name).
        Empty strings for missing levels.

    Example:
        >>> level1, level2, level3 = get_building_type_hierarchy(104)
        >>> print(f"{level1} > {level2} > {level3}")
        Kultur- og forskningsbygning > Bygning for religiøse aktiviteter > Kirke, kapell
    """
    if internal_id is None:
        return ('', '', '')

    # Convert internal ID to NS 3457 code
    ns3457_code = INTERNAL_ID_TO_NS3457.get(internal_id)
    if ns3457_code is None:
        return ('', '', '')

    # Derive parent codes from the NS 3457 code structure
    code_str = str(ns3457_code)

    if len(code_str) == 3:
        # Level 3 code (e.g., 111 -> level2=11, level1=1)
        level3_code = ns3457_code
        level2_code = int(code_str[:2])
        level1_code = int(code_str[0])
    elif len(code_str) == 2:
        # Level 2 code (e.g., 11 -> level1=1)
        level3_code = None
        level2_code = ns3457_code
        level1_code = int(code_str[0])
    elif len(code_str) == 1:
        # Level 1 code
        level3_code = None
        level2_code = None
        level1_code = ns3457_code
    else:
        # Unknown structure (e.g., 999)
        return (BUILDING_TYPE_CODES.get(ns3457_code, ''), '', '')

    level1_name = BUILDING_TYPE_CODES.get(level1_code, '')
    level2_name = BUILDING_TYPE_CODES.get(level2_code, '') if level2_code else ''
    level3_name = BUILDING_TYPE_CODES.get(level3_code, '') if level3_code else ''

    return (level1_name, level2_name, level3_name)


def get_building_type_name(internal_id: Optional[int]) -> str:
    """
    Get the most specific building type name from Kartverket's internal ID.

    The API returns internal IDs (0-127) which need to be converted to NS 3457 codes
    before looking up the description. This function returns the most specific
    level available (Level 3 if exists, else Level 2, else Level 1).

    Args:
        internal_id: Kartverket internal building type ID (0-127)

    Returns:
        Human-readable building type name, or empty string if not found

    Example:
        >>> get_building_type_name(104)
        'Kirke, kapell'
        >>> get_building_type_name(1)
        'Enebolig'
    """
    level1, level2, level3 = get_building_type_hierarchy(internal_id)
    # Return the most specific level available
    return level3 or level2 or level1


def get_building_status_name(status_code: Optional[int]) -> str:
    """
    Get building status name from status code.

    Args:
        status_code: Building status code

    Returns:
        Human-readable status name, or empty string if not found
    """
    if status_code is None:
        return ''
    return BUILDING_STATUS_CODES.get(status_code, '')


def get_ownership_type_name(ownership_code: Optional[int]) -> str:
    """
    Get ownership type name from ownership code.

    Args:
        ownership_code: Ownership type code

    Returns:
        Human-readable ownership type name, or 'Unknown' if not found
    """
    if ownership_code is None:
        return ''
    return OWNERSHIP_TYPE_CODES.get(ownership_code, f'Unknown ({ownership_code})')


# =============================================================================
# Simplified Building Category Mapping
# =============================================================================

import json
from pathlib import Path

_SIMPLIFIED_CATEGORY_MAPPING: dict[str, str] | None = None
SIMPLIFIED_CATEGORY_FALLBACK = "Annet"
_SIMPLIFIED_CATEGORY_MISSING_TOKENS = {"", "-", "nan", "<na>", "none", "null"}


def _load_simplified_category_mapping() -> dict[str, str]:
    """
    Load the code-to-category mapping from JSON file.

    Returns:
        Dictionary mapping NS 3457 codes (as strings) to Norwegian category names.
    """
    global _SIMPLIFIED_CATEGORY_MAPPING
    if _SIMPLIFIED_CATEGORY_MAPPING is None:
        mapping_file = Path(__file__).parent / "building_category_mapping_simplified.json"
        with open(mapping_file, encoding="utf-8") as f:
            data = json.load(f)
        _SIMPLIFIED_CATEGORY_MAPPING = data.get("code_to_category", {})
    return _SIMPLIFIED_CATEGORY_MAPPING


def normalize_simplified_building_category(value: Any) -> str:
    """Normalize simplified category values and collapse missing placeholders to fallback."""
    if value is None:
        return SIMPLIFIED_CATEGORY_FALLBACK

    if isinstance(value, float) and value != value:
        return SIMPLIFIED_CATEGORY_FALLBACK

    normalized = str(value).strip()
    if normalized.lower() in _SIMPLIFIED_CATEGORY_MISSING_TOKENS:
        return SIMPLIFIED_CATEGORY_FALLBACK
    return normalized


def get_simplified_building_category(ssb_code: Optional[int]) -> str:
    """
    Map NS 3457 building type code to simplified Norwegian category.

    Args:
        ssb_code: NS 3457/SSB building type code (e.g., 613, 721)

    Returns:
        Simplified Norwegian category name (e.g., "Skoler", "Sykehjem og omsorgsboliger"),
        or fallback category "Annet" if code is None or not found.

    Example:
        >>> get_simplified_building_category(613)
        'Skoler'
        >>> get_simplified_building_category(721)
        'Sykehjem og omsorgsboliger'
    """
    if ssb_code is None:
        return SIMPLIFIED_CATEGORY_FALLBACK
    mapping = _load_simplified_category_mapping()
    return mapping.get(str(ssb_code), SIMPLIFIED_CATEGORY_FALLBACK)

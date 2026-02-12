"""
Centralized column name constants for Kartverket/Matrikkel data.

This module provides a single source of truth for all DataFrame column names
used throughout the backend. When API responses or data formats change,
update the values here rather than searching through multiple files.

Usage:
    from app.core.columns import Col, GEONORGE_MAPPING

    # DataFrame operations
    df[Col.KOMMUNE_NR] = "0301"
    row.get(Col.BYGG_ID)

    # API response mapping
    for api_key, col_name in GEONORGE_MAPPING.items():
        df[col_name] = response[api_key]
"""


class Col:
    """DataFrame column names. Single source of truth."""

    # =========================================================================
    # Property Identification
    # =========================================================================
    KOMMUNE_NR = "Kommunenummer"
    GARDS_NR = "Gardsnummer"
    BRUKS_NR = "Bruksnummer"
    FESTE_NR = "Festenummer"
    SEKSJON_NR = "Seksjonsnummer"
    MATRIKKEL_ID = "MatrikkelenhetId"
    KNR_GNR_BNR = "Knr-Gnr-Bnr"  # Computed: "{KNR}-{GNR}-{BNR}"

    # =========================================================================
    # Building Identification
    # =========================================================================
    BYGG_ID = "ByggId"
    BYGNINGS_NR = "Bygningsnummer"

    # =========================================================================
    # Building Type Hierarchy
    # =========================================================================
    BYGNINGSTYPE_KODE_ID = "BygningstypeKodeId"  # Internal Kartverket ID
    BYGNINGSTYPE_KODE_SSB = "BygningstypeKodeSSB"  # NS3457/SSB code
    HOVEDGRUPPE = "Hovedgruppe"  # Level 1: Main group
    BYGNINGSGRUPPE = "Bygningsgruppe"  # Level 2: Building group
    BYGNINGSTYPE = "Bygningstype"  # Level 3: Building type
    FORENKLET_BYGNINGS_KATEGORI = "Forenklet Bygningskategori"  # Simplified building category

    # =========================================================================
    # Building Status
    # =========================================================================
    BYGNINGSSTATUS_KODE_ID = "BygningsstatusKodeId"
    BYGNINGSSTATUS = "Bygningsstatus"
    DATO = "Dato"  # Earliest status date
    TIDLIGSTE_STATUS_DATO = "TidligsteStatusDato"
    TEK_STANDARD = "TEK-standard"
    TEK_IKRAFTTREDELSE = "TEK Ikrafttredelse"
    TEK_PERIODE = "TEK Periode"
    STATUS_REGISTRERT_DATO = "StatusRegistrertDato"
    STATUS_SLETTET_DATO = "StatusSlettetDato"
    STATUS_OPPDATERINGSDATO = "StatusOppdateringsdato"
    STATUS_SLUTTDATO = "StatusSluttdato"
    BYGNINGSSTATUS_HISTORIKK_KODE_IDS = "BygningsstatusHistorikkKodeIds"
    BYGNINGSSTATUS_HISTORIKK = "BygningsstatusHistorikk"

    # =========================================================================
    # Area Measurements
    # =========================================================================
    BRUKSAREAL_TOTALT = "BruksarealTotalt"
    BRUKSAREAL_TIL_BOLIG = "BruksarealTilBolig"
    BRUKSAREAL_TIL_ANNET = "BruksarealTilAnnet"
    BRUTTOAREAL_TOTALT = "BruttoarealTotalt"
    BEBYGD_AREAL = "BebygdAreal"
    ANTALL_BOENHETER = "AntallBoenheter"
    ETASJER = "Etasjer"
    ANTALL_BYGNINGER = "AntallBygninger"

    # =========================================================================
    # Utilities
    # =========================================================================
    HAR_HEIS = "HarHeis"
    OPPVARMING_KODE_IDS = "OppvarmingsKodeIds"
    ENERGIKILDE_KODE_IDS = "EnergikildeKodeIds"
    VANNFORSYNING_KODE_ID = "VannforsyningsKodeId"
    AVLOP_KODE_ID = "AvlopsKodeId"

    # =========================================================================
    # Cultural Heritage
    # =========================================================================
    HAR_SEFRAKMINNE = "HarSefrakminne"
    HAR_KULTURMINNE = "HarKulturminne"
    SKJERMINGSVERDIG = "Skjermingsverdig"

    # =========================================================================
    # Address Data
    # =========================================================================
    ADRESSENAVN = "Adressenavn"
    NUMMER = "Nummer"  # House number
    POSTNUMMER = "Postnummer"
    POSTSTED = "Poststed"
    LAT = "Lat"
    LON = "Lon"
    ADRESSER = "Alt. Adresser"  # Aggregated: semicolon-separated addresses
    ALT_ADRESSER_FRA_KNR_GNR_BNR = "Alt. Adresser fra Knr-Gnr-Bnr"
    ADRESSE = "Adresse"  # Computed: "{Adressenavn} {Nummer}"
    ALT_ADRESSER = "Alt. Adresser"  # Alternative addresses (deprecated)

    # =========================================================================
    # Ownership - Aggregated (per building/property)
    # =========================================================================
    ALLE_EIERE = "AlleEiere"  # Semicolon-separated owner names
    ALLE_EIER_IDER = "AlleEierIder"  # Semicolon-separated org numbers
    ALLE_EIERTYPER = "AlleEiertyper"  # Semicolon-separated types
    ALLE_TINGLYST = "AlleTinglyst"  # Semicolon-separated registration status
    ALLE_EIERFORHOLD_KODE_IDS = "AlleEierforholdKodeIds"  # Semicolon-separated ownership codes (raw)
    ALLE_EIERFORHOLD = "AlleEierforhold"  # Semicolon-separated ownership codes
    ALLE_EIERANDELER = "AlleEierandeler"  # Semicolon-separated percentages
    ANTALL_EIERE = "AntallEiere"

    # =========================================================================
    # Ownership - Per Owner (Ownership sheet)
    # =========================================================================
    EIER_ID = "EierId"  # Owner org number
    NAVN = "Navn"  # Owner name
    EIERTYPE = "Eiertype"  # Person/Organization
    TINGLYST = "Tinglyst"  # Registered/Non-registered
    EIERFORHOLD_KODE_ID = "EierforholdKodeId"
    EIERFORHOLD = "Eierforhold"  # Hjemmelshaver, Fester, etc.
    TELLER = "Teller"  # Share numerator
    NEVNER = "Nevner"  # Share denominator
    EIERANDEL = "Eierandel"  # Share percentage
    EIER_INDEKS = "EierIndeks"  # "1 of 3" format

    # =========================================================================
    # Business Data (Brønnøysund Register)
    # =========================================================================
    UNDERENHETER = "Underenheter"  # Semicolon-separated business names
    ANTALL_UNDERENHETER = "Antall Underenheter"

    # =========================================================================
    # Duplicate Detection
    # =========================================================================
    DUPLIKAT_FLAGG = "DuplikatFlagg"
    DUPLIKAT_GRUPPE = "DuplikatGruppe"

    # =========================================================================
    # Input/Lookup Status (Address Processing)
    # =========================================================================
    # User input columns (English)
    MUNICIPALITY = "Municipality"
    STREET = "Street"
    POSTCODE = "Postcode"
    CITY = "City"
    ORIGINAL_STREET = "OriginalStreet"
    CLEAN_STREET = "CleanStreet"
    TYPE = "Type"
    AREA = "Area"
    ORIGINAL_ROW_ID = "OriginalRowID"
    GOOGLE_MAPS_LINK = "GoogleMapsLink"

    # Processing status
    MATCH_STATUS = "Match Status"
    NOTES = "Notes"
    GEONORGE_SCORE = "GeoNorge Score"
    INPUT_INDEX = "Input Index"
    VARIANT_INDEX = "Variant Index"
    PROTECTOR_SOURCE = "Protector Source"
    ENRICHMENT_STATUS = "Enrichment Status"

    # =========================================================================
    # Summary Sheet (Norwegian labels)
    # =========================================================================
    METRIKK = "Metrikk"
    VERDI = "Verdi"
    ORGANISASJONSNUMMER = "Organisasjonsnummer"
    KOMMUNENAVN = "Kommunenavn"
    TOTALT_EIENDOMMER = "Totalt Eiendommer"
    TOTALT_BYGNINGER = "Totalt Bygninger"
    TOTALT_EIERFORHOLD = "Totalt Eierforhold"
    EIENDOMMER_MED_BYGNINGER = "Eiendommer med Bygninger"
    EIENDOMMER_UTEN_BYGNINGER = "Eiendommer uten Bygninger"
    UNIKE_EIERE = "Unike Eiere"

    # =========================================================================
    # LLM Analysis Categories
    # =========================================================================
    USAGE = "Usage"

    # =========================================================================
    # User Data Aggregation (preserves original BigQuery data for modal display)
    # =========================================================================
    AGG_USER_DATA = "AggUserData"  # JSON string of original user rows
    AGG_USER_DATA_COUNT = "AggUserDataCount"  # Number of original rows for address
    AGG_USER_DATA_TOTAL_AREA = "AggUserDataTotalArea"  # Sum of Area from user data
    AGG_USER_DATA_MISMATCH = "AggUserDataMismatch"  # True if user count != Kartverket count


# =============================================================================
# GeoNorge API Field Mapping
# =============================================================================
# Maps lowercase GeoNorge API response fields to PascalCase DataFrame columns.
# Use this when processing GeoNorge responses to ensure consistent column names.

GEONORGE_MAPPING: dict[str, str] = {
    "kommunenummer": Col.KOMMUNE_NR,
    "gardsnummer": Col.GARDS_NR,
    "bruksnummer": Col.BRUKS_NR,
    "festenummer": Col.FESTE_NR,
    "seksjonsnummer": Col.SEKSJON_NR,
    "adressenavn": Col.ADRESSENAVN,
    "nummer": Col.NUMMER,
    "postnummer": Col.POSTNUMMER,
    "poststed": Col.POSTSTED,
}

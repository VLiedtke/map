"""
Convert raw CSV data → per-country JSON files keyed by ISO2 code (matching world.svg).

Outputs (in resources2/processed/):
  plastic_waste_per_capita.json       — kg/person, 2010  (OWID)
  mismanaged_waste_per_capita.json    — kg/person, 2019  (OWID)
  plastic_imports_per_capita.json     — kg/person, 2017  (UNCTAD)
  plastic_exports_per_capita.json     — kg/person, 2017  (UNCTAD)
  plastic_trade_balance_per_capita.json — kg/person, 2017 (exports - imports)

All values are floats rounded to 4 decimal places. Missing values are omitted.
"""

import csv
import json
import os

BASE = os.path.dirname(__file__)
OUT_DIR = os.path.join(BASE, "processed")
os.makedirs(OUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# ISO3 → ISO2   (standard mapping for all codes appearing in OWID data)
# ---------------------------------------------------------------------------
ISO3_TO_ISO2 = {
    "ABW": "AW", "AFG": "AF", "AGO": "AO", "AIA": "AI", "ALB": "AL",
    "AND": "AD", "ARE": "AE", "ARG": "AR", "ARM": "AM", "ASM": "AS",
    "ATG": "AG", "AUS": "AU", "AUT": "AT", "AZE": "AZ", "BDI": "BI",
    "BEL": "BE", "BEN": "BJ", "BFA": "BF", "BGD": "BD", "BGR": "BG",
    "BHR": "BH", "BHS": "BS", "BIH": "BA", "BLR": "BY", "BLZ": "BZ",
    "BMU": "BM", "BOL": "BO", "BRA": "BR", "BRB": "BB", "BRN": "BN",
    "BTN": "BT", "BWA": "BW", "CAF": "CF", "CAN": "CA", "CHE": "CH",
    "CHL": "CL", "CHN": "CN", "CIV": "CI", "CMR": "CM", "COD": "CD",
    "COG": "CG", "COL": "CO", "COM": "KM", "CPV": "CV", "CRI": "CR",
    "CUB": "CU", "CUW": "CW", "CYM": "KY", "CYP": "CY", "CZE": "CZ",
    "DEU": "DE", "DJI": "DJ", "DMA": "DM", "DNK": "DK", "DOM": "DO",
    "DZA": "DZ", "ECU": "EC", "EGY": "EG", "ERI": "ER", "ESP": "ES",
    "EST": "EE", "ETH": "ET", "FIN": "FI", "FJI": "FJ", "FRA": "FR",
    "FRO": "FO", "FSM": "FM", "GAB": "GA", "GBR": "GB", "GEO": "GE",
    "GHA": "GH", "GIN": "GN", "GMB": "GM", "GNB": "GW", "GRC": "GR",
    "GRD": "GD", "GRL": "GL", "GTM": "GT", "GUY": "GY", "HKG": "HK",
    "HND": "HN", "HRV": "HR", "HTI": "HT", "HUN": "HU", "IDN": "ID",
    "IND": "IN", "IRL": "IE", "IRN": "IR", "IRQ": "IQ", "ISL": "IS",
    "ISR": "IL", "ITA": "IT", "JAM": "JM", "JOR": "JO", "JPN": "JP",
    "KAZ": "KZ", "KEN": "KE", "KGZ": "KG", "KHM": "KH", "KIR": "KI",
    "KNA": "KN", "KOR": "KR", "KWT": "KW", "LAO": "LA", "LBN": "LB",
    "LBR": "LR", "LBY": "LY", "LCA": "LC", "LKA": "LK", "LSO": "LS",
    "LTU": "LT", "LUX": "LU", "LVA": "LV", "MAC": "MO", "MAR": "MA",
    "MDA": "MD", "MDG": "MG", "MDV": "MV", "MEX": "MX", "MKD": "MK",
    "MLI": "ML", "MLT": "MT", "MMR": "MM", "MNG": "MN", "MOZ": "MZ",
    "MRT": "MR", "MSR": "MS", "MUS": "MU", "MWI": "MW", "MYS": "MY",
    "MYT": "YT", "NAM": "NA", "NCL": "NC", "NER": "NE", "NGA": "NG",
    "NIC": "NI", "NLD": "NL", "NOR": "NO", "NPL": "NP", "NRU": "NR",
    "NZL": "NZ", "OMN": "OM", "PAK": "PK", "PAN": "PA", "PER": "PE",
    "PHL": "PH", "PLW": "PW", "PNG": "PG", "POL": "PL", "PRK": "KP",
    "PRT": "PT", "PRY": "PY", "PSE": "PS", "PYF": "PF", "QAT": "QA",
    "ROU": "RO", "RUS": "RU", "RWA": "RW", "SAU": "SA", "SDN": "SD",
    "SEN": "SN", "SGP": "SG", "SLB": "SB", "SLE": "SL", "SLV": "SV",
    "SOM": "SO", "SRB": "RS", "SSD": "SS", "STP": "ST", "SUR": "SR",
    "SVK": "SK", "SVN": "SI", "SWE": "SE", "SWZ": "SZ", "SYC": "SC",
    "SYR": "SY", "TCD": "TD", "TGO": "TG", "THA": "TH", "TJK": "TJ",
    "TKM": "TM", "TLS": "TL", "TON": "TO", "TTO": "TT", "TUN": "TN",
    "TUR": "TR", "TUV": "TV", "TWN": "TW", "TZA": "TZ", "UGA": "UG",
    "UKR": "UA", "URY": "UY", "USA": "US", "UZB": "UZ", "VCT": "VC",
    "VEN": "VE", "VNM": "VN", "VUT": "VU", "WSM": "WS", "YEM": "YE",
    "YTZ": "YT", "ZAF": "ZA", "ZMB": "ZM", "ZWE": "ZW",
}

# ---------------------------------------------------------------------------
# UNCTAD Economy_Label → ISO2  (trade + population files)
# Aggregates/regions are intentionally omitted — they get no ISO2 code.
# ---------------------------------------------------------------------------
UNCTAD_TO_ISO2 = {
    "Afghanistan": "AF", "Albania": "AL", "Algeria": "DZ", "Andorra": "AD",
    "Angola": "AO", "Antigua and Barbuda": "AG", "Argentina": "AR",
    "Armenia": "AM", "Aruba": "AW", "Australia": "AU", "Austria": "AT",
    "Azerbaijan": "AZ", "Bahamas": "BS", "Bahrain": "BH", "Bangladesh": "BD",
    "Barbados": "BB", "Belarus": "BY", "Belgium": "BE", "Belize": "BZ",
    "Benin": "BJ", "Bermuda": "BM", "Bhutan": "BT",
    "Bolivia (Plurinational State of)": "BO",
    "Bosnia and Herzegovina": "BA", "Botswana": "BW", "Brazil": "BR",
    "Brunei Darussalam": "BN", "Bulgaria": "BG", "Burkina Faso": "BF",
    "Burundi": "BI", "Cabo Verde": "CV", "Cambodia": "KH", "Cameroon": "CM",
    "Canada": "CA", "Cayman Islands": "KY", "Central African Republic": "CF",
    "Chile": "CL", "China": "CN", "China, Hong Kong SAR": "HK",
    "China, Macao SAR": "MO", "China, Taiwan Province of": "TW",
    "Colombia": "CO", "Comoros": "KM", "Congo": "CG", "Costa Rica": "CR",
    "Cote d'Ivoire": "CI", "Croatia": "HR", "Cuba": "CU", "Curacao": "CW",
    "Cyprus": "CY", "Czechia": "CZ", "Dem. Rep. of the Congo": "CD",
    "Denmark": "DK", "Djibouti": "DJ", "Dominica": "DM",
    "Dominican Republic": "DO", "Ecuador": "EC", "Egypt": "EG",
    "El Salvador": "SV", "Estonia": "EE", "Eswatini": "SZ", "Ethiopia": "ET",
    "Faroe Islands": "FO", "Fiji": "FJ", "Finland": "FI", "France": "FR",
    "French Polynesia": "PF", "Gabon": "GA", "Gambia": "GM",
    "Georgia": "GE", "Germany": "DE", "Ghana": "GH", "Greece": "GR",
    "Greenland": "GL", "Grenada": "GD", "Guatemala": "GT", "Guinea": "GN",
    "Guinea-Bissau": "GW", "Guyana": "GY", "Honduras": "HN", "Hungary": "HU",
    "Iceland": "IS", "India": "IN", "Indonesia": "ID",
    "Iran (Islamic Republic of)": "IR", "Ireland": "IE", "Israel": "IL",
    "Italy": "IT", "Jamaica": "JM", "Japan": "JP", "Jordan": "JO",
    "Kazakhstan": "KZ", "Kenya": "KE", "Kiribati": "KI", "Kuwait": "KW",
    "Kyrgyzstan": "KG", "Lao People's Dem. Rep.": "LA", "Latvia": "LV",
    "Lebanon": "LB", "Lesotho": "LS", "Liberia": "LR", "Libya": "LY",
    "Lithuania": "LT", "Luxembourg": "LU", "Madagascar": "MG",
    "Malawi": "MW", "Malaysia": "MY", "Maldives": "MV", "Mali": "ML",
    "Malta": "MT", "Mauritania": "MR", "Mauritius": "MU", "Mayotte": "YT",
    "Mexico": "MX", "Micronesia (Federated States of)": "FM",
    "Mongolia": "MN", "Montenegro": "ME", "Montserrat": "MS",
    "Morocco": "MA", "Mozambique": "MZ", "Myanmar": "MM", "Namibia": "NA",
    "Nepal": "NP", "Netherlands (Kingdom of the)": "NL",
    "Netherlands Antilles": None,   # dissolved 2010 — skip
    "New Caledonia": "NC", "New Zealand": "NZ", "Nicaragua": "NI",
    "Niger": "NE", "Nigeria": "NG", "North Macedonia": "MK", "Norway": "NO",
    "Oman": "OM", "Pakistan": "PK", "Palau": "PW", "Panama": "PA",
    "Papua New Guinea": "PG", "Paraguay": "PY", "Peru": "PE",
    "Philippines": "PH", "Poland": "PL", "Portugal": "PT", "Qatar": "QA",
    "Republic of Korea": "KR", "Republic of Moldova": "MD", "Romania": "RO",
    "Russian Federation": "RU", "Rwanda": "RW",
    "Saint Kitts and Nevis": "KN", "Saint Lucia": "LC",
    "Saint Vincent and the Grenadines": "VC", "Samoa": "WS",
    "Sao Tome and Principe": "ST", "Saudi Arabia": "SA", "Senegal": "SN",
    "Serbia": "RS", "Serbia and Montenegro": None,  # dissolved 2006 — skip
    "Seychelles": "SC", "Sierra Leone": "SL", "Singapore": "SG",
    "Slovakia": "SK", "Slovenia": "SI", "Solomon Islands": "SB",
    "South Africa": "ZA", "Spain": "ES", "Sri Lanka": "LK",
    "State of Palestine": "PS", "Sudan": "SD",
    "Sudan (...2011)": None,        # historical aggregate — skip
    "Suriname": "SR", "Sweden": "SE", "Switzerland": "CH",
    "Syrian Arab Republic": "SY", "Tajikistan": "TJ", "Thailand": "TH",
    "Timor-Leste": "TL", "Togo": "TG", "Tonga": "TO",
    "Trinidad and Tobago": "TT", "Tunisia": "TN", "Turkiye": "TR",
    "Turks and Caicos Islands": "TC", "Uganda": "UG", "Ukraine": "UA",
    "United Arab Emirates": "AE", "United Kingdom": "GB",
    "United Republic of Tanzania": "TZ", "United States": "US",
    "Uruguay": "UY", "Uzbekistan": "UZ", "Vanuatu": "VU",
    "Venezuela (Bolivarian Rep. of)": "VE", "Viet Nam": "VN",
    "Yemen": "YE", "Zambia": "ZM", "Zimbabwe": "ZW",
}

# ---------------------------------------------------------------------------
# 2017 population estimates by ISO2 (thousands of persons)
# Source: UN World Population Prospects 2022 Revision
# Used to convert UNCTAD trade totals (thousand metric tons) to per-capita kg
# ---------------------------------------------------------------------------
POP_2017 = {  # thousands of persons
    "AD": 77,       "AE": 9400,     "AF": 34656,    "AG": 103,
    "AL": 2877,     "AM": 2986,     "AO": 29784,    "AR": 44272,
    "AS": 56,       "AT": 8797,     "AU": 24598,    "AW": 105,
    "AZ": 9869,     "BA": 3503,     "BB": 286,      "BD": 161793,
    "BE": 11350,    "BF": 19193,    "BG": 7050,     "BH": 1649,
    "BI": 10864,    "BJ": 11175,    "BM": 64,       "BN": 429,
    "BO": 11079,    "BR": 207833,   "BS": 393,      "BT": 757,
    "BW": 2254,     "BY": 9468,     "BZ": 381,      "CA": 36708,
    "CD": 82243,    "CF": 4659,     "CG": 5261,     "CH": 8467,
    "CI": 24905,    "CK": 18,       "CL": 18470,    "CM": 24566,
    "CN": 1409517,  "CO": 49066,    "CR": 4905,     "CU": 11339,
    "CV": 546,      "CW": 161,      "CY": 1180,     "CZ": 10578,
    "DE": 82695,    "DJ": 971,      "DK": 5769,     "DM": 72,
    "DO": 10735,    "DZ": 41831,    "EC": 16906,    "EE": 1315,
    "EG": 97553,    "ER": 3474,     "ES": 46561,    "ET": 105045,
    "FI": 5517,     "FJ": 883,      "FM": 113,      "FO": 49,
    "FR": 67118,    "GA": 2051,     "GB": 66181,    "GD": 112,
    "GE": 3717,     "GH": 29122,    "GL": 56,       "GM": 2101,
    "GN": 12717,    "GQ": 1268,     "GR": 10753,    "GT": 16913,
    "GW": 1861,     "GY": 779,      "HK": 7425,     "HN": 9265,
    "HR": 4130,     "HT": 10982,    "HU": 9723,     "ID": 263991,
    "IE": 4761,     "IL": 8680,     "IN": 1338676,  "IQ": 37550,
    "IR": 81163,    "IS": 338,      "IT": 60551,    "JM": 2890,
    "JO": 9903,     "JP": 126785,   "KE": 50950,    "KG": 6201,
    "KH": 15918,    "KI": 116,      "KM": 832,      "KN": 55,
    "KP": 25490,    "KR": 51361,    "KW": 4137,     "KY": 64,
    "KZ": 18037,    "LA": 6858,     "LB": 6855,     "LC": 178,
    "LK": 21444,    "LR": 4853,     "LS": 2091,     "LT": 2847,
    "LU": 590,      "LV": 1940,     "LY": 6375,     "MA": 35740,
    "MD": 3553,     "ME": 628,      "MG": 25571,    "MK": 2082,
    "ML": 19418,    "MM": 53371,    "MN": 3121,     "MO": 622,
    "MR": 4301,     "MS": 5,        "MT": 476,      "MU": 1265,
    "MV": 530,      "MW": 18143,    "MX": 129163,   "MY": 31528,
    "MZ": 29669,    "NA": 2534,     "NC": 278,      "NE": 21477,
    "NG": 190873,   "NI": 6218,     "NL": 17132,    "NO": 5285,
    "NP": 29305,    "NR": 11,       "NZ": 4793,     "OM": 4636,
    "PA": 4111,     "PE": 31989,    "PF": 282,      "PG": 8606,
    "PH": 104918,   "PK": 212228,   "PL": 37976,    "PT": 10293,
    "PW": 18,       "PY": 6811,     "QA": 2639,     "RO": 19521,
    "RS": 6943,     "RU": 143690,   "RW": 12208,    "SA": 32938,
    "SB": 636,      "SC": 95,       "SD": 40813,    "SE": 9910,
    "SG": 5709,     "SI": 2079,     "SK": 5439,     "SL": 7557,
    "SM": 33,       "SN": 15854,    "SO": 14742,    "SR": 580,
    "SS": 11091,    "ST": 211,      "SV": 6378,     "SY": 19398,
    "SZ": 1141,     "TC": 38,       "TG": 7798,     "TH": 69210,
    "TJ": 8921,     "TL": 1269,     "TN": 11532,    "TO": 100,
    "TR": 82017,    "TT": 1378,     "TV": 11,       "TW": 23572,
    "TZ": 57310,    "UA": 44831,    "UG": 42729,    "US": 325147,
    "UY": 3456,     "UZ": 32388,    "VC": 110,      "VE": 28838,
    "VN": 95546,    "VU": 276,      "WS": 197,      "YE": 27584,
    "YT": 253,      "ZA": 56717,    "ZM": 17094,    "ZW": 14415,
    "PS": 4685,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"  Written {len(data)} countries → {os.path.relpath(path, BASE)}")


def parse_owid(filepath, value_col):
    """Return {iso2: float} from an OWID-style CSV (Entity, Code, Year, value).
    Only keeps rows with a valid ISO3 Code and a non-empty value.
    Picks the most recent year per country.
    """
    result = {}
    with open(filepath, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            iso3 = row["Code"].strip()
            if not iso3 or iso3.startswith("OWID_"):
                continue
            iso2 = ISO3_TO_ISO2.get(iso3)
            if iso2 is None:
                continue
            val_str = row[value_col].strip()
            if not val_str:
                continue
            try:
                val = float(val_str)
            except ValueError:
                continue
            # keep most recent year (file may have multiple years per country)
            year = int(row["Year"])
            if iso2 not in result or year > result[iso2][1]:
                result[iso2] = (val, year)
    return {k: round(v, 4) for k, (v, _) in result.items()}


def parse_trade(filepath, year):
    """Return {iso2: value_thousand_mt} for a given year from UNCTAD wide CSV.
    MissingValue flag == '1' → treat as null.
    """
    year_col = f"{year}_Metric_tons_in_thousands_Value"
    miss_col = f"{year}_Metric_tons_MissingValue"

    result = {}
    with open(filepath, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["Economy_Label"].strip().strip('"')
            iso2 = UNCTAD_TO_ISO2.get(name)
            if iso2 is None:
                continue

            miss = row.get(miss_col, "").strip()
            if miss == "1":
                continue  # explicitly flagged missing

            val_str = row.get(year_col, "").strip()
            if not val_str:
                continue  # empty cell
            try:
                val = float(val_str)
            except ValueError:
                continue
            result[iso2] = val
    return result


def trade_to_per_capita(trade_dict):
    """Convert thousand metric tons → kg/person using POP_2017."""
    out = {}
    for iso2, val_k_mt in trade_dict.items():
        pop = POP_2017.get(iso2)
        if pop is None or pop == 0:
            continue
        # val_k_mt × 1000 MT × 1000 kg/MT / (pop × 1000 persons)
        # = val_k_mt × 1e6 / (pop × 1e3) = val_k_mt × 1000 / pop
        kg_per_person = val_k_mt * 1000.0 / pop
        out[iso2] = round(kg_per_person, 4)
    return out


# ---------------------------------------------------------------------------
# 1. Plastic waste per capita  (OWID, 2010)
# ---------------------------------------------------------------------------
print("Processing plastic waste per capita…")
plastic_waste = parse_owid(
    os.path.join(BASE, "plastic-waste-per-capita.csv"),
    "Per capita plastic waste"
)
write_json(os.path.join(OUT_DIR, "plastic_waste_per_capita.json"), plastic_waste)

# ---------------------------------------------------------------------------
# 2. Mismanaged waste per capita  (OWID, 2019)
# ---------------------------------------------------------------------------
print("Processing mismanaged waste per capita…")
mismanaged = parse_owid(
    os.path.join(BASE, "mismanaged-plastic-waste-per-capita.csv"),
    "Mismanaged plastic waste per capita"
)
write_json(os.path.join(OUT_DIR, "mismanaged_waste_per_capita.json"), mismanaged)

# ---------------------------------------------------------------------------
# 3 & 4. Trade imports / exports — use 2017 (fewest nulls in both files)
# ---------------------------------------------------------------------------
TRADE_YEAR = 2017

print(f"Processing trade data (year {TRADE_YEAR})…")
imp_raw = parse_trade(
    os.path.join(BASE, "US.PlasticsTradebyPartner_20260530_204708_imports.csv"),
    TRADE_YEAR
)
exp_raw = parse_trade(
    os.path.join(BASE, "US.PlasticsTradebyPartner_20260530_204716_exports.csv"),
    TRADE_YEAR
)

imp_pc = trade_to_per_capita(imp_raw)
exp_pc = trade_to_per_capita(exp_raw)

write_json(os.path.join(OUT_DIR, "plastic_imports_per_capita.json"), imp_pc)
write_json(os.path.join(OUT_DIR, "plastic_exports_per_capita.json"), exp_pc)

# ---------------------------------------------------------------------------
# 5. Trade balance per capita  (exports - imports)
#    Only include countries that have BOTH values.
# ---------------------------------------------------------------------------
print("Processing trade balance…")
balance = {}
all_countries = set(imp_pc) | set(exp_pc)
for iso2 in all_countries:
    exp_val = exp_pc.get(iso2)
    imp_val = imp_pc.get(iso2)
    if exp_val is None or imp_val is None:
        # If one side is missing, we skip — a balance without both sides is misleading.
        continue
    balance[iso2] = round(exp_val - imp_val, 4)

write_json(os.path.join(OUT_DIR, "plastic_trade_balance_per_capita.json"), balance)

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
print("\nDone.")
print(f"  plastic_waste_per_capita:        {len(plastic_waste)} countries")
print(f"  mismanaged_waste_per_capita:     {len(mismanaged)} countries")
print(f"  plastic_imports_per_capita:      {len(imp_pc)} countries")
print(f"  plastic_exports_per_capita:      {len(exp_pc)} countries")
print(f"  plastic_trade_balance_per_capita:{len(balance)} countries")

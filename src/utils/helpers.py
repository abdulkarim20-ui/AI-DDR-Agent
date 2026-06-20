import re

def validate_field(value, field_name="field"):
    """Return value or 'Not Available' string."""
    if not value or value.strip() in ("", "None", "null"):
        return "Not Available"
    return value.strip()

def count_field_coverage(text):
    """Count how many key engineering fields appear in extracted text."""
    key_terms = [
        "location", "area", "defect", "crack", "moisture", "water",
        "severity", "damage", "inspection", "observation", "temperature",
        "thermal", "recommendation", "root cause", "remediation"
    ]
    text_lower = text.lower()
    found = sum(1 for term in key_terms if term in text_lower)
    return found, len(key_terms)

def clean_text_for_pdf(text):
    """Replace non-standard characters with standard ASCII to prevent black squares in PDF."""
    if not isinstance(text, str):
        return text
    replacements = {
        '–': '-', '—': '-',
        '“': '"', '”': '"',
        '‘': "'", '’': "'",
        '•': '-',
        '\u2010': '-', '\u2011': '-', '\u2012': '-', '\u2013': '-', '\u2014': '-', '\u2015': '-',
        '\u2212': '-', '\xad': '-',
        '\u2018': "'", '\u2019': "'",
        '\u201c': '"', '\u201d': '"',
        '\u2022': '-',
        '\u25A0': '-', '\u25AA': '-', '\u25CF': '-',
        '\u00A0': ' ',
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    return text

AREA_KEYWORDS = {
    "Hall": ["hall", "living room", "drawing room", "lounge"],
    "Kitchen": ["kitchen"],
    "Bedroom": ["bedroom", "common bedroom"],
    "Master Bedroom": ["master bedroom", "mb bathroom", "master bed room"],
    "Bathroom / WC": ["bathroom", "wc", "toilet", "washroom"],
    "External Wall": ["external wall", "facade", "elevation", "parapet"],
    "Parking Area": ["parking"],
    "Ceiling": ["ceiling"],
    "Plumbing": ["plumbing", "pipe", "seepage", "leakage", "drainage"],
}

def detect_area(text: str):
    if not text:
        return None
    t = text.lower()
    best_area, best_hits = None, 0
    for area, kws in AREA_KEYWORDS.items():
        hits = sum(1 for kw in kws if kw in t)
        if hits > best_hits:
            best_hits, best_area = hits, area
    return best_area


def parse_photo_area_map(full_text: str) -> dict:
    """
    Walks structured inspection forms of this shape:
        Negative side Description   <area + issue text>
        Negative side photographs
        Photo 1 Photo 2 Photo 3 ...
    and maps every 'Photo N' to the description text that precedes it.
    Returns {} gracefully if the report doesn't use this layout — callers
    must fall back to spatial-proximity matching in that case.
    """
    photo_area_map = {}
    current_desc = None
    lines = full_text.replace("\r", "").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if re.match(r'^(Negative|Positive)\s+side\s+Description', line, re.IGNORECASE):
            desc_parts = [re.sub(r'^(Negative|Positive)\s+side\s+Description\s*', '', line, flags=re.IGNORECASE)]
            j = i + 1
            while j < len(lines) and not re.search(r'side\s+photographs', lines[j], re.IGNORECASE):
                if lines[j].strip():
                    desc_parts.append(lines[j].strip())
                j += 1
            current_desc = " ".join(p for p in desc_parts if p).strip()
            i = j
            continue

        if re.search(r'side\s+photographs', line, re.IGNORECASE):
            j = i + 1
            while j < len(lines) and re.search(r'Photo\s+\d+', lines[j]):
                for n in re.findall(r'Photo\s+(\d+)', lines[j]):
                    if current_desc:
                        photo_area_map.setdefault(int(n), current_desc)
                j += 1
            i = j
            continue

        i += 1

    return photo_area_map

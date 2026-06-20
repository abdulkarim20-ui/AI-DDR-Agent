import re
from src.utils.helpers import detect_area

def enforce_image_placement(ddr_content: str, all_images_list: list) -> str:
    if not all_images_list:
        return ddr_content

    sec_pattern = re.compile(r'(## 2\. Area-wise Observations.*?)(?=\n## 3\.)', re.DOTALL)
    match = sec_pattern.search(ddr_content)
    if not match:
        return ddr_content

    section2 = match.group(1)
    section2_clean = re.sub(r'\n?\[(?:INSP|THERM)_IMG_\d+\]\n?', '\n', section2)

    heading_pattern = re.compile(r'(###\s*[^\n]+)')
    pieces = heading_pattern.split(section2_clean)
    rebuilt = [pieces[0]]
    remaining = list(all_images_list)

    for i in range(1, len(pieces), 2):
        heading = pieces[i]
        body = pieces[i + 1] if i + 1 < len(pieces) else ""
        heading_area = heading.replace("###", "").strip()

        matched = [img for img in remaining
                   if img.get("area") and img["area"].lower() in heading_area.lower()]

        block = heading + body
        for img in matched:
            tag = f"\n[{img['id']}]\n"
            if img.get("area_source") == "vision" and img.get("vision_result"):
                v = img["vision_result"]
                tag += (f"*AI visual classification (confidence: {v['confidence']}): "
                        f"{v['description']} — likely defect: {v['defect_type']}*\n")
            elif img.get("area_raw"):
                tag += f"*Source caption: {img['area_raw']}*\n"
            block += tag
            remaining.remove(img)
        rebuilt.append(block)

    section2_final = "".join(rebuilt)

    if remaining:
        # Thermal images (and anything else with no determinable area) land
        # here — explicitly, instead of being guessed into the wrong room.
        section2_final += "\n\n### Thermal / Unclassified Readings (Area Not Specified in Source)\n"
        section2_final += (
            "The source document did not specify a room/area for the items below. "
            "Cross-reference with the inspection photos is recommended for exact location.\n"
        )
        for img in remaining:
            meta = img.get("thermal_meta") or {}
            v = img.get("vision_result")
            cap = f"\n[{img['id']}]\n"
            if meta:
                cap += (f"*Thermal reading — Hotspot: {meta.get('hotspot_c','Not Available')}°C, "
                        f"Coldspot: {meta.get('coldspot_c','Not Available')}°C*\n")
            if v and v["area"] == "Unclear":
                cap += f"*AI visual note (low confidence): {v['description']}*\n"
            section2_final += cap

    return ddr_content[:match.start(1)] + section2_final + ddr_content[match.end(1):]

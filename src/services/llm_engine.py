import re
import os
from groq import Groq
from dotenv import load_dotenv

from src.utils.helpers import count_field_coverage, validate_field

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def detect_conflicts(inspection_text, thermal_text):
    """
    Compare inspection vs thermal report for conflicting information.
    Returns: (conflict_found: bool, conflict_summaries: list)
    """
    if thermal_text == "Not Available":
        return False, ["No thermal data available for conflict check."]

    conflicts = []

    # Severity keyword sets
    high_severity = {"critical", "severe", "major", "urgent", "dangerous"}
    low_severity = {"minor", "negligible", "slight", "minimal", "low"}

    insp_lower = inspection_text.lower()
    therm_lower = thermal_text.lower()

    insp_high = any(w in insp_lower for w in high_severity)
    insp_low = any(w in insp_lower for w in low_severity)
    therm_high = any(w in therm_lower for w in high_severity)
    therm_low = any(w in therm_lower for w in low_severity)

    # Check severity contradiction
    if insp_high and therm_low:
        conflicts.append(
            "Severity Conflict: Inspection report indicates HIGH/CRITICAL severity, "
            "but Thermal report suggests LOW/MINOR severity. Review field data."
        )
    elif insp_low and therm_high:
        conflicts.append(
            "Severity Conflict: Inspection report indicates LOW severity, "
            "but Thermal report indicates HIGH/CRITICAL severity. Verify readings."
        )

    # Area/location conflict check
    location_pattern = re.compile(
        r'\b(roof|wall|floor|ceiling|basement|foundation|column|beam|slab|balcony|terrace)\b',
        re.IGNORECASE
    )
    insp_areas = set(m.lower() for m in location_pattern.findall(inspection_text))
    therm_areas = set(m.lower() for m in location_pattern.findall(thermal_text))

    only_in_thermal = therm_areas - insp_areas
    if only_in_thermal:
        conflicts.append(
            f"Area Conflict: Thermal report mentions area(s) not found in inspection report: "
            f"{', '.join(only_in_thermal).title()}. "
            f"These areas may have been missed during inspection."
        )

    if conflicts:
        return True, conflicts
    else:
        return False, ["No significant conflicts detected between inspection and thermal reports."]


def calculate_confidence(inspection_text, thermal_text, insp_images, therm_images):
    """
    Confidence = Document Completeness (40%) + Field Coverage (35%) + Image Availability (25%)
    """
    score = 0.0
    breakdown = {}

    # A) Document Completeness (40 pts)
    doc_score = 0
    if inspection_text != "Not Available" and len(inspection_text) > 100:
        doc_score += 25
    elif inspection_text != "Not Available":
        doc_score += 10

    if thermal_text != "Not Available" and len(thermal_text) > 100:
        doc_score += 15
    elif thermal_text != "Not Available":
        doc_score += 5

    breakdown["Document Completeness"] = f"{doc_score}/40"
    score += doc_score

    # B) Field Coverage (35 pts)
    combined_text = inspection_text + " " + thermal_text
    found, total = count_field_coverage(combined_text)
    field_score = round((found / total) * 35)
    breakdown["Field Coverage"] = f"{field_score}/35 ({found}/{total} key terms found)"
    score += field_score

    # C) Image Availability (25 pts)
    total_images = len(insp_images) + len(therm_images)
    if total_images >= 5:
        img_score = 25
    elif total_images >= 2:
        img_score = 15
    elif total_images == 1:
        img_score = 8
    else:
        img_score = 0
    breakdown["Image Availability"] = f"{img_score}/25 ({total_images} image(s) extracted)"
    score += img_score

    return int(score), breakdown


def generate_ddr(inspection_text, thermal_text, conflict_summary, confidence, available_images):
    """Call Groq LLM to generate DDR with exact 7 sections and in-context image placeholders."""

    insp_safe = validate_field(inspection_text, "Inspection Report")
    therm_safe = validate_field(thermal_text, "Thermal Report")

    # Format available images for LLM to place in-context
    images_instruction = ""
    if available_images:
        images_instruction = "\nAVAILABLE IMAGES FOR REFERENCE IN REPORT:\n"
        for img in available_images:
            area_label = img.get("area") or "Unclassified"
            images_instruction += (
                f"- Image Tag: [{img['id']}] | Detected Area: {area_label} | "
                f"Page: {img['page_num']} | Context: \"{img['context']}\"\n"
            )
        images_instruction += (
            "\nSTRICT IMAGE PLACEMENT RULES:\n"
            "1. In Section 2 (Area-wise Observations), create one '### <AreaName>' sub-heading "
            "for every building area you discuss (e.g. '### Kitchen', '### Hall', '### Roof').\n"
            "2. Place each image tag on its own line directly under the '### <AreaName>' heading "
            "matching its 'Detected Area' value above.\n"
            "3. Never group all image tags at the end. Never put a tag under the wrong heading.\n"
            "4. Do not invent tags not listed above.\n"
        )
    else:
        images_instruction = "\nNo images are available in source documents. Do not insert any image tags.\n"

    prompt = f"""You are a senior civil engineering inspection specialist generating a professional Detailed Defect Report (DDR).

INSPECTION REPORT DATA:
{insp_safe}

THERMAL REPORT DATA:
{therm_safe}

CONFLICT ANALYSIS RESULT:
{conflict_summary}
{images_instruction}
STRICT RULES:
1. If any data is missing or unclear → write exactly "Not Available" for that item.
2. Do NOT assume or fabricate any data not present in the input.
3. Use precise technical language appropriate for engineering reports.
4. For every defect, reference its location and area if mentioned.
5. Be specific about severity reasoning — do not just say "high" without explaining why.
6. Do NOT use Markdown tables (i.e. do not use `|` characters). Use bulleted or numbered lists instead.

Generate the DDR using EXACTLY these 7 required section headings:

---

## 1. Property Issue Summary
Provide a concise executive summary of all identified property issues. Include property location (if mentioned), date of inspection (if mentioned), and a high-level overview of the condition. If any info is unavailable, write "Not Available".

## 2. Area-wise Observations
List observations organized by building area/zone (e.g., Roof, Walls, Foundation, Electrical, Plumbing). For each area, describe:
- Visual observations
- Thermal observations (if thermal data is available)
- Specific defects noted
If an area has no data, write "Not Available".

## 3. Probable Root Cause
Analyze and explain the most probable root causes for the identified defects. Group by defect type if multiple issues exist. Base reasoning only on the provided data.

## 4. Severity Assessment (with Reasoning)
Assess the overall severity of each defect on a scale:
- CRITICAL: Immediate safety risk or structural failure imminent
- HIGH: Significant damage requiring urgent repair within 30 days
- MEDIUM: Moderate damage requiring attention within 3 months
- LOW: Minor issues for routine maintenance
Provide explicit reasoning for each rating based on the evidence in the reports.

## 5. Recommended Actions
List specific, actionable repair and remediation steps. Prioritize by severity. Include:
- Immediate actions (for CRITICAL/HIGH)
- Short-term actions (1–3 months)
- Long-term preventive measures
If insufficient data exists, write "Not Available".

## 6. Additional Notes
Include any supplementary information such as:
- Observations from thermal imaging not captured in visual inspection
- Environmental factors affecting the assessment
- Limitations of this report
- Suggested specialist consultations

## 7. Missing or Unclear Information
List explicitly what information was missing, unclear, or unavailable in the source documents. For each item, state what data would be needed for a more complete assessment.

---

IMPORTANT: Maintain the exact section numbers and headings above.

AI Confidence Score: {confidence}%
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional civil engineering report writer. "
                    "Generate structured, precise, and technically accurate DDR reports. "
                    "Always follow the exact section structure provided. "
                    "Never fabricate data — use 'Not Available' for missing information."
                )
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )

    return response.choices[0].message.content

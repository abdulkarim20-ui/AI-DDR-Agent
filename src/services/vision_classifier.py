import base64
import json
import re
from groq import Groq
import os
from dotenv import load_dotenv

load_dotenv()
vision_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

VALID_AREAS = [
    "Hall", "Kitchen", "Bedroom", "Master Bedroom", "Bathroom", "WC",
    "External Wall", "Parking", "Ceiling", "Roof", "Terrace", "Staircase",
    "Plumbing", "Electrical", "Foundation", "Balcony", "Unclear"
]

def classify_image_with_vision(img_bytes: bytes, ext: str, hint_context: str = "") -> dict:
    """
    Uses a vision-capable LLM to look at the actual image and classify:
      - which building area/room it most likely shows
      - what defect/condition is visible
      - confidence level
    This is a FALLBACK only — used when text/caption-based matching in
    pdf_extractor.py could not determine the area with confidence
    (e.g. thermal camera images with no room label in the source text).
    """
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    mime = "image/png" if ext.lower() == "png" else "image/jpeg"
    data_url = f"data:{mime};base64,{b64}"

    prompt = (
        "You are a civil engineering inspection assistant. Look at this photo "
        "from a building defect inspection report and respond with ONLY a JSON "
        "object, no extra text, in this exact schema:\n"
        f'{{"area": "<one of: {", ".join(VALID_AREAS)}>", '
        '"defect_type": "<short label, e.g. dampness, crack, tile hollowness, '
        'corrosion, seepage, paint peeling, none>", '
        '"description": "<one plain-language sentence describing only what is '
        'visibly present in the photo>", '
        '"confidence": "<high|medium|low>"}\n\n'
        "Rules:\n"
        "- Only describe what is visibly present. Do not invent details.\n"
        "- If the room/area cannot be determined from the image alone, set "
        'area to "Unclear" and confidence to "low".\n'
        "- Do not guess based on assumptions about typical floor plans.\n"
    )
    if hint_context:
        prompt += f"\nContext text found near this image in the source document: \"{hint_context}\"\n"

    try:
        response = vision_client.chat.completions.create(
            model=VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}}
                ]
            }],
            temperature=0.1,
            max_tokens=300,
        )
        raw = response.choices[0].message.content.strip()

        # Robust JSON extraction in case the model wraps it in ```json fences
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        data = json.loads(match.group(0)) if match else {}

        area = data.get("area", "Unclear")
        if area not in VALID_AREAS:
            area = "Unclear"

        return {
            "area": area,
            "defect_type": data.get("defect_type", "Not Available"),
            "description": data.get("description", "Not Available"),
            "confidence": data.get("confidence", "low"),
            "source": "AI visual classification",
        }
    except Exception as e:
        return {
            "area": "Unclear",
            "defect_type": "Not Available",
            "description": f"Vision classification unavailable: {e}",
            "confidence": "low",
            "source": "AI visual classification (failed)",
        }

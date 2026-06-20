import io
import re
import hashlib
import pdfplumber
from src.utils.helpers import detect_area, parse_photo_area_map
from src.services.vision_classifier import classify_image_with_vision

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = hasattr(fitz, "open")
except ImportError:
    PYMUPDF_AVAILABLE = False

def _find_caption_photo_number(page, rect):
    """Find the 'Photo N' caption immediately below an image — far more
    reliable than nearest-text-block matching for forms with photo grids."""
    try:
        words = page.get_text("words")
        line_words = {}
        for w in words:
            x0, y0, _, _, word = w[0], w[1], w[2], w[3], w[4]
            line_words.setdefault(round(y0, 1), []).append((x0, word))
        lines = []
        for y, items in line_words.items():
            items.sort()
            lines.append((y, " ".join(w for _, w in items)))

        best, best_dist = None, float("inf")
        for y, text in lines:
            m = re.match(r'^Photo\s+(\d+)$', text.strip())
            if m and y >= rect.y0:
                dist = abs(y - rect.y1)
                if dist < best_dist:
                    best_dist, best = dist, int(m.group(1))
        return best
    except Exception:
        return None

def extract_pdf_data(uploaded_file, prefix="INSP"):
    """
    Extracts text page-by-page and extracts images, associating each image
    with its page number and a contextual text snippet.
    """
    pages_text = []
    images = []
    seen_hashes = set()   # NEW — tracks image content already captured
    
    uploaded_file.seek(0)
    file_bytes = uploaded_file.read()
    uploaded_file.seek(0)
    
    # --- Try PyMuPDF (fitz) first ---
    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            
            # Pass 1: get full text first, to build the photo->area map
            full_text_pass1 = "\n".join((doc[p].get_text() or "") for p in range(len(doc)))
            photo_area_map = parse_photo_area_map(full_text_pass1)   # {} for thermal-style PDFs

            img_counter = 1
            for page_index in range(len(doc)):
                page = doc[page_index]
                text = page.get_text() or ""
                text_clean = text.replace("\r", "").strip()
                pages_text.append(text_clean)
                
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    
                    # Filter out small decorative images and logos (e.g. width or height < 150px)
                    img_w = base_image.get("width", 0)
                    img_h = base_image.get("height", 0)
                    if img_w < 150 or img_h < 150:
                        continue
                        
                    img_bytes = base_image["image"]
                    
                    # NEW: skip exact duplicate images (e.g. same photo appearing in
                    # both the inline "Impacted Area" section and the Appendix)
                    img_hash = hashlib.md5(img_bytes).hexdigest()
                    if img_hash in seen_hashes:
                        continue
                    seen_hashes.add(img_hash)
                    
                    ext = base_image["ext"]
                    
                    img_id = f"{prefix}_IMG_{img_counter}"
                    # Advanced context extraction using spatial block distance:
                    snippet = ""
                    try:
                        rects = page.get_image_rects(xref)
                        if rects:
                            rect = rects[0]
                            blocks = page.get_text("blocks")
                            # block[6] == 0 is text block. block structure: (x0, y0, x1, y1, "text", block_no, block_type)
                            text_blocks = [b for b in blocks if len(b) > 6 and b[6] == 0]
                            if text_blocks:
                                img_center = ((rect.x0 + rect.x1)/2, (rect.y0 + rect.y1)/2)
                                def dist_to_img(b):
                                    b_center = ((b[0] + b[2])/2, (b[1] + b[3])/2)
                                    return (b_center[0] - img_center[0])**2 + (b_center[1] - img_center[1])**2
                                text_blocks.sort(key=dist_to_img)
                                # Take closest 2 text blocks
                                closest_text = " ".join([b[4].strip() for b in text_blocks[:2]])
                                snippet = closest_text.replace("\n", " ").strip()
                    except Exception:
                        pass
                    
                    if not snippet:
                        snippet = text_clean[:300].replace("\n", " ") + "..." if text_clean else "No text on page."
                    
                    if len(snippet) > 300:
                        snippet = snippet[:300] + "..."

                    # NEW: try caption-based matching first
                    rects = page.get_image_rects(xref)
                    photo_num = None
                    if rects:
                        photo_num = _find_caption_photo_number(page, rects[0])

                    area_raw = None
                    if photo_num is not None and photo_num in photo_area_map:
                        area_raw = photo_area_map[photo_num]
                        area = detect_area(area_raw)
                        snippet = area_raw
                    else:
                        if prefix == "THERM":
                            area = None
                        else:
                            area = detect_area(snippet) or detect_area(text_clean[:500])

                    vision_result = None
                    if area is None:   # text/caption matching found nothing — fall back to vision
                        vision_result = classify_image_with_vision(img_bytes, ext, hint_context=snippet)
                        if vision_result["confidence"] in ("high", "medium") and vision_result["area"] != "Unclear":
                            area = vision_result["area"]
                            area_source = "vision"
                        else:
                            area_source = "none"
                    else:
                        area_source = "caption"

                    images.append({
                        "id": img_id,
                        "bytes": img_bytes,
                        "ext": ext,
                        "page_num": page_index + 1,
                        "context": snippet,
                        "area": area,
                        "area_source": area_source,          # NEW — "caption" | "vision" | "none"
                        "vision_result": vision_result,      # NEW — full vision output, or None
                        "area_raw": area_raw,
                        "photo_num": photo_num
                    })

                    # If thermal, extract hotspot/coldspot metadata
                    if prefix == "THERM":
                        therm_meta = {}
                        m_hot = re.search(r'Hotspot\s*:\s*([\d.]+)\s*°?C', text_clean)
                        m_cold = re.search(r'Coldspot\s*:\s*([\d.]+)\s*°?C', text_clean)
                        m_file = re.search(r'Thermal image\s*:\s*(\S+)', text_clean)
                        if m_hot: therm_meta["hotspot_c"] = m_hot.group(1)
                        if m_cold: therm_meta["coldspot_c"] = m_cold.group(1)
                        if m_file: therm_meta["filename"] = m_file.group(1)
                        images[-1]["thermal_meta"] = therm_meta

                    img_counter += 1
                    if len(images) >= 10:  # limit to avoid memory overload
                        break
                if len(images) >= 10:
                    break
            doc.close()
            full_text = "\n".join([p for p in pages_text if p])
            return full_text if full_text.strip() else "Not Available", pages_text, images
        except Exception:
            pass  # Fail over to pdfplumber
            
    # --- Fallback: pdfplumber ---
    try:
        pages_text = []
        images = []
        img_counter = 1
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page_index, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                text_clean = text.replace("\r", "").strip()
                pages_text.append(text_clean)
                
                for img in page.images:
                    try:
                        # Filter out small decorative images and logos (e.g. width or height < 150px)
                        img_w = img.get("width", 0)
                        img_h = img.get("height", 0)
                        if img_w < 150 or img_h < 150:
                            continue
                            
                        x0, top, x1, bottom = img["x0"], img["top"], img["x1"], img["bottom"]
                        cropped = page.within_bbox((x0, top, x1, bottom)).to_image(resolution=100)
                        img_buf = io.BytesIO()
                        cropped.save(img_buf, format="PNG")
                        img_bytes = img_buf.getvalue()
                        
                        # NEW: skip exact duplicate images
                        img_hash = hashlib.md5(img_bytes).hexdigest()
                        if img_hash in seen_hashes:
                            continue
                        seen_hashes.add(img_hash)
                        
                        img_id = f"{prefix}_IMG_{img_counter}"
                        # Advanced context extraction using spatial word/char distance:
                        snippet = ""
                        try:
                            words = page.extract_words()
                            if words:
                                img_center = ((x0 + x1)/2, (top + bottom)/2)
                                def word_dist(w):
                                    w_center = ((w["x0"] + w["x1"])/2, (w["top"] + w["bottom"])/2)
                                    return (w_center[0] - img_center[0])**2 + (w_center[1] - img_center[1])**2
                                words.sort(key=word_dist)
                                closest_words = " ".join([w["text"] for w in words[:25]])
                                snippet = closest_words.strip()
                        except Exception:
                            pass
                        
                        if not snippet:
                            snippet = text_clean[:300].replace("\n", " ") + "..." if text_clean else "No text on page."
                        
                        if len(snippet) > 300:
                            snippet = snippet[:300] + "..."

                        if prefix == "THERM":
                            area = None
                        else:
                            area = detect_area(snippet) or detect_area(text_clean[:500])

                        vision_result = None
                        if area is None:
                            vision_result = classify_image_with_vision(img_bytes, "png", hint_context=snippet)
                            if vision_result["confidence"] in ("high", "medium") and vision_result["area"] != "Unclear":
                                area = vision_result["area"]
                                area_source = "vision"
                            else:
                                area_source = "none"
                        else:
                            area_source = "caption"

                        images.append({
                            "id": img_id,
                            "bytes": img_bytes,
                            "ext": "png",
                            "page_num": page_index + 1,
                            "context": snippet,
                            "area": area,
                            "area_source": area_source,
                            "vision_result": vision_result,
                            "area_raw": None,
                            "photo_num": None
                        })

                        if prefix == "THERM":
                            therm_meta = {}
                            m_hot = re.search(r'Hotspot\s*:\s*([\d.]+)\s*°?C', text_clean)
                            m_cold = re.search(r'Coldspot\s*:\s*([\d.]+)\s*°?C', text_clean)
                            m_file = re.search(r'Thermal image\s*:\s*(\S+)', text_clean)
                            if m_hot: therm_meta["hotspot_c"] = m_hot.group(1)
                            if m_cold: therm_meta["coldspot_c"] = m_cold.group(1)
                            if m_file: therm_meta["filename"] = m_file.group(1)
                            images[-1]["thermal_meta"] = therm_meta

                        img_counter += 1
                        if len(images) >= 10:
                            break
                    except Exception:
                        continue
                if len(images) >= 10:
                    break
        full_text = "\n".join([p for p in pages_text if p])
        return full_text if full_text.strip() else "Not Available", pages_text, images
    except Exception:
        pass
        
    return "Not Available", [], []

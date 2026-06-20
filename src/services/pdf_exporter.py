import io
import re
from datetime import datetime

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, Image as RLImage
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from src.utils.helpers import clean_text_for_pdf

def generate_pdf_report(ddr_content, confidence, confidence_breakdown,
                         conflict_found, conflict_summary_list,
                         all_images_dict):
    """Generate a professional PDF report using ReportLab, resolving image placements."""
    if not REPORTLAB_AVAILABLE:
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DDRTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "DDRSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    h2_style = ParagraphStyle(
        "DDRH2",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6,
        spaceBefore=16,
        fontName="Helvetica-Bold",
        borderPad=4,
    )
    body_style = ParagraphStyle(
        "DDRBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#333333"),
        spaceAfter=8,
        alignment=TA_JUSTIFY,
    )
    note_style = ParagraphStyle(
        "DDRNote",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#888888"),
        spaceAfter=4,
        fontName="Helvetica-Oblique",
    )
    caption_style = ParagraphStyle(
        "DDRCaption",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#555555"),
        spaceBefore=4,
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName="Helvetica-Oblique",
    )
    h3_style = ParagraphStyle(
        "DDRH3",
        parent=styles["Heading3"],
        fontSize=11,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=4,
        spaceBefore=10,
        fontName="Helvetica-Bold",
    )
    list_style = ParagraphStyle(
        "DDRList",
        parent=styles["Normal"],
        fontSize=10,
        leading=15,
        textColor=colors.HexColor("#333333"),
        spaceAfter=4,
        leftIndent=15,
        alignment=TA_JUSTIFY,
    )

    story = []

    # Title block
    story.append(Paragraph("DETAILED DEFECT REPORT (DDR)", title_style))
    story.append(Paragraph(
        f"AI-Assisted Engineering Assessment | Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}",
        subtitle_style
    ))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#1a1a2e")))
    story.append(Spacer(1, 0.3 * cm))

    # Confidence Badge Table
    conf_color = (
        colors.HexColor("#2ecc71") if confidence >= 75
        else colors.HexColor("#f39c12") if confidence >= 50
        else colors.HexColor("#e74c3c")
    )
    conf_data = [
        ["AI Confidence Score", f"{confidence}%"],
    ]
    for k, v in confidence_breakdown.items():
        conf_data.append([f"  • {k}", v])

    conf_table = Table(conf_data, colWidths=[10 * cm, 7 * cm])
    conf_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a1a2e")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 12),
        ("BACKGROUND", (1, 1), (1, -1), conf_color),
        ("TEXTCOLOR", (1, 1), (1, -1), colors.white),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#f5f5f5"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(conf_table)
    story.append(Spacer(1, 0.4 * cm))

    # Conflict Detection Summary (No emojis)
    conflict_label = "CONFLICTS DETECTED" if conflict_found else "NO CONFLICTS DETECTED"
    conflict_bg = colors.HexColor("#fff3cd") if conflict_found else colors.HexColor("#d4edda")
    conflict_txt_color = colors.HexColor("#856404") if conflict_found else colors.HexColor("#155724")
    conflict_text = "\n".join(conflict_summary_list)

    conflict_table = Table(
        [[conflict_label], [conflict_text]],
        colWidths=[17 * cm]
    )
    conflict_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), conflict_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), conflict_txt_color),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("FONTSIZE", (0, 1), (-1, 1), 9),
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#f8f9fa")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(conflict_table)
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))

    # DDR Content — parse sections and resolve image tag references
    rendered_pdf_tags = []
    sections = ddr_content.split("\n## ")
    for i, section in enumerate(sections):
        if not section.strip():
            continue
        lines = section.strip().split("\n")
        heading = lines[0].strip().lstrip("#").strip()
        heading = clean_text_for_pdf(heading)
        body = "\n".join(lines[1:]).strip()

        if heading:
            story.append(Paragraph(heading, h2_style))

        # Render body paragraphs
        for para in body.split("\n\n"):
            para = para.strip()
            if not para:
                continue

            # Split paragraph by potential image tags
            parts = re.split(r'(\[(?:INSP|THERM)_IMG_\d+\])', para)
            for part in parts:
                part_strip = part.strip()
                if re.match(r'^\[(?:INSP|THERM)_IMG_\d+\]$', part_strip):
                    img_id = part_strip[1:-1]
                    if img_id in all_images_dict:
                        img_data = all_images_dict[img_id]
                        try:
                            img_buf = io.BytesIO(img_data["bytes"])
                            rl_img = RLImage(img_buf, width=12 * cm, height=8 * cm, kind="proportional")
                            rl_img.hAlign = 'CENTER'
                            story.append(rl_img)
                            story.append(Paragraph(f"Figure: {img_id} (Page {img_data['page_num']})", caption_style))
                            rendered_pdf_tags.append(img_id)
                        except Exception:
                            story.append(Paragraph(f"[Image {img_id} could not be rendered]", caption_style))
                else:
                    if part:
                        part_safe = clean_text_for_pdf(part)
                        part_safe = (part_safe
                                     .replace("&", "&amp;")
                                     .replace("<", "&lt;")
                                     .replace(">", "&gt;")
                                     .replace("**", ""))
                        
                        for line in part_safe.split("\n"):
                            line = line.strip()
                            if not line:
                                continue
                            if line.startswith("### "):
                                story.append(Paragraph(line[4:], h3_style))
                            elif line.startswith("- ") or line.startswith("* "):
                                story.append(Paragraph("• " + line[2:], list_style))
                            else:
                                # Strip Markdown table pipes and don't render them if empty
                                line_clean = line
                                if line.startswith("|") and line.endswith("|") or line == "|":
                                    line_clean = line.replace("|", " ").strip()
                                    if not line_clean or line_clean.replace("-", "").strip() == "":
                                        continue
                                story.append(Paragraph(line_clean, body_style))

        story.append(Spacer(1, 0.2 * cm))

    # Reference Images (those not placed inline by the LLM)
    remaining_pdf_tags = set(all_images_dict.keys()) - set(rendered_pdf_tags)
    if remaining_pdf_tags:
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
        story.append(Paragraph("Additional Extracted Reference Images", h2_style))

        for img_id in sorted(list(remaining_pdf_tags)):
            img_data = all_images_dict[img_id]
            try:
                img_buf = io.BytesIO(img_data["bytes"])
                rl_img = RLImage(img_buf, width=12 * cm, height=8 * cm, kind="proportional")
                rl_img.hAlign = 'CENTER'
                story.append(rl_img)
                story.append(Paragraph(f"Figure: {img_id} (Source Page {img_data['page_num']})", caption_style))
            except Exception:
                pass

    # Footer note
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cccccc")))
    story.append(Paragraph(
        "This report is AI-assisted and should be reviewed by a qualified civil engineer before use in any official capacity.",
        note_style
    ))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()

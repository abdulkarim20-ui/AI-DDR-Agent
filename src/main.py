import streamlit as st
import io
import re
from datetime import datetime
import sys
import os

# Add parent directory to sys.path so 'src' can be imported when running inside the directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ui.components import inject_custom_css, get_svg_icon, st_markdown_icon, render_section_heading
from src.services.pdf_extractor import extract_pdf_data
from src.services.llm_engine import detect_conflicts, calculate_confidence, generate_ddr
from src.services.pdf_exporter import generate_pdf_report, REPORTLAB_AVAILABLE

# ─────────────────────────────────────────────
# PAGE CONFIG & CSS
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI DDR Generator | Urbanroof",
    layout="wide"
)

inject_custom_css()

# ─────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────
if "report_generated" not in st.session_state:
    st.session_state.report_generated = False
    st.session_state.ddr_content = None
    st.session_state.confidence = 0
    st.session_state.conf_breakdown = {}
    st.session_state.conflict_found = False
    st.session_state.conflict_summary_list = []
    st.session_state.conflict_summary_text = ""
    st.session_state.all_images_dict = {}
    st.session_state.all_images_list = []
    st.session_state.pdf_bytes = None

# ─────────────────────────────────────────────
# HEADER & UPLOADS
# ─────────────────────────────────────────────
st.markdown(f"""
<div class="main-header" style="display: flex; align-items: center; gap: 16px;">
    {get_svg_icon("building", size=42, color="#ffffff")}
    <div>
        <h1 style="color: white; margin: 0; font-size: 2.1rem;">AI Detailed Defect Report Generator</h1>
        <p style="margin: 0.2rem 0 0; opacity: 0.8; font-size: 0.95rem;">Upload building inspection and thermal imaging reports to compile a structured engineering DDR</p>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    st_markdown_icon("file-text", "Inspection Report", color="#1a1a2e", font_size="1.15rem")
    inspection_file = st.file_uploader(
        "Upload Inspection PDF", type=["pdf"], label_visibility="collapsed", key="insp_upload"
    )
    if inspection_file:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 6px; color: #155724; font-size: 0.88rem;">
            {get_svg_icon("check-circle", size=16, color="#10b981")}
            <span>{inspection_file.name} uploaded successfully</span>
        </div>
        """, unsafe_allow_html=True)

with col2:
    st_markdown_icon("thermometer", "Thermal Report (Optional)", color="#1a1a2e", font_size="1.15rem")
    thermal_file = st.file_uploader(
        "Upload Thermal PDF", type=["pdf"], label_visibility="collapsed", key="therm_upload"
    )
    if thermal_file:
        st.markdown(f"""
        <div style="display: flex; align-items: center; gap: 6px; color: #155724; font-size: 0.88rem;">
            {get_svg_icon("check-circle", size=16, color="#10b981")}
            <span>{thermal_file.name} uploaded successfully</span>
        </div>
        """, unsafe_allow_html=True)

st.markdown("")
generate_btn = st.button("Generate DDR Report", use_container_width=True)

# ─────────────────────────────────────────────
# GENERATION LOGIC
# ─────────────────────────────────────────────
if generate_btn:
    if not inspection_file:
        st.error("Please upload an Inspection PDF to proceed.")
    else:
        # Reset state for new run
        st.session_state.report_generated = False
        
        progress = st.progress(0, text="Initializing report compiler...")

        # Step 1 — Parse reports
        progress.progress(15, text="Reading inspection report text and images...")
        inspection_file.seek(0)
        inspection_text, insp_pages, insp_images = extract_pdf_data(inspection_file, prefix="INSP")

        thermal_text = "Not Available"
        therm_pages = []
        therm_images = []
        if thermal_file:
            progress.progress(30, text="Reading thermal report text and images...")
            thermal_file.seek(0)
            thermal_text, therm_pages, therm_images = extract_pdf_data(thermal_file, prefix="THERM")

        all_images_list = insp_images + therm_images
        all_images_dict = {img["id"]: img for img in all_images_list}

        # Step 2 — Conflict detection
        progress.progress(45, text="Detecting report contradictions...")
        conflict_found, conflict_summary_list = detect_conflicts(inspection_text, thermal_text)
        conflict_summary_text = "\n".join(conflict_summary_list)

        # Step 3 — Confidence score
        progress.progress(60, text="Calculating data reliability index...")
        confidence, conf_breakdown = calculate_confidence(
            inspection_text, thermal_text, insp_images, therm_images
        )

        # Step 4 — Generate DDR
        progress.progress(75, text="Compiling Detailed Defect Report (this takes 15-30s)...")
        try:
            ddr_content = generate_ddr(inspection_text, thermal_text, conflict_summary_text, confidence, all_images_list)
            progress.progress(82, text="Running AI visual classification on unmatched images...")
            from src.services.image_placement import enforce_image_placement
            ddr_content = enforce_image_placement(ddr_content, all_images_list)
        except Exception as e:
            st.error(f"LLM compilation failed: {str(e)}")
            st.stop()

        # Step 5 — Generate PDF report
        progress.progress(90, text="Exporting professional PDF document...")
        pdf_bytes = None
        if REPORTLAB_AVAILABLE:
            try:
                pdf_bytes = generate_pdf_report(
                    ddr_content, confidence, conf_breakdown,
                    conflict_found, conflict_summary_list,
                    all_images_dict
                )
            except Exception as e:
                st.warning(f"PDF creation bypassed: {e}. Text download still available.")

        progress.progress(100, text="Report compiled.")
        progress.empty()

        # Cache in session state
        st.session_state.ddr_content = ddr_content
        st.session_state.confidence = confidence
        st.session_state.conf_breakdown = conf_breakdown
        st.session_state.conflict_found = conflict_found
        st.session_state.conflict_summary_list = conflict_summary_list
        st.session_state.conflict_summary_text = conflict_summary_text
        st.session_state.all_images_list = all_images_list
        st.session_state.all_images_dict = all_images_dict
        st.session_state.pdf_bytes = pdf_bytes
        st.session_state.report_generated = True

# ─────────────────────────────────────────────
# DISPLAY CACHED REPORT
# ─────────────────────────────────────────────
if st.session_state.report_generated:
    st.markdown("""
    <div style="display: flex; align-items: center; gap: 8px; color: #155724; background-color: #d4edda; padding: 0.8rem 1.2rem; border-radius: 8px; margin-bottom: 1.2rem;">
        {get_svg_icon("check-circle", size=20, color="#10b981")}
        <span style="font-weight: 600;">DDR Report Generated Successfully!</span>
    </div>
    """.replace('{get_svg_icon("check-circle", size=20, color="#10b981")}', get_svg_icon("check-circle", size=20, color="#10b981")), unsafe_allow_html=True)
    st.markdown("---")

    # ── Metrics Display ──
    m1, m2, m3, m4 = st.columns(4)
    confidence = st.session_state.confidence
    conflict_found = st.session_state.conflict_found
    all_images_list = st.session_state.all_images_list
    ddr_content = st.session_state.ddr_content

    conf_color_hex = "#2ecc71" if confidence >= 75 else "#f39c12" if confidence >= 50 else "#e74c3c"
    with m1:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value" style="color:{conf_color_hex}">{confidence}%</div>
          <div class="metric-label">AI Confidence</div>
        </div>""", unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{len(all_images_list)}</div>
          <div class="metric-label">Images Extracted</div>
        </div>""", unsafe_allow_html=True)
    with m3:
        conflict_val = "Alert" if conflict_found else "No Issues"
        conflict_col = "#e74c3c" if conflict_found else "#2ecc71"
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value" style="color:{conflict_col}">{conflict_val}</div>
          <div class="metric-label">Conflict Check</div>
        </div>""", unsafe_allow_html=True)
    with m4:
        sections_count = ddr_content.count("## ")
        st.markdown(f"""
        <div class="metric-card">
          <div class="metric-value">{sections_count}</div>
          <div class="metric-label">Report Sections</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("")

    # ── Confidence Breakdown ──
    with st.expander("Confidence Score Breakdown", expanded=True):
        st.markdown(f"**Total Score: {confidence}/100**")
        st.markdown(f"""
        <div class="confidence-bar-wrap">
          <div class="confidence-bar-fill" style="width:{confidence}%;background:{conf_color_hex}"></div>
        </div>""", unsafe_allow_html=True)
        for k, v in st.session_state.conf_breakdown.items():
            st.markdown(f"- **{k}**: {v}")

    # ── Conflict Detection ──
    with st.expander("Conflict Detection Details", expanded=conflict_found):
        box_class = "conflict-found" if conflict_found else "conflict-ok"
        conflict_html_lines = "<br>".join(st.session_state.conflict_summary_list)
        st.markdown(f"""
        <div class="conflict-box {box_class}">
        {conflict_html_lines}
        </div>""", unsafe_allow_html=True)

    # ── DDR Report content with inline images ──
    render_section_heading("file-text", "Detailed Defect Report")
    
    rendered_tags = []
    if ddr_content:
        parts = re.split(r'(\[(?:INSP|THERM)_IMG_\d+\])', ddr_content)
        for part in parts:
            part_strip = part.strip()
            if re.match(r'^\[(?:INSP|THERM)_IMG_\d+\]$', part_strip):
                img_id = part_strip[1:-1]
                if img_id in st.session_state.all_images_dict:
                    img_data = st.session_state.all_images_dict[img_id]
                    img_col1, img_col2, img_col3 = st.columns([1, 1, 1])
                    with img_col1:
                        st.image(img_data["bytes"], caption=f"Figure: {img_id} (Page {img_data['page_num']})", use_container_width=True)
                    rendered_tags.append(img_id)
                else:
                    st.markdown(f'<div class="image-not-available">Image reference {part_strip} not found</div>', unsafe_allow_html=True)
            else:
                if part:
                    st.markdown(part)

    # ── Reference Images ──
    st.markdown("---")
    remaining_tags = set(st.session_state.all_images_dict.keys()) - set(rendered_tags)
    
    render_section_heading("image", "Additional Extracted Reference Images")
    
    if remaining_tags:
        remaining_list = sorted(list(remaining_tags))
        img_cols = st.columns(min(len(remaining_list), 3))
        for i, img_id in enumerate(remaining_list):
            img_data = st.session_state.all_images_dict[img_id]
            with img_cols[i % 3]:
                try:
                    st.image(img_data["bytes"], caption=f"Figure: {img_id} (Page {img_data['page_num']})", use_container_width=True)
                except Exception:
                    st.markdown(f'<div class="image-not-available">Image {img_id} could not be rendered</div>', unsafe_allow_html=True)
    else:
        if not all_images_list:
            st.markdown("""
            <div class="image-not-available">
              No images were extracted from the uploaded PDF documents.
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="color: #666; font-size: 0.9rem; font-style: italic; padding: 1rem 0;">
              All extracted images were placed inline under their relevant sections in the report.
            </div>""", unsafe_allow_html=True)

    # ── Download buttons ──
    st.markdown("---")
    dl_col1, dl_col2 = st.columns(2)

    with dl_col1:
        if st.session_state.pdf_bytes and REPORTLAB_AVAILABLE:
            st.download_button(
                label="Download PDF Report",
                data=st.session_state.pdf_bytes,
                file_name=f"DDR_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        else:
            st.info("PDF export not available (install reportlab)")

    with dl_col2:
        txt_content = f"""DETAILED DEFECT REPORT (DDR)
Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}
AI Confidence Score: {confidence}%

Confidence Breakdown:
{chr(10).join(f'  • {k}: {v}' for k, v in st.session_state.conf_breakdown.items())}

Conflict Detection:
{st.session_state.conflict_summary_text}

{'='*60}

{ddr_content}

{'='*60}
This report is AI-assisted. Review by a qualified civil engineer is recommended.
"""
        st.download_button(
            label="Download Text Report",
            data=txt_content,
            file_name=f"DDR_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
            use_container_width=True
        )

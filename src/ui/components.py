import streamlit as st

def get_svg_icon(name, size=24, color="currentColor"):
    """Return inline SVG for Lucide icons."""
    icons = {
        "building": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-building" style="display:inline-block;vertical-align:middle;"><rect width="16" height="20" x="4" y="2" rx="2" ry="2"/><path d="M9 22v-4h6v4"/><path d="M8 6h.01"/><path d="M16 6h.01"/><path d="M8 10h.01"/><path d="M16 10h.01"/><path d="M12 14h.01"/><path d="M12 10h.01"/><path d="M12 6h.01"/></svg>',
        "file-text": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-file-text" style="display:inline-block;vertical-align:middle;"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>',
        "thermometer": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-thermometer" style="display:inline-block;vertical-align:middle;"><path d="M14 4v10.54a4 4 0 1 1-4 0V4a2 2 0 0 1 4 0Z"/></svg>',
        "alert-triangle": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-alert-triangle" style="display:inline-block;vertical-align:middle;"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>',
        "check-circle": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-check-circle" style="display:inline-block;vertical-align:middle;"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>',
        "download": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-download" style="display:inline-block;vertical-align:middle;"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>',
        "info": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-info" style="display:inline-block;vertical-align:middle;"><circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/></svg>',
        "activity": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-activity" style="display:inline-block;vertical-align:middle;"><path d="M22 12h-4l-3 9L9 3l-3 9H2"/></svg>',
        "image": f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-image" style="display:inline-block;vertical-align:middle;"><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></svg>'
    }
    return icons.get(name, "")

def st_markdown_icon(icon_name, text, color="#1a1a2e", size=20, font_weight="600", font_size="1.1rem"):
    """Helper to display inline Lucide icons alongside text in Streamlit."""
    svg = get_svg_icon(icon_name, size=size, color=color)
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 8px; margin: 0.5rem 0;">
        {svg}
        <span style="font-size: {font_size}; font-weight: {font_weight}; color: {color};">{text}</span>
    </div>
    """, unsafe_allow_html=True)

def render_section_heading(icon_name, text):
    """Helper to display a section heading with an inline Lucide icon."""
    svg = get_svg_icon(icon_name, size=22, color="#1a1a2e")
    st.markdown(f"""
    <div class="section-heading" style="display: flex; align-items: center; gap: 10px;">
        {svg}
        <span>{text}</span>
    </div>
    """, unsafe_allow_html=True)

def inject_custom_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

        .main-header {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            padding: 2rem 2.5rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            color: white;
            box-shadow: 0 8px 32px rgba(26,26,46,0.3);
        }
        .main-header h1 { margin: 0; font-size: 2rem; font-weight: 700; }
        .main-header p  { margin: 0.4rem 0 0; opacity: 0.75; font-size: 0.95rem; }

        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 1rem 1.2rem;
            text-align: center;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            border: 1px solid #e8ecf4;
        }
        .metric-value { font-size: 2rem; font-weight: 700; color: #1a1a2e; }
        .metric-label { font-size: 0.78rem; color: #888; text-transform: uppercase; letter-spacing: 0.05em; }

        .conflict-box {
            padding: 1rem 1.2rem;
            border-radius: 10px;
            margin: 0.8rem 0;
            border-left: 4px solid;
        }
        .conflict-found   { background: #fff8e1; border-color: #f59e0b; color: #92400e; }
        .conflict-ok      { background: #ecfdf5; border-color: #10b981; color: #065f46; }

        .section-heading {
            font-size: 1.25rem;
            font-weight: 600;
            color: #1a1a2e;
            border-bottom: 2px solid #e0e4f0;
            padding-bottom: 0.4rem;
            margin-top: 1.8rem;
            margin-bottom: 1rem;
        }

        .confidence-bar-wrap {
            background: #e8ecf4;
            border-radius: 999px;
            height: 12px;
            width: 100%;
            margin: 0.4rem 0 0.8rem;
            overflow: hidden;
        }
        .confidence-bar-fill {
            height: 12px;
            border-radius: 999px;
            transition: width 1s ease;
        }

        .image-not-available {
            background: #f3f4f6;
            border: 2px dashed #d1d5db;
            border-radius: 10px;
            text-align: center;
            padding: 1.5rem;
            color: #9ca3af;
            font-size: 0.9rem;
        }

        div.stButton > button {
            background: linear-gradient(135deg, #1a1a2e, #0f3460);
            color: white;
            border: none;
            border-radius: 10px;
            padding: 0.65rem 2rem;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
        }
        div.stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(15,52,96,0.4);
        }
    </style>
    """, unsafe_allow_html=True)

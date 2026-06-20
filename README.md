<div align="center">
  <h1>🏗️ AI DDR Generator</h1>
  <h3>Professional Detailed Defect Reports Powered by AI</h3>
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B.svg?style=flat&logo=Streamlit&logoColor=white)](https://streamlit.io)
</div>

An AI-powered system that automatically generates professional **Detailed Defect Reports (DDR)** from building inspection and thermal PDF documents using Large Language Models.

---

## 🎥 Demo Video
Watch the detailed walkthrough here:
👉 [Loom Walkthrough](https://www.loom.com/share/3d508f29d67d4492b2283eae4504cf29)

> GitHub README does not reliably play embedded MP4 video files.
> Use the direct video link below if the player does not load.

[Open demo video](assets/DEMO.mp4)

---

## 📐 System Architecture Pipeline

```
Inspection PDF + Thermal PDF
         ↓
PDF Text Extractor      (pdfplumber)
PDF Image Extractor     (PyMuPDF / pdfplumber fallback)
         ↓
Missing Data Validator  → "Not Available" for every empty field
         ↓
Conflict Detector       → compares severity & area mentions across reports
         ↓
DDR Generator (Groq LLM) → 7 required DDR sections
         ↓
Confidence Scorer       → document completeness + field coverage + images
         ↓
PDF Report Export       (ReportLab) + Streamlit Display
```

---

## 📌 Features

- 📄 **Text Extraction** — Full PDF text extraction using pdfplumber
- 🖼️ **Image Extraction** — Embedded images extracted via PyMuPDF (fallback to pdfplumber)
- 🔍 **Conflict Detection** — Compares severity and location data between inspection and thermal reports
- 📊 **Real Confidence Scoring** — Based on document completeness, field coverage, and image availability
- 📋 **Correct DDR Structure** — Generates exactly 7 required sections per assignment specification
- 📑 **Professional PDF Export** — Styled PDF with images, confidence badge, and conflict status
- 🌐 **Interactive Streamlit UI** — Clean, dark-themed web interface

---

## 📋 Required DDR Sections (Assignment Compliant)

The generated report follows the exact required structure:

1. **Property Issue Summary**
2. **Area-wise Observations**
3. **Probable Root Cause**
4. **Severity Assessment** (with explicit reasoning)
5. **Recommended Actions**
6. **Additional Notes**
7. **Missing or Unclear Information**

---

## 📊 Confidence Score Formula

The AI Confidence Score is calculated transparently:

| Component | Weight | How Measured |
|-----------|--------|--------------|
| Document Completeness | 40 pts | Presence + length of inspection & thermal text |
| Field Coverage | 35 pts | Count of 15 key engineering terms found |
| Image Availability | 25 pts | Number of images extracted from PDFs |

---

## 🔍 Conflict Detection Logic

The system compares inspection and thermal reports for:

- **Severity conflicts** — If one says "CRITICAL" and the other says "MINOR"
- **Area/location conflicts** — If thermal report mentions areas not covered in inspection

Conflicts are flagged in both the UI and the exported PDF report.

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python | Core language |
| Streamlit | Web UI |
| Groq API | LLM inference (DDR generation) |
| pdfplumber | PDF text extraction |
| PyMuPDF (fitz) | PDF image extraction |
| ReportLab | Professional PDF export |
| python-dotenv | Environment variable management |

---

## ⚙️ How It Works

1. Upload inspection PDF (required)
2. Upload thermal PDF (optional)
3. System extracts text AND images from both PDFs
4. Missing data is automatically flagged as "Not Available"
5. Conflict detector compares both reports
6. AI generates a 7-section DDR report
7. Confidence score is calculated from data completeness
8. Download as professional PDF or plain text

---

## 🧪 How to Use

1. Clone and run the project locally.
2. Upload inspection PDF
3. Upload thermal PDF (optional)
4. Click **Generate DDR Report**
5. Review conflict detection and confidence score
6. Download the PDF report

---

## 📄 Sample Input Files

Test files are included in `data/samples/`:

- Inspection → `data/samples/inspection_data.pdf`
- Thermal → `data/samples/thermal_data.pdf`

---

## ▶️ Run Locally

```bash
git clone <repo-url>
cd DDR
pip install -r requirements.txt
```

Create `.env` file:
```
GROQ_API_KEY=your_groq_api_key_here
```

Run:
```bash
streamlit run src/main.py
```

---

## 📁 Project Structure

```
DDR/
├── src/                      # Modular application source code
│   ├── main.py               # Application entry point
│   ├── ui/                   # UI components (icons, CSS)
│   ├── services/             # Core logic (LLM, PDF extraction/export)
│   └── utils/                # Helper utilities
├── data/samples/             # Sample PDF documents
├── assets/                   # Media and demo videos
├── requirements.txt          # Dependencies
├── .env                      # API key (not committed)
└── README.md
```

---

## 🤝 Community & Support

*   **Contributions**: Check out [CONTRIBUTING.md](.github/CONTRIBUTING.md) to join the project.
*   **Security**: See [SECURITY.md](.github/SECURITY.md) for vulnerability reporting.
*   **Author**: Developed by **Abdulkarim Shaikh**.

---

## ⚠️ Disclaimer

This report is AI-assisted and should be reviewed by a qualified civil engineer before use in any official or legal capacity.

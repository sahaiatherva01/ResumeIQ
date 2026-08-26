import os
import time
import json
from flask import Flask, request, jsonify, render_template, send_file
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from resume_parser import parse_resume
from extractor import extract_candidate_profile, match_job_description, improve_bullet_point
from ats_analyzer import run_ats_analysis

app = Flask(__name__)

# Configure upload constraints
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max limit

def allowed_file(filename: str) -> bool:
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    """Serves the main single-page application dashboard."""
    return render_template('index.html')

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "timestamp": time.time(),
        "api_configured": bool(os.environ.get("GEMINI_API_KEY"))
    }), 200

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """
    Accepts PDF/DOCX file, validates it, and extracts the raw text and metadata.
    """
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded in the request."}), 400
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file was selected."}), 400
        
    if not allowed_file(file.filename):
        return jsonify({"error": "Unsupported file format. Please upload a PDF or DOCX file."}), 400
        
    try:
        file_bytes = file.read()
        metadata = parse_resume(file_bytes, file.filename)
        return jsonify(metadata), 200
    except Exception as e:
        return jsonify({"error": f"Failed to parse document: {str(e)}"}), 500

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """
    Runs the full analysis pipeline. Can accept either:
    1. A multipart file upload ('file' key)
    2. A JSON payload with 'raw_text' and 'parser_metadata'
    Optionally accepts a 'job_description' text field.
    """
    raw_text = None
    parser_metadata = {}
    job_description = None
    
    # 1. Handle File Upload
    if 'file' in request.files:
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected."}), 400
        if not allowed_file(file.filename):
            return jsonify({"error": "Unsupported file format. Please upload PDF or DOCX."}), 400
            
        try:
            file_bytes = file.read()
            parser_metadata = parse_resume(file_bytes, file.filename)
            raw_text = parser_metadata.pop("raw_text")
            # Get job description from form data if present
            job_description = request.form.get("job_description")
        except Exception as e:
            return jsonify({"error": f"Failed to parse document: {str(e)}"}), 500
            
    # 2. Handle JSON Payload
    elif request.is_json:
        data = request.get_json()
        raw_text = data.get("raw_text")
        parser_metadata = data.get("parser_metadata", {})
        job_description = data.get("job_description")
        
    # Check if we have valid text to analyze
    if not raw_text or raw_text.strip() == "":
        return jsonify({
            "status": "extraction_failed",
            "message": "Unable to reliably extract the uploaded resume. Please upload a text-readable PDF/DOCX."
        }), 422
        
    try:
        # Step A: Run LLM structured extraction
        extracted_profile = extract_candidate_profile(raw_text)
        
        # Step B: Run optional JD matching
        job_match = None
        if job_description and job_description.strip() != "":
            job_match = match_job_description(raw_text, job_description)
            
        # Step C: Run programmatic ATS+ grading and checklist calculations
        candidate_profile = run_ats_analysis(extracted_profile, parser_metadata, raw_text, job_match)
        
        version_id = str(int(time.time()))
        candidate_profile.version_id = version_id
        
        # Step C: Save analysis JSON locally
        os.makedirs("data", exist_ok=True)
        debug_filename = f"data/analysis_{version_id}.json"
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(candidate_profile.model_dump_json(indent=2))
            
        # Append version to data/history.json
        history_file = "data/history.json"
        history_entry = {
            "version_id": version_id,
            "date": time.strftime("%b %d, %H:%M"),
            "file_name": file.filename if 'file' in request.files else "Raw Text Input",
            "overall_score": candidate_profile.ats_scores.overall_score,
            "category_scores": candidate_profile.ats_scores.model_dump()
        }
        
        history_data = []
        if os.path.exists(history_file):
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history_data = json.load(f)
            except Exception:
                history_data = []
                
        history_data.insert(0, history_entry)
        with open(history_file, "w", encoding="utf-8") as f:
            json.dump(history_data, f, indent=2)
            
        return candidate_profile.model_dump_json(), 200, {'Content-Type': 'application/json'}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "extraction_failed",
            "message": "Unable to reliably extract the uploaded resume. Please upload a text-readable PDF/DOCX."
        }), 422

@app.route('/api/improve_bullet', methods=['POST'])
def improve_bullet():
    """Improves a single bullet point dynamically without hallucinating facts."""
    if not request.is_json:
        return jsonify({"error": "Payload must be JSON."}), 400
    data = request.get_json()
    bullet_text = data.get("bullet_text")
    role_context = data.get("role_context")
    if not bullet_text or bullet_text.strip() == "":
        return jsonify({"error": "bullet_text is required."}), 400
        
    improved = improve_bullet_point(bullet_text, role_context)
    return jsonify({
        "original": bullet_text,
        "improved": improved
    }), 200

@app.route('/api/history', methods=['GET'])
def get_history():
    """Returns the list of previously analyzed resume versions."""
    history_file = "data/history.json"
    if not os.path.exists(history_file):
        return jsonify([]), 200
    try:
        with open(history_file, "r", encoding="utf-8") as f:
            history_data = json.load(f)
        return jsonify(history_data), 200
    except Exception as e:
        return jsonify({"error": f"Failed to load history: {str(e)}"}), 500

@app.route('/api/compare', methods=['GET'])
def compare_versions():
    """Compares the scores and category details between two analysis versions."""
    v1 = request.args.get("v1")
    v2 = request.args.get("v2")
    if not v1 or not v2:
        return jsonify({"error": "Missing v1 or v2 version parameters."}), 400
        
    f1 = f"data/analysis_{v1}.json"
    f2 = f"data/analysis_{v2}.json"
    
    if not os.path.exists(f1) or not os.path.exists(f2):
        return jsonify({"error": "One or both version files could not be found."}), 404
        
    try:
        with open(f1, "r", encoding="utf-8") as file1:
            data1 = json.load(file1)
        with open(f2, "r", encoding="utf-8") as file2:
            data2 = json.load(file2)
            
        s1 = data1["ats_scores"]
        s2 = data2["ats_scores"]
        
        comparisons = {
            "v1": v1,
            "v2": v2,
            "overall": {"v1": s1["overall_score"], "v2": s2["overall_score"], "diff": round(s2["overall_score"] - s1["overall_score"], 1)},
            "categories": {
                "ats_compatibility": {"v1": s1["ats_compatibility"], "v2": s2["ats_compatibility"], "diff": round(s2["ats_compatibility"] - s1["ats_compatibility"], 1)},
                "resume_structure": {"v1": s1["resume_structure"], "v2": s2["resume_structure"], "diff": round(s2["resume_structure"] - s1["resume_structure"], 1)},
                "keyword_relevance": {"v1": s1["keyword_relevance"], "v2": s2["keyword_relevance"], "diff": round(s2["keyword_relevance"] - s1["keyword_relevance"], 1)},
                "content_quality": {"v1": s1["content_quality"], "v2": s2["content_quality"], "diff": round(s2["content_quality"] - s1["content_quality"], 1)},
                "skills_representation": {"v1": s1["skills_representation"], "v2": s2["skills_representation"], "diff": round(s2["skills_representation"] - s1["skills_representation"], 1)},
                "quantified_impact": {"v1": s1["quantified_impact"], "v2": s2["quantified_impact"], "diff": round(s2["quantified_impact"] - s1["quantified_impact"], 1)},
                "completeness": {"v1": s1["completeness"], "v2": s2["completeness"], "diff": round(s2["completeness"] - s1["completeness"], 1)},
                "readability_consistency": {"v1": s1["readability_consistency"], "v2": s2["readability_consistency"], "diff": round(s2["readability_consistency"] - s1["readability_consistency"], 1)}
            },
            "improved": [],
            "stayed_same": [],
            "worsened": []
        }
        
        for cat_key, cat_data in comparisons["categories"].items():
            diff = cat_data["diff"]
            name = cat_key.replace("_", " ").title()
            if diff > 0:
                comparisons["improved"].append(f"{name} improved by +{diff} points")
            elif diff == 0:
                comparisons["stayed_same"].append(f"{name} remained identical")
            else:
                comparisons["worsened"].append(f"{name} decreased by {diff} points")
                
        return jsonify(comparisons), 200
    except Exception as e:
        return jsonify({"error": f"Failed to calculate comparison: {str(e)}"}), 500

def generate_pdf_report(data):
    from io import BytesIO
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=54, leftMargin=54, topMargin=54, bottomMargin=54)
    story = []
    
    styles = getSampleStyleSheet()
    
    color_primary = colors.HexColor("#0f172a")
    color_secondary = colors.HexColor("#3b82f6")
    color_text = colors.HexColor("#334155")
    color_border = colors.HexColor("#e2e8f0")
    color_bg_header = colors.HexColor("#f8fafc")
    
    style_title = ParagraphStyle(
        'DocTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=24, textColor=color_primary, spaceAfter=15
    )
    style_subtitle = ParagraphStyle(
        'DocSubTitle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=14, textColor=color_secondary, spaceAfter=8
    )
    style_h2 = ParagraphStyle(
        'SectionHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, textColor=color_primary, spaceBefore=15, spaceAfter=10
    )
    style_body = ParagraphStyle(
        'BodyTextCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=color_text, leading=14, spaceAfter=6
    )
    style_bullet = ParagraphStyle(
        'BulletCustom', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=color_text, leading=14, leftIndent=15, firstLineIndent=-10, spaceAfter=4
    )
    
    name = data.get("personal_info", {}).get("name") or "Candidate Name"
    story.append(Paragraph(f"ResumeLens AI — Optimization Report", style_subtitle))
    story.append(Paragraph(name, style_title))
    
    pi = data.get("personal_info", {})
    contacts = []
    if pi.get("email"): contacts.append(pi["email"])
    if pi.get("phone"): contacts.append(pi["phone"])
    if pi.get("location"): contacts.append(pi["location"])
    story.append(Paragraph(" | ".join(contacts), style_body))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("ATS Plus Grading Dashboard", style_h2))
    overall = data.get("ats_scores", {}).get("overall_score")
    story.append(Paragraph(f"<b>Overall ATS Readiness Score: {overall} / 100</b>", style_subtitle))
    story.append(Spacer(1, 8))
    
    scores = data.get("ats_scores", {})
    scores_data = [
        [Paragraph("<b>Category</b>", style_body), Paragraph("<b>Score</b>", style_body), Paragraph("<b>Max</b>", style_body)],
        [Paragraph("ATS Compatibility", style_body), Paragraph(str(scores.get("ats_compatibility")), style_body), "15"],
        [Paragraph("Resume Structure", style_body), Paragraph(str(scores.get("resume_structure")), style_body), "15"],
        [Paragraph("Keyword / Job Relevance", style_body), Paragraph(str(scores.get("keyword_relevance")), style_body), "20"],
        [Paragraph("Content Quality", style_body), Paragraph(str(scores.get("content_quality")), style_body), "15"],
        [Paragraph("Skills Representation", style_body), Paragraph(str(scores.get("skills_representation")), style_body), "10"],
        [Paragraph("Quantified Impact", style_body), Paragraph(str(scores.get("quantified_impact")), style_body), "10"],
        [Paragraph("Completeness", style_body), Paragraph(str(scores.get("completeness")), style_body), "10"],
        [Paragraph("Readability & Consistency", style_body), Paragraph(str(scores.get("readability_consistency")), style_body), "5"]
    ]
    
    t = Table(scores_data, colWidths=[250, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), color_bg_header),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.5, color_border),
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Top Prioritized Action Items", style_h2))
    for imp in data.get("top_improvements", []):
        story.append(Paragraph(f"<b>{imp.get('priority')}. {imp.get('title')}</b> (Potential Score Impact: +{imp.get('impact_score')} points)<br/>{imp.get('description')}", style_bullet))
    story.append(Spacer(1, 15))
    
    story.append(PageBreak())
    
    story.append(Paragraph("Strengths & Weaknesses Analysis", style_h2))
    story.append(Paragraph("<b>Strengths</b>", style_subtitle))
    for str_t in data.get("strengths", []):
        story.append(Paragraph(f"• {str_t}", style_bullet))
    story.append(Spacer(1, 8))
    
    story.append(Paragraph("<b>Resume Weaknesses Detected</b>", style_subtitle))
    for wk in data.get("detailed_weaknesses", [])[:8]:
        story.append(Paragraph(f"• <b>[{wk.get('severity').upper()}]</b> {wk.get('message')}<br/><i>Context: \"{wk.get('context')}\"</i>", style_bullet))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Target Role Fit & Gap Analysis", style_h2))
    for fit in data.get("target_role_fit", []):
        story.append(Paragraph(f"<b>{fit.get('role_name')} Fit Score: {fit.get('fit_score')}%</b>", style_subtitle))
        story.append(Paragraph(f"<b>Key Gaps:</b> {', '.join(fit.get('potential_gaps', [])[:5]) if fit.get('potential_gaps') else 'None'}", style_body))
        story.append(Spacer(1, 4))
        
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

@app.route('/api/report/pdf', methods=['GET'])
def get_pdf_report():
    """Generates and downloads the professional PDF analysis report."""
    v = request.args.get("version")
    if not v:
        # Get the latest saved analysis JSON from history.json
        history_file = "data/history.json"
        if not os.path.exists(history_file):
            return jsonify({"error": "No analyses have been run yet."}), 404
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            if not history:
                return jsonify({"error": "No analyses have been run yet."}), 404
            v = history[0]["version_id"]
        except Exception as e:
            return jsonify({"error": f"Failed to retrieve latest version: {str(e)}"}), 500
            
    fpath = f"data/analysis_{v}.json"
    if not os.path.exists(fpath):
        return jsonify({"error": f"Analysis file for version {v} could not be found."}), 404
        
    try:
        with open(fpath, "r", encoding="utf-8") as file:
            data = json.load(file)
            
        pdf_bytes = generate_pdf_report(data)
        
        from io import BytesIO
        return send_file(
            BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"ResumeLens_Analysis_{v}.pdf"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Failed to generate PDF: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001 , debug=True)

"""RecruitAI v2 — Flask Backend for Resume Screening"""

import os
import io
import json
import PyPDF2
import docx
import requests
from dotenv import load_dotenv

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

print("=" * 60)
print("🚀 RecruitAI v2 Backend Starting...")
print("=" * 60)

# Get the directory where this app.py is located
APP_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(APP_DIR, "frontend")

# Configure Flask with static folder for frontend files
app = Flask(
    __name__, 
    static_folder=FRONTEND_DIR,
    static_url_path=""
)
CORS(app)

# Health check endpoint (keeps Railway from stopping the app)
@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint for deployment monitoring"""
    return jsonify({
        "status": "ok",
        "app": "RecruitAI Resume Screening Backend",
        "version": "2.0",
        "tfidf_ready": True,
        "supabase_configured": bool(SUPABASE_URL and SUPABASE_KEY)
    }), 200

@app.route("/")
def serve_index():
    """Serve frontend index.html"""
    try:
        return send_from_directory(FRONTEND_DIR, "index.html")
    except Exception as e:
        print(f"[ERROR] Failed to serve index.html: {e}")
        print(f"[DEBUG] FRONTEND_DIR = {FRONTEND_DIR}")
        print(f"[DEBUG] Frontend exists: {os.path.exists(FRONTEND_DIR)}")
        if os.path.exists(FRONTEND_DIR):
            print(f"[DEBUG] Files: {os.listdir(FRONTEND_DIR)}")
        return jsonify({"error": "Frontend not found"}), 500

@app.route("/<path:path>")
def serve_static(path):
    """Serve frontend static assets"""
    file_path = os.path.join(FRONTEND_DIR, path)
    
    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(FRONTEND_DIR)):
        return jsonify({"error": "Forbidden"}), 403
    
    if os.path.isfile(file_path):
        return send_from_directory(FRONTEND_DIR, path)
    
    # SPA fallback
    if not path.startswith("screen") and not path.startswith("export"):
        try:
            return send_from_directory(FRONTEND_DIR, "index.html")
        except Exception as e:
            return jsonify({"error": f"Not found: {path}"}), 404
    
    return jsonify({"error": f"Not found: {path}"}), 404

print("⏳ Initializing TF-IDF vectorizer...")
VECTORIZER = TfidfVectorizer(max_features=500, stop_words='english')
print("✅ TF-IDF vectorizer ready.")

BERT_WEIGHT   = 0.40
GEMINI_WEIGHT = 0.60

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

if SUPABASE_URL and SUPABASE_KEY:
    print("✅ Supabase credentials loaded from environment variables.")
else:
    print("⚠️  Supabase credentials not configured. App will use TF-IDF scoring only.")

print("=" * 60)
print("✅ RecruitAI v2 Backend Ready!")
print("=" * 60)

SUPPORTED_EXTS = {"pdf", "docx", "doc", "txt"}

def extract_text(file) -> str:
    """Extract text from PDF, DOCX, DOC, or TXT files"""
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(file)
            text = "\n".join(page.extract_text() for page in pdf_reader.pages)
            return text.strip()
        
        elif filename.endswith('.docx'):
            doc = docx.Document(file)
            return "\n".join(paragraph.text for paragraph in doc.paragraphs)
        
        elif filename.endswith('.doc'):
            print(f"⚠️  .doc format detected. Converting...")
            return "[DOC file detected - limited support]"
        
        elif filename.endswith('.txt'):
            return file.read().decode('utf-8', errors='ignore')
        
        else:
            return ""
    
    except Exception as e:
        print(f"[ERROR] extract_text: {str(e)}")
        return ""

def compute_bert_score(jd: str, resume: str) -> int:
    """Compute resume-JD similarity using TF-IDF (0-100)"""
    try:
        if not jd or not resume:
            return 0
        
        corpus = [jd, resume]
        tfidf_matrix = VECTORIZER.fit_transform(corpus)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        
        score = int(round(similarity * 100))
        return max(0, min(100, score))
    
    except Exception as e:
        print(f"[ERROR] compute_bert_score: {str(e)}")
        return 0

def screen_with_supabase(jd: str, resume: str, candidate_name: str = "Unknown") -> dict:
    """Enhanced screening with Supabase LLM (fallback to TF-IDF)"""
    
    bert_score = compute_bert_score(jd, resume)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        return {
            "candidate_name": candidate_name,
            "supabase_score": bert_score,
            "key_strengths": [],
            "key_gaps": [],
            "final_recommendation": "Good Match" if bert_score >= 70 else "Moderate Match" if bert_score >= 50 else "Needs Review"
        }
    
    try:
        payload = {
            "model": "gpt-4",
            "messages": [{
                "role": "user",
                "content": f"Resume Quality Score (0-100) based on JD:\n\nJD:\n{jd[:500]}\n\nResume:\n{resume[:500]}\n\nProvide only a numeric score and brief assessment."
            }],
            "max_tokens": 100
        }
        
        headers = {
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json"
        }
        
        response = requests.post(
            f"{SUPABASE_URL}/functions/v1/screen",
            json=payload,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            supabase_score = int(result.get("score", bert_score))
        else:
            supabase_score = bert_score
    
    except Exception as e:
        print(f"[SUPABASE ERROR] {str(e)}")
        supabase_score = bert_score
    
    return {
        "candidate_name": candidate_name,
        "supabase_score": supabase_score,
        "key_strengths": [],
        "key_gaps": [],
        "final_recommendation": "Good Match" if supabase_score >= 70 else "Moderate Match" if supabase_score >= 50 else "Needs Review"
    }

def compute_hybrid_score(bert_score: int, supabase_score: int) -> int:
    """Calculate hybrid score: 40% BERT + 60% Supabase"""
    return int(round(BERT_WEIGHT * bert_score + GEMINI_WEIGHT * supabase_score))

@app.route("/screen", methods=["POST"])
def screen():
    """Screen resumes against job description"""
    print(f"[SCREEN] Screening request received")
    
    try:
        jd = ""
        jd_file = request.files.get("jd_file")
        jd_text = request.form.get("jd_text", "").strip()
        
        if jd_file:
            jd = extract_text(jd_file)
        elif jd_text:
            jd = jd_text
        
        if not jd:
            return jsonify({"success": False, "error": "No job description provided"}), 400
        
        resume_files = request.files.getlist("resume_files")
        if not resume_files:
            return jsonify({"success": False, "error": "No resumes provided"}), 400
        
        results = []
        errors = []
        
        for file in resume_files:
            if not file or not file.filename:
                continue
            
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext not in SUPPORTED_EXTS:
                errors.append(f"{file.filename}: Unsupported format")
                continue
            
            try:
                resume_text = extract_text(file)
                if not resume_text:
                    errors.append(f"{file.filename}: Could not extract text")
                    continue
                
                filename = file.filename.rsplit(".", 1)[0]
                supabase_result = screen_with_supabase(jd, resume_text, filename)
                
                bert_score = compute_bert_score(jd, resume_text)
                supabase_score = supabase_result.get("supabase_score", bert_score)
                hybrid_score = compute_hybrid_score(bert_score, supabase_score)
                
                results.append({
                    "filename": file.filename,
                    "candidate_name": supabase_result["candidate_name"],
                    "bert_score": bert_score,
                    "supabase_score": supabase_score,
                    "hybrid_score": hybrid_score,
                    "recommendation": supabase_result["final_recommendation"],
                    "strengths": supabase_result["key_strengths"],
                    "gaps": supabase_result["key_gaps"]
                })
            
            except Exception as e:
                print(f"[ERROR] {file.filename}: {str(e)}")
                errors.append(f"{file.filename}: {str(e)}")
                continue
        
        if not results:
            return jsonify({
                "success": False,
                "error": "No candidates could be processed.",
                "details": errors
            }), 500
        
        results.sort(key=lambda x: x["hybrid_score"], reverse=True)
        
        return jsonify({
            "success": True,
            "total": len(results),
            "weights": {"bert": BERT_WEIGHT, "supabase": GEMINI_WEIGHT},
            "mode": "hybrid",
            "errors": errors,
            "results": results
        })
    
    except Exception as e:
        print(f"[ERROR] Screening failed: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Production: Gunicorn runs the app directly
# No app.run() needed - gunicorn handles the server

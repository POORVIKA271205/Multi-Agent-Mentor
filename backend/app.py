"""
Multi Agent Mentor - Backend
A zero-external-dependency (no API keys) multi-agent career mentoring backend.
Rule-based / heuristic "AI" agents + SQLite storage.

Run:
    pip install -r requirements.txt
    python app.py
Server starts at http://127.0.0.1:5000
"""

import os
import json
import datetime
import jwt
from functools import wraps

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

from career_data import (
    ASSESSMENT_QUESTIONS,
    CAREER_PROFILES,
    ROADMAPS,
    JOB_TITLES,
    RESUME_REQUIRED_SECTIONS,
    RESUME_CONTACT_KEYWORDS,
    RESUME_ACTION_VERBS,
    CHAT_RULES,
    CHAT_FALLBACK,
)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
SECRET_KEY = "careerpilot-local-dev-secret-key"  # local-only demo app, no external exposure

app = Flask(__name__)
CORS(app)
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(BASE_DIR, 'careerpilot.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Assessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    answers_json = db.Column(db.Text)
    results_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Roadmap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    career = db.Column(db.String(120), nullable=False)
    topics_json = db.Column(db.Text)  # list of {id, title, done}
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ResumeReview(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    target_career = db.Column(db.String(120))
    score = db.Column(db.Integer)
    feedback_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    role = db.Column(db.String(20))  # 'user' or 'agent'
    content = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)


with app.app_context():
    db.create_all()


# ---------------------------------------------------------------------------
# Auth helpers
# ---------------------------------------------------------------------------

def make_token(user_id):
    payload = {
        "user_id": user_id,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(days=7),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            user = User.query.get(payload["user_id"])
            if not user:
                return jsonify({"error": "User not found"}), 401
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
        return f(user, *args, **kwargs)
    return decorated


def user_to_dict(u: User):
    return {"id": u.id, "name": u.name, "email": u.email, "bio": u.bio,
            "created_at": u.created_at.isoformat()}


# ---------------------------------------------------------------------------
# Auth routes
# ---------------------------------------------------------------------------

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json(force=True)
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "Name, email and password are required"}), 400
    if len(password) < 4:
        return jsonify({"error": "Password must be at least 4 characters"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "An account with this email already exists"}), 409

    user = User(name=name, email=email, password_hash=generate_password_hash(password))
    db.session.add(user)
    db.session.commit()
    token = make_token(user.id)
    return jsonify({"token": token, "user": user_to_dict(user)}), 201


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json(force=True)
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password"}), 401
    token = make_token(user.id)
    return jsonify({"token": token, "user": user_to_dict(user)})


@app.route("/api/auth/me", methods=["GET"])
@token_required
def me(current_user):
    return jsonify({"user": user_to_dict(current_user)})


@app.route("/api/profile", methods=["PUT"])
@token_required
def update_profile(current_user):
    data = request.get_json(force=True)
    if "name" in data and data["name"].strip():
        current_user.name = data["name"].strip()
    if "bio" in data:
        current_user.bio = data["bio"][:500]
    db.session.commit()
    return jsonify({"user": user_to_dict(current_user)})


# ---------------------------------------------------------------------------
# 1. Dashboard
# ---------------------------------------------------------------------------

@app.route("/api/dashboard", methods=["GET"])
@token_required
def dashboard(current_user):
    latest_assessment = (Assessment.query.filter_by(user_id=current_user.id)
                          .order_by(Assessment.created_at.desc()).first())
    latest_roadmap = (Roadmap.query.filter_by(user_id=current_user.id)
                       .order_by(Roadmap.created_at.desc()).first())
    latest_resume = (ResumeReview.query.filter_by(user_id=current_user.id)
                      .order_by(ResumeReview.created_at.desc()).first())

    top_career = None
    if latest_assessment:
        results = json.loads(latest_assessment.results_json)
        if results:
            top_career = results[0]

    roadmap_progress = None
    if latest_roadmap:
        topics = json.loads(latest_roadmap.topics_json)
        done = sum(1 for t in topics if t["done"])
        roadmap_progress = {
            "career": latest_roadmap.career,
            "total": len(topics),
            "done": done,
            "percent": round((done / len(topics)) * 100) if topics else 0,
        }

    resume_score = latest_resume.score if latest_resume else None

    assessments_count = Assessment.query.filter_by(user_id=current_user.id).count()
    chats_count = ChatMessage.query.filter_by(user_id=current_user.id, role="user").count()

    return jsonify({
        "user_name": current_user.name,
        "top_career": top_career,
        "roadmap_progress": roadmap_progress,
        "resume_score": resume_score,
        "assessments_count": assessments_count,
        "chats_count": chats_count,
        "supported_careers": list(CAREER_PROFILES.keys()),
    })


# ---------------------------------------------------------------------------
# 2. Career Assessment Agent
# ---------------------------------------------------------------------------

@app.route("/api/assessment/questions", methods=["GET"])
def get_questions():
    # strip trait weights before sending to client
    clean = [{"id": q["id"], "question": q["question"],
              "options": {k: v["label"] for k, v in q["options"].items()}}
             for q in ASSESSMENT_QUESTIONS]
    return jsonify({"questions": clean})


def _score_careers(answers: dict):
    trait_totals = {}
    for q in ASSESSMENT_QUESTIONS:
        chosen = answers.get(q["id"])
        if chosen and chosen in q["options"]:
            for trait, weight in q["options"][chosen]["traits"].items():
                trait_totals[trait] = trait_totals.get(trait, 0) + weight

    results = []
    for career, profile in CAREER_PROFILES.items():
        ideal = profile["traits"]
        # cosine-like similarity using simple dot product normalized by ideal magnitude
        dot = sum(trait_totals.get(t, 0) * w for t, w in ideal.items())
        ideal_mag = sum(w * w for w in ideal.values()) ** 0.5
        user_mag = sum(v * v for v in trait_totals.values()) ** 0.5 or 1
        similarity = dot / (ideal_mag * user_mag) if ideal_mag else 0
        fit_score = round(max(0, min(1, similarity)) * 100)
        results.append({
            "career": career,
            "fit_score": fit_score,
            "description": profile["description"],
            "core_skills": profile["core_skills"],
            "avg_salary_inr": profile["avg_salary_inr"],
        })

    results.sort(key=lambda r: r["fit_score"], reverse=True)
    return results


@app.route("/api/assessment/submit", methods=["POST"])
@token_required
def submit_assessment(current_user):
    data = request.get_json(force=True)
    answers = data.get("answers", {})
    if not answers:
        return jsonify({"error": "No answers provided"}), 400

    best_career_options = _score_careers(answers)

    record = Assessment(
        user_id=current_user.id,
        answers_json=json.dumps(answers),
        results_json=json.dumps(best_career_options),
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({
        "assessment_id": record.id,
        "best_career_options": best_career_options,
    })


@app.route("/api/assessment/history", methods=["GET"])
@token_required
def assessment_history(current_user):
    records = (Assessment.query.filter_by(user_id=current_user.id)
               .order_by(Assessment.created_at.desc()).all())
    return jsonify({"history": [
        {"id": r.id, "created_at": r.created_at.isoformat(),
         "best_career_options": json.loads(r.results_json)}
        for r in records
    ]})


# ---------------------------------------------------------------------------
# 3. Learning Roadmap Agent
# ---------------------------------------------------------------------------

@app.route("/api/roadmap/careers", methods=["GET"])
def roadmap_careers():
    return jsonify({"careers": list(ROADMAPS.keys())})


@app.route("/api/roadmap/generate", methods=["POST"])
@token_required
def generate_roadmap(current_user):
    data = request.get_json(force=True)
    career = data.get("career")
    if career not in ROADMAPS:
        return jsonify({"error": "Unknown career. Choose one of: " + ", ".join(ROADMAPS.keys())}), 400

    topics = [{"id": i + 1, "title": title, "done": False}
              for i, title in enumerate(ROADMAPS[career])]

    record = Roadmap(user_id=current_user.id, career=career, topics_json=json.dumps(topics))
    db.session.add(record)
    db.session.commit()

    return jsonify({"roadmap_id": record.id, "career": career, "topics": topics})


@app.route("/api/roadmap/current", methods=["GET"])
@token_required
def current_roadmap(current_user):
    record = (Roadmap.query.filter_by(user_id=current_user.id)
              .order_by(Roadmap.created_at.desc()).first())
    if not record:
        return jsonify({"roadmap": None})
    return jsonify({"roadmap": {
        "roadmap_id": record.id,
        "career": record.career,
        "topics": json.loads(record.topics_json),
    }})


@app.route("/api/roadmap/<int:roadmap_id>/toggle/<int:topic_id>", methods=["POST"])
@token_required
def toggle_topic(current_user, roadmap_id, topic_id):
    record = Roadmap.query.filter_by(id=roadmap_id, user_id=current_user.id).first()
    if not record:
        return jsonify({"error": "Roadmap not found"}), 404
    topics = json.loads(record.topics_json)
    for t in topics:
        if t["id"] == topic_id:
            t["done"] = not t["done"]
    record.topics_json = json.dumps(topics)
    db.session.commit()
    done = sum(1 for t in topics if t["done"])
    return jsonify({"topics": topics, "percent": round((done / len(topics)) * 100) if topics else 0})


# ---------------------------------------------------------------------------
# 4. Resume Review Agent
# ---------------------------------------------------------------------------

def _review_resume(text: str, target_career: str | None):
    text_lower = text.lower()
    word_count = len(text.split())

    section_hits = [s for s in RESUME_REQUIRED_SECTIONS if s in text_lower]
    missing_sections = [s for s in RESUME_REQUIRED_SECTIONS if s not in section_hits]

    has_contact = any(k in text_lower for k in RESUME_CONTACT_KEYWORDS)
    action_verb_hits = [v for v in RESUME_ACTION_VERBS if v in text_lower]
    has_numbers = any(ch.isdigit() for ch in text)

    keyword_hits, missing_keywords = [], []
    if target_career and target_career in CAREER_PROFILES:
        skills = CAREER_PROFILES[target_career]["core_skills"]
        keyword_hits = [s for s in skills if s.lower() in text_lower]
        missing_keywords = [s for s in skills if s.lower() not in text_lower]

    # --- Scoring heuristic (out of 100) ---
    score = 0
    score += min(30, len(section_hits) * 6)                       # sections: up to 30
    score += 15 if has_contact else 0                              # contact info: 15
    score += min(20, len(action_verb_hits) * 4)                    # action verbs: up to 20
    score += 10 if has_numbers else 0                              # quantified impact: 10
    score += min(15, len(keyword_hits) * 3) if target_career else 10  # keyword match: up to 15
    length_score = 10 if 150 <= word_count <= 900 else 5
    score += length_score
    score = min(100, score)

    feedback = []
    if missing_sections:
        feedback.append(f"Add these missing sections: {', '.join(missing_sections)}.")
    if not has_contact:
        feedback.append("Add clear contact info (email, phone, or LinkedIn) near the top.")
    if len(action_verb_hits) < 3:
        feedback.append("Use more strong action verbs (e.g. built, led, improved, launched).")
    if not has_numbers:
        feedback.append("Quantify achievements with numbers (e.g. 'increased efficiency by 30%').")
    if target_career and missing_keywords:
        feedback.append(f"For {target_career}, consider adding these skills if you have them: "
                         f"{', '.join(missing_keywords[:5])}.")
    if word_count < 150:
        feedback.append("Your resume looks quite short — add more detail on projects/experience.")
    elif word_count > 900:
        feedback.append("Your resume is long — try trimming to the most relevant, impactful points.")
    if not feedback:
        feedback.append("Great job! Your resume covers the key fundamentals well.")

    return {
        "score": score,
        "word_count": word_count,
        "sections_found": section_hits,
        "missing_sections": missing_sections,
        "action_verbs_found": action_verb_hits,
        "has_contact_info": has_contact,
        "has_quantified_impact": has_numbers,
        "matched_keywords": keyword_hits,
        "missing_keywords": missing_keywords,
        "feedback": feedback,
    }


@app.route("/api/resume/review", methods=["POST"])
@token_required
def review_resume(current_user):
    data = request.get_json(force=True)
    text = (data.get("resume_text") or "").strip()
    target_career = data.get("target_career")
    if len(text) < 20:
        return jsonify({"error": "Please paste your resume text (at least a few sentences)."}), 400

    result = _review_resume(text, target_career)

    record = ResumeReview(
        user_id=current_user.id,
        target_career=target_career,
        score=result["score"],
        feedback_json=json.dumps(result),
    )
    db.session.add(record)
    db.session.commit()

    return jsonify({"review_id": record.id, **result})


@app.route("/api/resume/history", methods=["GET"])
@token_required
def resume_history(current_user):
    records = (ResumeReview.query.filter_by(user_id=current_user.id)
               .order_by(ResumeReview.created_at.desc()).all())
    return jsonify({"history": [
        {"id": r.id, "created_at": r.created_at.isoformat(), "score": r.score,
         "target_career": r.target_career}
        for r in records
    ]})


# ---------------------------------------------------------------------------
# 5. Career Chat Agent
# ---------------------------------------------------------------------------

def _chat_reply(message: str) -> str:
    msg_lower = message.lower()
    for keywords, reply in CHAT_RULES:
        if any(k in msg_lower for k in keywords):
            return reply
    return CHAT_FALLBACK


@app.route("/api/chat/message", methods=["POST"])
@token_required
def chat_message(current_user):
    data = request.get_json(force=True)
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Message cannot be empty"}), 400

    reply = _chat_reply(message)

    db.session.add(ChatMessage(user_id=current_user.id, role="user", content=message))
    db.session.add(ChatMessage(user_id=current_user.id, role="agent", content=reply))
    db.session.commit()

    return jsonify({"reply": reply})


@app.route("/api/chat/history", methods=["GET"])
@token_required
def chat_history(current_user):
    records = (ChatMessage.query.filter_by(user_id=current_user.id)
               .order_by(ChatMessage.created_at.asc()).all())
    return jsonify({"history": [
        {"role": r.role, "content": r.content, "created_at": r.created_at.isoformat()}
        for r in records
    ]})


# ---------------------------------------------------------------------------
# 6. Job Recommendation Agent
# ---------------------------------------------------------------------------

@app.route("/api/jobs/recommend", methods=["POST"])
@token_required
def recommend_jobs(current_user):
    data = request.get_json(force=True)
    career = data.get("career")
    user_skills = set(s.strip().lower() for s in data.get("skills", []) if s.strip())

    if career and career in JOB_TITLES:
        careers_to_use = [career]
    else:
        # fall back to latest assessment's top career
        latest = (Assessment.query.filter_by(user_id=current_user.id)
                  .order_by(Assessment.created_at.desc()).first())
        if latest:
            results = json.loads(latest.results_json)
            careers_to_use = [results[0]["career"]] if results else list(JOB_TITLES.keys())[:1]
        else:
            careers_to_use = list(JOB_TITLES.keys())[:1]

    recommendations = []
    for c in careers_to_use:
        for job in JOB_TITLES.get(c, []):
            job_skills = set(s.lower() for s in job["skills"])
            overlap = len(job_skills & user_skills)
            match_score = round((overlap / len(job_skills)) * 100) if user_skills and job_skills else 60
            recommendations.append({
                "career": c,
                "title": job["title"],
                "level": job["level"],
                "required_skills": job["skills"],
                "match_score": match_score,
            })

    recommendations.sort(key=lambda r: r["match_score"], reverse=True)
    return jsonify({"recommendations": recommendations})


@app.route("/api/jobs/careers", methods=["GET"])
def job_careers():
    return jsonify({"careers": list(JOB_TITLES.keys())})


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "Multi Agent Mentor backend"})


if __name__ == "__main__":
    print("=" * 60)
    print("Multi Agent Mentor backend running at http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)

# ruff: noqa: E402
from __future__ import annotations

from functools import wraps

from flask import Flask, jsonify, request, render_template
from jwt import PyJWTError

from src_bootstrap import ensure_src_on_path

ensure_src_on_path()

from nova.auth import verify_jwt_token
from nova.slots.slot06_cultural_synthesis.engine import (
    CulturalSynthesisEngine,
    CulturalProfile,
    GuardrailValidationResult,
)
from nova.slots.slot06_cultural_synthesis.adapter import MulticulturalTruthSynthesisAdapter

# Initialize the Flask app and the Slot 6 engine adapter
app = Flask(__name__, template_folder="interface")
cultural_synthesis_engine = MulticulturalTruthSynthesisAdapter(CulturalSynthesisEngine())


def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return jsonify({"error": "Unauthorized"}), 401
        token = header.split(" ", 1)[1]
        try:
            verify_jwt_token(token)
        except PyJWTError:
            return jsonify({"error": "Invalid token"}), 401
        return func(*args, **kwargs)

    return wrapper


@app.route("/")
def index():
    return render_template("test_slot6_live.html")


@app.route("/api/analyze", methods=["POST"])
@require_auth
def analyze():
    raw = request.get_json(silent=True)
    data = raw if isinstance(raw, dict) else {}
    institution_name = data.get("institution_name")
    context = data.get("cultural_context")
    if not institution_name or not isinstance(context, dict):
        return (
            jsonify(
                {
                    "error": "Missing required fields: institution_name and cultural_context",
                }
            ),
            400,
        )
    profile: CulturalProfile = cultural_synthesis_engine.analyze_cultural_context(
        institution_name, context
    )
    return jsonify({"ok": True, **profile})


@app.route("/api/validate", methods=["POST"])
@require_auth
def validate():
    raw = request.get_json(silent=True)
    data = raw if isinstance(raw, dict) else {}
    profile = data.get("profile")
    if not isinstance(profile, dict):
        return jsonify({"error": "Profile data is required"}), 400
    payload = data.get("payload")
    if not isinstance(payload, dict):
        return jsonify({"error": "payload must be a JSON object"}), 400
    institution_type = data.get("institutionType", "")
    result: GuardrailValidationResult = cultural_synthesis_engine.validate_cultural_deployment(
        profile, institution_type, payload
    )
    return jsonify(
        {
            "result": result.result.value,
            "compliance_score": result.compliance_score,
            "violations": result.violations,
            "recommendations": result.recommendations,
        }
    )


@app.route("/api/validate_architecture", methods=["POST"])
@app.route("/validate_architecture", methods=["POST"])
@require_auth
def validate_architecture():
    """Light‑weight schema check for Slot‑10 architecture payloads."""
    raw = request.get_json(silent=True)
    data = raw if isinstance(raw, dict) else {}
    required = {
        "analysis",
        "cultural_alignment",
        "psychology_matrix",
        "philosophy_enforcement",
        "diversity_model",
    }
    if not required.issubset(data):
        return (
            jsonify(
                {
                    "client": data.get("client", "test"),
                    "validation": "failed",
                    "error": "Missing required fields",
                }
            ),
            400,
        )
    return jsonify({key: data[key] for key in required})


if __name__ == "__main__":
    import os
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    print("🚀 Starting NOVA Slot 6 Live Testing Server...")
    print("🌍 Open your browser and navigate to http://127.0.0.1:5000")
    if debug_mode:
        print("⚠️  DEBUG MODE ENABLED (set FLASK_DEBUG=0 for production)")
    app.run(debug=debug_mode)

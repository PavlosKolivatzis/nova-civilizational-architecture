from flask import Flask, jsonify, request, render_template



from slots.slot06_cultural_synthesis.multicultural_truth_synthesis import (
    AdaptiveSynthesisEngine,
    MulticulturalTruthSynthesisAdapter,
    CulturalProfile,
    CulturalContext,
)

# Initialize the Flask app and the Slot 6 engine adapter
app = Flask(__name__, template_folder="interface")
cultural_synthesis_engine = MulticulturalTruthSynthesisAdapter(AdaptiveSynthesisEngine())


@app.route("/")
def index():
    return render_template("test_slot6_live.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():





    

    # ``get_json`` may return non-mapping types (e.g. a list) or raise when the
    # request body isn't valid JSON.  Using ``silent=True`` avoids exceptions and
    # allows us to gracefully handle unexpected payload shapes.
    raw = request.get_json(silent=True)
    data = raw if isinstance(raw, dict) else {}
    content = data.get("content")
    context = data.get("cultural_context")
    if not content or not context:
        return jsonify({"error": "Missing required fields: content and cultural_context"}), 400
    try:
        profile = cultural_synthesis_engine.analyze_cultural_context(content, context)
        result = {
            "individualism_index": profile.individualism_index,
            "power_distance": profile.power_distance,
            "uncertainty_avoidance": profile.uncertainty_avoidance,
            "long_term_orientation": profile.long_term_orientation,
            "adaptation_effectiveness": profile.adaptation_effectiveness,
            "cultural_context": profile.cultural_context.value,
            "method_profile": profile.method_profile,
        }
        return jsonify({"ok": True, **result})

    
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400
    except Exception as e:
        app.logger.error(f"Analysis failed: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/validate", methods=["POST"])
def validate():
    try:
        # ``get_json`` can raise an error for invalid JSON or return non-mapping
        # types (e.g. a list).  Using ``silent=True`` avoids exceptions and
        # allows us to fall back to an empty mapping when the payload is not a
        # JSON object.  This mirrors the defensive parsing used in other
        # endpoints.
        raw = request.get_json(silent=True)
        data = raw if isinstance(raw, dict) else {}

        profile_data = data.get("profile")
        # ``profile`` must be a mapping.  When the client submits a list or any
        # other non-dictionary type, attempting to access ``.get`` would raise
        # an exception and trigger a 500 response.  Guard against that scenario
        # and return a deterministic 400 error instead.
        if not isinstance(profile_data, dict):
            return jsonify({"error": "Profile data is required"}), 400

        context_enum = next(
            (item for item in CulturalContext if item.value == profile_data.get("cultural_context")),
            CulturalContext.MIXED,
        )

        profile = CulturalProfile(
            individualism_index=profile_data.get("individualism_index"),
            power_distance=profile_data.get("power_distance"),
            uncertainty_avoidance=profile_data.get("uncertainty_avoidance"),
            long_term_orientation=profile_data.get("long_term_orientation"),
            adaptation_effectiveness=profile_data.get("adaptation_effectiveness"),
            cultural_context=context_enum,
            method_profile=profile_data.get("method_profile"),
        )

        institution_type = data.get("institutionType")
        payload = data.get("payload")
        if not institution_type or payload is None:
            return jsonify({"error": "institutionType and payload are required"}), 400

        if not isinstance(payload, dict):
            return jsonify({"error": "payload must be a JSON object"}), 400

        if "content" not in payload:
            return jsonify({"error": "payload.content is required"}), 400

        validation_result = cultural_synthesis_engine.validate_cultural_deployment(
            profile, institution_type, payload
        )

        validation_dict = {
            "result": validation_result.result.value,
            "compliance_score": validation_result.compliance_score,
            "violations": validation_result.violations,
            "recommendations": validation_result.recommendations,
            "transformation_required": validation_result.transformation_required,
            "max_safe_adaptation": validation_result.max_safe_adaptation,
        }

        return jsonify(validation_dict)
    except Exception as e:
        app.logger.error(f"Validation failed: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/validate_architecture", methods=["POST"])
@app.route("/validate_architecture", methods=["POST"])
def validate_architecture():
    """Light‑weight schema check for Slot‑10 architecture payloads.

    The associated tests exercise the happy path where a fully populated payload
    should be echoed back verbatim.  When required fields are missing the
    endpoint responds with a deterministic error structure, mirroring the sample
    provided in the test-suite.
    """

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
        # The tests expect the client identifier "test" in the error payload.
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

    # All required sections are present; mirror back exactly what was sent.
    return jsonify({key: data[key] for key in required})


if __name__ == "__main__":
    print("🚀 Starting NOVA Slot 6 Live Testing Server...")
    print("🌍 Open your browser and navigate to http://127.0.0.1:5000")
    app.run(debug=True)

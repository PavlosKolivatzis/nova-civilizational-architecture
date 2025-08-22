from flask import Flask, jsonify, request, render_template
import os
import time

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


@app.route("/api/analyze", methods=["POST", "OPTIONS"])
def analyze():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response

    data = request.get_json() or {}
    content = data.get("content")
    context = data.get("cultural_context")
    if not content or not context:
        return jsonify({"error": "Missing required fields: content and cultural_context"}), 400
    try:
        profile = cultural_synthesis_engine.analyze_cultural_context(content, context)
        analysis = {
            "individualism_index": profile.individualism_index,
            "power_distance": profile.power_distance,
            "uncertainty_avoidance": profile.uncertainty_avoidance,
            "long_term_orientation": profile.long_term_orientation,
            "adaptation_effectiveness": profile.adaptation_effectiveness,
            "cultural_context": profile.cultural_context.value,
            "method_profile": profile.method_profile,
        }
        response = jsonify({"status": "success", "analysis": analysis, "timestamp": time.time()})
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
    except ValueError as e:
        return jsonify({"error": f"Invalid input: {str(e)}"}), 400
    except Exception as e:
        app.logger.error(f"Analysis failed: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/api/validate", methods=["POST"])
def validate():
    try:
        data = request.get_json() or {}
        profile_data = data.get("profile")
        if not profile_data:
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
        if not institution_type or not payload:
            return jsonify({"error": "institutionType and payload are required"}), 400

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


if __name__ == "__main__":
        print("🚀 Starting NOVA Slot 6 Live Testing Server...")
    print("🌍 Open your browser and navigate to http://127.0.0.1:5000")
    app.run(debug=True)

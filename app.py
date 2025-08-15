from flask import Flask, jsonify, request, render_template
import os
import sys

# Add the slots directory to the Python path to find our module
sys.path.insert(0, os.path.abspath('slots'))
from slot06_cultural_truth_synthesis.multicultural_truth_synthesis import MulticulturalTruthSynthesis

# Initialize the Flask app and the Slot 6 engine
app = Flask(__name__, template_folder='.')
engine = MulticulturalTruthSynthesis()

@app.route('/')
def index():
    """Serve the main HTML testing page."""
    # We will use 'interface.html' as the filename for the testing page
    return render_template('interface.html')

@app.route('/api/analyze', methods=['POST'])
def analyze():
    """API endpoint to perform cultural analysis."""
    data = request.json
    
    # Extract data from the incoming request
    institution_name = data.get('institutionName', 'Unnamed Institution')
    context = data.get('context', {})
    
    # Use the actual Slot 6 engine to analyze the data
    profile = engine.analyze_cultural_context(institution_name, context)
    
    # Convert the profile object to a dictionary for the response
    profile_dict = {
        "individualism_index": profile.individualism_index,
        "power_distance": profile.power_distance,
        "uncertainty_avoidance": profile.uncertainty_avoidance,
        "long_term_orientation": profile.long_term_orientation,
        "adaptation_effectiveness": profile.adaptation_effectiveness,
        "cultural_context": profile.cultural_context.value,
        "method_profile": profile.method_profile
    }
    
    return jsonify(profile_dict)

@app.route('/api/validate', methods=['POST'])
def validate():
    """API endpoint to perform guardrail validation."""
    data = request.json
    
    # Re-create a CulturalProfile object from the provided profile data
    profile_data = data.get('profile')
    if not profile_data:
        return jsonify({"error": "Profile data is required"}), 400
        
    # Find the correct CulturalContext enum member
    context_enum = next((item for item in CulturalContext if item.value == profile_data.get('cultural_context')), CulturalContext.MIXED)
    
    profile = CulturalProfile(
        individualism_index=profile_data.get('individualism_index'),
        power_distance=profile_data.get('power_distance'),
        uncertainty_avoidance=profile_data.get('uncertainty_avoidance'),
        long_term_orientation=profile_data.get('long_term_orientation'),
        adaptation_effectiveness=profile_data.get('adaptation_effectiveness'),
        cultural_context=context_enum,
        method_profile=profile_data.get('method_profile')
    )

    institution_type = data.get('institutionType')
    payload = data.get('payload')
    
    # Use the engine to validate the deployment
    validation_result = engine.validate_cultural_deployment(profile, institution_type, payload)
    
    # Convert the result to a dictionary
    validation_dict = {
        "result": validation_result.result.value,
        "compliance_score": validation_result.compliance_score,
        "violations": validation_result.violations,
        "recommendations": validation_result.recommendations,
        "transformation_required": validation_result.transformation_required,
        "max_safe_adaptation": validation_result.max_safe_adaptation
    }
    
    return jsonify(validation_dict)

if __name__ == '__main__':
    print("🚀 Starting NOVA Slot 6 Live Testing Server...")
    print("🌍 Open your browser and navigate to http://127.0.0.1:5000")
    app.run(debug=True)

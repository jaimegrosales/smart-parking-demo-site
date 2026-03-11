from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from datetime import datetime
from prediction_service import predict_parking_availability

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
# Parking Decks
decks = [
    #Chesapeake Parking Zones
    #Missing Faculty Zone
    {"name": "chesapeakeAccessible", "value": 0},
    {"name": "chesapeakeElectric", "value": 0},
    {"name": "chesapeakeCommuter", "value": 0},

    #Ballard Parking Zones
    {"name": "ballardAccessible", "value": 0},
    {"name": "ballardElectric", "value": 0},
    {"name": "ballardFaculty", "value": 0},
    {"name": "ballardCommuter", "value": 0},

    #Champions Parking Zones
    {"name": "championsAccessible", "value": 0},
    {"name": "championsElectric", "value": 0},
    {"name": "championsFaculty", "value": 0},
    {"name": "championsCommuter", "value": 0},

    #Warsaw Parking Zones
    {"name": "warsawAccessible", "value": 0},
    {"name": "warsawElectric", "value": 0},
    {"name": "warsawFaculty", "value": 0},
    {"name": "warsawCommuter", "value": 0},

    #Grace Parking Zones
    {"name": "graceAccessible", "value": 0},
    {"name": "graceElectric", "value": 0},
    {"name": "graceFaculty", "value": 0},
    {"name": "graceCommuter", "value": 0},

    #Mason Parking Zones
    #Missing Commuter Zone
    {"name": "masonAccessible", "value": 0},
    {"name": "masonElectric", "value": 0},
    {"name": "masonFaculty", "value": 0}
]

# Get a single parking deck by name
@app.route('/decks/<string:deck_name>', methods=['GET'])
@cross_origin()
def get_deck(deck_name):
    deck = next((u for u in decks if u['name'] == deck_name), None)
    if deck:
        return jsonify(deck)
    return jsonify({"error": "User not found"}), 404

#Get all parking decks
@app.route('/decks', methods=['GET'])
@cross_origin()
def get_decks():
    return jsonify(decks)

# Update a parking deck
@app.route('/decks/<string:deck_name>', methods=['PUT'])
@cross_origin()
def update_deck(deck_name):
    deck = next((u for u in decks if u['name'] == deck_name), None)
    if deck:
        data = request.get_json()
        deck.update(data)
        return jsonify(deck)
    return jsonify({"error": "Deck not found"}), 404

# Parking Availability Prediction Endpoint
@app.route('/predict', methods=['POST'])
@cross_origin()
def predict_parking():
    """
    Predict parking availability at arrival time.
    
    Expected JSON payload:
    {
        "arrival_time": "2024-02-03T14:30:00",  // ISO format datetime
        "garage_name": "Chesapeake Hall Parking Deck",
        "zone_type": "commuter"  // optional: commuter, accessible, electric, faculty
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Validate required fields
        if 'arrival_time' not in data or 'garage_name' not in data:
            return jsonify({"error": "Missing required fields: arrival_time, garage_name"}), 400
        
        # Parse arrival time
        try:
            arrival_datetime = datetime.fromisoformat(data['arrival_time'].replace('Z', '+00:00'))
        except ValueError as e:
            return jsonify({"error": f"Invalid arrival_time format. Use ISO format: {e}"}), 400
        
        garage_name = data['garage_name']
        zone_type = data.get('zone_type', 'commuter')
        
        # Get prediction
        prediction = predict_parking_availability(arrival_datetime, garage_name, zone_type)
        
        if 'error' in prediction:
            return jsonify(prediction), 500
        
        # Format response
        response = {
            "success": True,
            "prediction": {
                "garage_name": garage_name,
                "zone_type": zone_type,
                "arrival_time": data['arrival_time'],
                "predicted_spaces": prediction['predicted_spaces'],
                "availability_percentage": round(prediction['availability_percentage'], 1),
                "confidence": round(prediction['confidence'] * 100, 1),  # Convert to percentage
                "model_used": prediction['model_used'],
                "zone_id": prediction['zone_id']
            },
            "metadata": {
                "prediction_time": datetime.now().isoformat(),
                "features": prediction.get('features', {})
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

def home():
    return "Welcome to the Flask REST API!"

if __name__ == '__main__':
    app.run(debug=True)

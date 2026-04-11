from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
from datetime import datetime
from pathlib import Path
import threading
import time
import os
import requests
import xml.etree.ElementTree as ET
from prediction_service import predict_parking_availability, prediction_service

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

OPENWEATHER_BASE_URL = 'https://api.openweathermap.org/data/2.5'
DEFAULT_WEATHER_LAT = 38.4495
DEFAULT_WEATHER_LON = -78.8690


def _get_repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _model_artifact_status() -> dict:
    model_dir = _get_repo_root() / 'final_ensemble' / 'final_ensemble'
    required_files = [
        'best_events_lgbm_production.pkl',
        'best_summer_lgbm_production.pkl',
        'best_schoolyear_lgbm_production.pkl',
        'events_stat_lookup_production.pkl',
        'summer_stat_lookup_production.pkl',
        'schoolyear_stat_lookup_production.pkl',
    ]
    artifacts = {}
    for name in required_files:
        file_path = model_dir / name
        artifacts[name] = {
            'exists': file_path.exists(),
            'size_bytes': file_path.stat().st_size if file_path.exists() else None,
        }
    return {
        'model_dir': str(model_dir),
        'artifacts': artifacts,
        'all_present': all(item['exists'] for item in artifacts.values()),
    }

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

# JMU sign feed and zone-to-deck mapping for live counter updates.
JMU_PARKING_FEED = (
    "https://www.jmu.edu/cgi-bin/parking_sign_data.cgi?hash="
    "53616c7465645f5f4c03eadd986acf07775e314a27e46ac7b36f35b8887e4e67"
    "ea5489a0733beab3e908f947f1a121913b0c1bbaa8d855d0a76820c2ce3b3b4f9"
    "c78a1a4638afe82e66c5e27e2c5af01|869835tg89dhkdnbnsv5sg5wg0vmcf4mfc"
    "fc2qwm5968unmeh5"
)

ZONE_TO_DECK = {
    '33': 'chesapeakeAccessible',
    '34': 'chesapeakeElectric',
    '19': 'chesapeakeCommuter',
    '29': 'ballardAccessible',
    '30': 'ballardElectric',
    '27': 'ballardFaculty',
    '22': 'ballardCommuter',
    '31': 'championsAccessible',
    '13': 'championsCommuter',
    '40': 'championsFaculty',
    '32': 'championsElectric',
    '38': 'warsawAccessible',
    '39': 'warsawElectric',
    '41': 'warsawFaculty',
    '42': 'warsawCommuter',
    '35': 'graceAccessible',
    '36': 'graceElectric',
    '6': 'graceFaculty',
    '4': 'graceCommuter',
    '37': 'masonAccessible',
    '28': 'masonElectric',
    '12': 'masonFaculty',
}


def _update_decks_from_feed_once() -> None:
    """Fetch one snapshot from JMU and update in-memory deck values."""
    response = requests.get(JMU_PARKING_FEED, timeout=20)
    response.raise_for_status()
    root = ET.fromstring(response.text)

    updated = 0
    for zone_vacancy in root.findall('./ZoneVacanSpaces'):
        zone_id = zone_vacancy.findtext('ZoneId')
        if zone_id not in ZONE_TO_DECK:
            continue

        result_text = zone_vacancy.findtext('Result')
        if result_text is None:
            continue

        try:
            value = int(result_text)
        except ValueError:
            continue

        deck_name = ZONE_TO_DECK[zone_id]
        deck = next((d for d in decks if d['name'] == deck_name), None)
        if deck is not None:
            deck['value'] = value
            updated += 1

    print(f"Live update complete: {updated} zones refreshed")


def _poll_jmu_feed_forever() -> None:
    """Background loop to keep live deck values fresh in hosted environments."""
    while True:
        try:
            _update_decks_from_feed_once()
        except Exception as exc:
            print(f"Live feed update error: {exc}")
        time.sleep(60)


def _start_live_updater() -> None:
    updater = threading.Thread(target=_poll_jmu_feed_forever, daemon=True)
    updater.start()


_start_live_updater()


def _openweather_api_key() -> str:
    return os.getenv('OPENWEATHER_API_KEY', '').strip()


def _weather_summary_from_payload(payload: dict) -> str:
    description = 'No description'
    if isinstance(payload.get('weather'), list) and payload['weather']:
        description = payload['weather'][0].get('description') or description
    description = description[:1].upper() + description[1:] if description else 'No description'

    temp_val = None
    if isinstance(payload.get('main'), dict):
        temp_val = payload['main'].get('temp')

    if isinstance(temp_val, (int, float)):
        return f"{description}, {float(temp_val):.1f}°F"
    return description

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
    POST /predict
    {
        "arrival_time": "2025-10-15T10:30:00",
        "garage_name":  "Ballard Parking Deck",
        "zone_type":    "faculty"
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON data provided"}), 400

    required = ['arrival_time', 'garage_name', 'zone_type']
    missing  = [f for f in required if f not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {missing}"}), 400

    try:
        arrival_datetime = datetime.fromisoformat(
            data['arrival_time'].replace('Z', '+00:00')
        )
    except ValueError as e:
        return jsonify({"error": f"Invalid arrival_time: {e}"}), 400

    result = prediction_service.predict_all_zones_for_type(
        arrival_datetime,
        data['garage_name'],
        data['zone_type'],
    )

    if 'error' in result:
        return jsonify(result), 400 if result.get('error_type') == 'validation' else 500

    return jsonify({
        "success":      True,
        "prediction":   result["primary"],
        "alternatives": result["alternatives"],
        "all_zones":    result["all_zones"],   # for map overlay / frontend use
        "metadata": {
            "model_used":      result["model_used"],
            "prediction_time": datetime.now().isoformat(),
        }
    })


@app.route('/weather/current', methods=['GET'])
@cross_origin()
def weather_current():
    api_key = _openweather_api_key()
    if not api_key:
        return jsonify({
            'error': 'OPENWEATHER_API_KEY is not configured on backend'
        }), 500

    lat = request.args.get('lat', type=float, default=DEFAULT_WEATHER_LAT)
    lon = request.args.get('lon', type=float, default=DEFAULT_WEATHER_LON)

    try:
        response = requests.get(
            f'{OPENWEATHER_BASE_URL}/weather',
            params={
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'imperial',
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        return jsonify({
            'success': True,
            'summary': _weather_summary_from_payload(payload),
            'raw': payload,
        })
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        return jsonify({'error': f'Weather API HTTP error: {exc}'}), status
    except requests.RequestException as exc:
        return jsonify({'error': f'Weather API request failed: {exc}'}), 502


@app.route('/weather/forecast', methods=['GET'])
@cross_origin()
def weather_forecast():
    api_key = _openweather_api_key()
    if not api_key:
        return jsonify({
            'error': 'OPENWEATHER_API_KEY is not configured on backend'
        }), 500

    lat = request.args.get('lat', type=float, default=DEFAULT_WEATHER_LAT)
    lon = request.args.get('lon', type=float, default=DEFAULT_WEATHER_LON)

    try:
        response = requests.get(
            f'{OPENWEATHER_BASE_URL}/forecast',
            params={
                'lat': lat,
                'lon': lon,
                'appid': api_key,
                'units': 'imperial',
            },
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()
        entries = payload.get('list', []) if isinstance(payload, dict) else []
        normalized = []
        for entry in entries:
            main = entry.get('main') or {}
            weather_items = entry.get('weather') or []
            description = ''
            if isinstance(weather_items, list) and weather_items:
                description = weather_items[0].get('description', '')
            normalized.append({
                'dt': entry.get('dt'),
                'temp': main.get('temp'),
                'desc': description,
            })

        return jsonify({
            'success': True,
            'forecast': normalized,
            'raw': payload,
        })
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else 502
        return jsonify({'error': f'Forecast API HTTP error: {exc}'}), status
    except requests.RequestException as exc:
        return jsonify({'error': f'Forecast API request failed: {exc}'}), 502


@app.route('/', methods=['GET'])
@cross_origin()
def home():
    return jsonify({"status": "ok", "message": "Smart Parking API is running"})

@app.route('/health', methods=['GET'])
@cross_origin()
def health():
    return jsonify({"status": "ok"})


@app.route('/version', methods=['GET'])
@cross_origin()
def version():
    return jsonify({
        'status': 'ok',
        'deploy': {
            'render_service_name': os.getenv('RENDER_SERVICE_NAME'),
            'render_git_commit': os.getenv('RENDER_GIT_COMMIT'),
            'render_git_branch': os.getenv('RENDER_GIT_BRANCH'),
            'render_instance_id': os.getenv('RENDER_INSTANCE_ID'),
        },
        'models': _model_artifact_status(),
    })

if __name__ == '__main__':
    app.run(debug=True)

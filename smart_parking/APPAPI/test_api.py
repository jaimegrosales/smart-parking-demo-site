#!/usr/bin/env python3
"""
Test the Flask API prediction endpoint directly
"""
import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, '/home/rosalejg/Downloads/smart-parking-capstone-main/smart_parking/APPAPI')

from appAPI import app
import json

def test_prediction_endpoint():
    """Test the /predict endpoint with a sample request"""
    with app.test_client() as client:
        # Test data
        test_data = {
            "garage_name": "Chesapeake Hall Parking Deck",
            "arrival_time": "2024-02-03T14:30:00", 
            "zone_type": "commuter"
        }
        
        print("🧪 Testing Flask API /predict endpoint")
        print("=" * 50)
        print(f"📋 Request: {json.dumps(test_data, indent=2)}")
        print()
        
        # Make the request
        response = client.post('/predict', 
                             data=json.dumps(test_data),
                             content_type='application/json')
        
        print(f"📊 Response Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.get_json()
            prediction_data = result.get('prediction', {})
            
            print("✅ Success! Prediction API Response:")
            print(f"   🎯 Predicted Spaces: {prediction_data.get('predicted_spaces')}")
            print(f"   📊 Availability: {prediction_data.get('availability_percentage'):.1f}%")
            print(f"   🎲 Confidence: {prediction_data.get('confidence')}")
            print(f"   🤖 Model Used: {prediction_data.get('model_used')}")
            print(f"   🏷️ Zone ID: {prediction_data.get('zone_id')}")
            print()
            print(f"🔍 Full Response: {json.dumps(result, indent=2)}")
            
            # Verify it's using real ML models (not fake math)
            predicted_spaces = prediction_data.get('predicted_spaces', 0)
            if predicted_spaces > 0 and prediction_data.get('model_used') in ['events', 'summer', 'school']:
                print("\n🎉 SUCCESS: API is using REAL ML models!")
                print(f"   Real prediction: {predicted_spaces} spaces")
                print(f"   Model: {prediction_data.get('model_used')}")
            else:
                print("\n❌ WARNING: API might still be using fake math")
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.get_data(as_text=True)}")

if __name__ == "__main__":
    test_prediction_endpoint()
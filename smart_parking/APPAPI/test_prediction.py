#!/usr/bin/env python3
"""
Test script to verify the real ML models are working
"""

from datetime import datetime
from prediction_service import predict_parking_availability

def test_prediction():
    """Test the prediction service with real ML models"""
    print("🔬 Testing Real ML Model Integration")
    print("=" * 50)
    
    # Test with Chesapeake Hall
    arrival_time = datetime(2024, 2, 3, 14, 30, 0)  # Saturday afternoon
    garage_name = "Chesapeake Hall Parking Deck"
    zone_type = "commuter"
    
    print(f"📍 Garage: {garage_name}")
    print(f"⏰ Arrival Time: {arrival_time}")
    print(f"🚗 Zone Type: {zone_type}")
    print()
    
    try:
        result = predict_parking_availability(arrival_time, garage_name, zone_type)
        
        if 'error' in result:
            print(f"❌ Error: {result['error']}")
        else:
            print("✅ Prediction Results:")
            print(f"   🎯 Predicted Spaces: {result['predicted_spaces']}")
            print(f"   📊 Availability: {result['availability_percentage']:.1f}%")
            print(f"   🎲 Confidence: {result['confidence']:.1f}")
            print(f"   🤖 Model Used: {result['model_used']}")
            print(f"   🏷️ Zone ID: {result['zone_id']}")
            print()
            print("🔧 Features:")
            features = result.get('features', {})
            for key, value in features.items():
                print(f"   {key}: {value}")
                
    except Exception as e:
        print(f"💥 Exception: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_prediction()
"""
Test script for ClearSkies API
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
API_URL = "http://localhost:5000"
API_KEY = os.getenv('API_KEY', 'test_key')

# Test coordinates
TEST_LOCATIONS = [
    {"name": "San Francisco", "latitude": 37.7749, "longitude": -122.4194},
    {"name": "New York", "latitude": 40.7128, "longitude": -74.0060},
    {"name": "Los Angeles", "latitude": 34.0522, "longitude": -118.2437},
]


def test_health_endpoint():
    """Test health check endpoint"""
    print("\n🔍 Testing Health Endpoint...")
    response = requests.get(f"{API_URL}/api/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200


def test_dashboard_endpoint():
    """Test unified dashboard endpoint"""
    print("\n🔍 Testing Dashboard Endpoint...")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    for location in TEST_LOCATIONS:
        print(f"\n📍 Testing: {location['name']}")

        payload = {
            "latitude": location["latitude"],
            "longitude": location["longitude"],
            "deviceId": "test-device-123",
            "userPreferences": {
                "sensitiveGroup": False,
                "units": "metric"
            }
        }

        response = requests.post(
            f"{API_URL}/dashboard",
            headers=headers,
            json=payload
        )

        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            data = response.json()

            # Print summary
            print(f"\n✅ Dashboard Data for {location['name']}:")
            print(f"   AQI: {data['data']['currentAQI']['raw']['aqi']}")
            print(f"   Category: {data['data']['currentAQI']['raw']['category']}")
            print(f"   AI Summary: {data['data']['currentAQI']['aiSummary']['brief']}")
            print(f"   Processing Time: {data['data']['metadata']['processingTime']}ms")

            # Save full response to file
            filename = f"test_response_{location['name'].lower().replace(' ', '_')}.json"
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"   📄 Full response saved to: {filename}")
        else:
            print(f"❌ Error: {response.json()}")

        print("-" * 60)


def test_auth():
    """Test authentication"""
    print("\n🔍 Testing Authentication...")

    # Test without auth
    print("\n1. Testing without Authorization header:")
    response = requests.post(
        f"{API_URL}/dashboard",
        json={"latitude": 37.7749, "longitude": -122.4194}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()['error']['code'] if response.status_code == 401 else 'Unexpected'}")

    # Test with invalid auth
    print("\n2. Testing with invalid token:")
    response = requests.post(
        f"{API_URL}/dashboard",
        headers={"Authorization": "Bearer invalid_token"},
        json={"latitude": 37.7749, "longitude": -122.4194}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()['error']['code'] if response.status_code == 401 else 'Unexpected'}")

    # Test with valid auth
    print("\n3. Testing with valid token:")
    response = requests.post(
        f"{API_URL}/dashboard",
        headers={"Authorization": f"Bearer {API_KEY}"},
        json={"latitude": 37.7749, "longitude": -122.4194}
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {'Success' if response.status_code == 200 else response.json()}")


if __name__ == "__main__":
    print("=" * 60)
    print("🌤️  ClearSkies API Test Suite")
    print("=" * 60)

    try:
        # Test health
        if test_health_endpoint():
            print("✅ Health check passed")
        else:
            print("❌ Health check failed")

        # Test auth
        test_auth()

        # Test dashboard
        test_dashboard_endpoint()

        print("\n" + "=" * 60)
        print("✅ All tests completed")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("   Make sure the Flask server is running: python app.py")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

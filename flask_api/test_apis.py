"""
Quick test to verify API keys are working
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_openaq():
    """Test OpenAQ API key"""
    api_key = os.getenv('OPENAQ_API_KEY')
    
    if not api_key:
        print("❌ OpenAQ API key not found")
        return False
    
    print(f"\n🔍 Testing OpenAQ API...")
    print(f"   API Key: {api_key[:20]}...")
    
    headers = {'X-API-Key': api_key}
    
    try:
        # Test with San Francisco coordinates
        params = {
            'coordinates': '37.7749,-122.4194',
            'radius': 25000,  # 25km
            'limit': 5
        }
        
        response = requests.get(
            'https://api.openaq.org/v3/latest',
            params=params,
            headers=headers,
            timeout=10
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"   ✅ Success! Found {len(results)} measurements")
            if results:
                print(f"   Sample: {results[0].get('parameter')} = {results[0].get('value')} {results[0].get('unit')}")
            return True
        else:
            print(f"   ❌ Error: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return False


def test_gemini():
    """Test Gemini API key"""
    api_key = os.getenv('GEMINI_API_KEY')
    
    if not api_key:
        print("❌ Gemini API key not found")
        return False
    
    print(f"\n🔍 Testing Gemini API...")
    print(f"   API Key: {api_key[:20]}...")
    
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')
        
        response = model.generate_content("Say 'API key is working!' in 5 words or less.")
        
        print(f"   ✅ Success! Response: {response.text.strip()}")
        return True
        
    except Exception as e:
        print(f"   ❌ Exception: {str(e)}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("🔑 API Key Validation Test")
    print("=" * 60)
    
    openaq_ok = test_openaq()
    gemini_ok = test_gemini()
    
    print("\n" + "=" * 60)
    print(f"📊 Results:")
    print(f"   OpenAQ: {'✅ Working' if openaq_ok else '❌ Failed'}")
    print(f"   Gemini: {'✅ Working' if gemini_ok else '❌ Failed'}")
    print("=" * 60)

import json
import requests

# Default local Ollama API endpoint
OLLAMA_URL = "http://localhost:11434/api/generate"
# Replace with the exact model name your app uses (e.g., 'llama3', 'mistral', etc.)
MODEL_NAME = "qwen2.5:7b" 

def test_ollama_connection():
    print("--- 1. Testing Connection to Ollama Server ---")
    try:
        # Check server tags endpoint
        tags_response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if tags_response.status_code == 200:
            print("✅ Successfully connected to Ollama backend daemon.")
            models = [m["name"] for m in tags_response.json().get("models", [])]
            print(f"📦 Installed models found: {models}")
            
            if MODEL_NAME not in models and f"{MODEL_NAME}:latest" not in models:
                print(f"⚠️ Warning: Target model '{MODEL_NAME}' not found in installed models list!")
        else:
            print(f"❌ Server responded with unexpected status code: {tags_response.status_code}")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to reach Ollama server. Is it running? Error: {e}")
        return

    print("\n--- 2. Testing Text Generation ---")
    payload = {
        "model": MODEL_NAME,
        "prompt": "Write a one-para confirmation that you are working.",
        "stream": False
    }
    
    try:
        print(f"Sending prompt to model '{MODEL_NAME}'...")
        response = requests.post(OLLAMA_URL, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            print("✅ Generation successful!")
            print(f"\n🤖 Ollama Response:\n{generated_text}")
        else:
            print(f"❌ Generation failed with status code: {response.status_code}")
            print(f"Response text: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out. The model might be loading too slowly or frozen.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Error during generation request: {e}")

if __name__ == "__main__":
    test_ollama_connection()

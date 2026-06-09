import google.generativeai as genai
import sys

def list_available_models(api_key):
    try:
        genai.configure(api_key=api_key)
        print("--- Kullanılabilir Modeller ---")
        models = genai.list_models()
        available = []
        for m in models:
            if 'generateContent' in m.supported_generation_methods:
                print(f"Model: {m.name}")
                available.append(m.name)
        return available
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return []

if __name__ == "__main__":
    if len(sys.argv) > 1:
        list_available_models(sys.argv[1])
    else:
        print("Lütfen bir API Key girin: python diagnostic.py YOUR_API_KEY")

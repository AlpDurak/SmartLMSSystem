import google.generativeai as genai
import os

class AIEngine:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model_name = self._find_best_model()
        if not self.model_name:
            # Fallback to a very common default if listing fails
            self.model_name = "models/gemini-1.5-pro"
        self.model = genai.GenerativeModel(self.model_name)

    def _find_best_model(self):
        try:
            # Try to find the best available model for this specific API key
            models = genai.list_models()
            preferred_order = [
                'models/gemini-1.5-flash',
                'models/gemini-1.5-flash-latest',
                'models/gemini-1.5-flash-8b',
                'models/gemini-1.5-pro',
                'models/gemini-1.5-pro-latest',
                'models/gemini-pro'
            ]
            
            available_models = [m.name for m in models if 'generateContent' in m.supported_generation_methods]
            
            for pref in preferred_order:
                if pref in available_models:
                    return pref
            
            if available_models:
                return available_models[0]
        except:
            pass
        return None

    def summarize(self, text):
        prompt = f"""
        Aşağıdaki üniversite ders materyali içeriğini (bir veya birden fazla dosya olabilir) bir öğrencinin sınavda en çok işine yarayacak şekilde kapsamlıca özetle. 
        Önemli kavramları kalın yaz (bold), maddeler halinde açıkla ve karmaşık konuları basitleştir.
        Dil: Türkçe
        
        İçerik:
        {text[:20000]}
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Özetleme sırasında hata oluştu. Kullandığınız API Key bu modeli ( {self.model_name} ) desteklemiyor olabilir. Hata: {str(e)}"

    def generate_exam(self, text, difficulty="Orta"):
        prompt = f"""
        Aşağıdaki ders materyallerine dayanarak, {difficulty} zorluk seviyesinde bir örnek sınav hazırla.
        Sınav içeriği şunları içermelidir:
        1. 5 adet Çoktan Seçmeli Soru (Şıklarıyla birlikte A, B, C, D, E).
        2. 3 adet Doğru/Yanlış sorusu.
        3. En sonda tüm soruların cevap anahtarı.
        
        Dil: Türkçe
        
        İçerik:
        {text[:20000]}
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Sınav oluşturma sırasında hata oluştu. Hata: {str(e)}"

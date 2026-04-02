import os
import json
from pathlib import Path
from groq import Groq
from django.conf import settings

class GroqService:
    def __init__(self):
        # Try to load from environment first
        self.api_key = os.environ.get("GROQ_API_KEY")
        
        # If not in environment, try loading from .env file directly
        if not self.api_key:
            env_path = Path(__file__).resolve().parent.parent / '.env'
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('GROQ_API_KEY='):
                            self.api_key = line.split('=', 1)[1].strip()
                            break
        
        if not self.api_key or self.api_key == 'your-groq-api-key-here':
            # Note: We fallback to 'your-groq-api-key-here' to avoid crashing if it's in .env as a placeholder
            print("Warning: GROQ_API_KEY not found or invalid.")
        
        self.client = Groq(api_key=self.api_key)
        self.model = "whisper-large-v3-turbo"

    def transcribe(self, audio_file, language=None):
        """
        Transcribe audio file using Groq's Whisper API.
        audio_file can be a file-like object or a path.
        """
        try:
            # Groq expects a file object or a tuple (filename, content, content_type)
            # For Django's UploadedFile, passing (file.name, file.read()) works best
            file_tuple = (audio_file.name, audio_file.read())
            
            # Context prompt to help Whisper with terminology and language detection
            context_prompt = "Ceci est une commande vocale pour l'application financière Akompta. L'utilisateur enregistre ses ventes, ses achats ou ses stocks. Ex: 'J'ai vendu 2 kilos de tomates', 'Paiement fournisseur', 'Ajouter du sucre au stock'."
            
            params = {
                "file": file_tuple,
                "model": self.model,
                "response_format": "json",
                "temperature": 0.0,
                "prompt": context_prompt
            }
            
            # Use 'fr' by default if no language is specified, to avoid wrong auto-detection
            if language:
                params["language"] = language.lower()[:2] # e.g. 'fr' or 'en'
            else:
                params["language"] = "fr" # Default to French for this app context
                
            transcription = self.client.audio.transcriptions.create(**params)
            return transcription.text
        except Exception as e:
            print(f"Error calling Groq STT: {e}")
            return None

    def process_text_command(self, text, context_products=None, model="llama-3.3-70b-versatile"):
        """
        Process text command using Groq's LLM models.
        """
        if context_products is None:
            context_products = []
            
        system_prompt = f"""
        You are an AI assistant for Akompta, a financial and inventory management app.
        Your task is to identify if the user wants to record a financial transaction (income/expense) or manage their inventory (create/update a product).
        
        RULES:
        1. If the user reports a SALE or PURCHASE of an item, it's a 'create_transaction'.
        2. If the user says they want to ADD, REGISTER, or CREATE an item in their catalog/stock, it's a 'create_product'.
        3. For 'create_transaction':
           - type: 'income' for sales, 'expense' for purchases/costs.
           - category: Use a descriptive name like 'Vente', 'Achat', 'Nourriture', etc.
           - name: A SHORT and DESCRIPTIVE name of the transaction (ex: 'Vente de Savon', 'Achat de Sac de Riz').
        
        4. For 'create_product':
           - name: The name of the product.
           - category: MUST BE exactly one of: 'vente', 'depense', 'stock'.
           - stock_status: MUST BE exactly one of: 'ok', 'low', 'rupture'.
        
        Inventory Context (Existing Products):
        {json.dumps(context_products)}
        
        Return ONLY a JSON object with this EXACT structure:
        
        If intent is 'create_transaction':
        {{
            "transcription": "...",
            "intent": "create_transaction",
            "data": {{
                "type": "income" or "expense",
                "amount": number,
                "currency": "FCFA",
                "category": "Descriptive category",
                "name": "Descriptive name",
                "date": "YYYY-MM-DD"
            }}
        }}

        If intent is 'create_product':
        {{
            "transcription": "...",
            "intent": "create_product",
            "data": {{
                "name": "Product name",
                "price": number,
                "unit": "Kg, Unit, etc.",
                "description": "...",
                "category": "vente" or "depense" or "stock",
                "stock_status": "ok" or "low" or "rupture"
            }}
        }}
        """
        
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                model=model,
                response_format={"type": "json_object"},
                temperature=0.0
            )
            
            result_text = chat_completion.choices[0].message.content
            return json.loads(result_text)
        except Exception as e:
            print(f"Error calling Groq LLM ({model}): {e}")
            return None

import os
import json
from pathlib import Path
from google import genai
from google.genai import types
from django.conf import settings

class GeminiService:
    def __init__(self):
        # Try to load from environment first
        self.api_key = os.environ.get("GEMINI_API_KEY")
        
        # If not in environment, try loading from .env file directly
        if not self.api_key:
            env_path = Path(__file__).resolve().parent.parent / '.env'
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('GEMINI_API_KEY='):
                            self.api_key = line.split('=', 1)[1].strip()
                            break
        
        if not self.api_key or self.api_key == 'your-gemini-api-key-here':
            raise ValueError("GEMINI_API_KEY not found or invalid. Please set it in backend/.env file")
        
        self.client = genai.Client(api_key=self.api_key)
        # Use free tier model with generous quotas
        self.model = "gemini-1.5-flash-latest"  # Stable and standard model name

    def process_voice_command(self, audio_bytes, mime_type="audio/mp3", context_products=None):
        """
        Process audio bytes to extract transaction details.
        Returns a dictionary with transcription and structured data.
        """
        if context_products is None:
            context_products = []

        prompt = f"""
        You are an AI assistant for a financial app called Akompta.
        Your task is to listen to the user's voice command and extract transaction details.
        
        The user might say things like:
        - "J'ai vendu la tomate pour 500FCFA le Kilo" (Income)
        - "J'ai payé un ordinateur à 300000FCFA" (Expense)
        
        Here is the list of products currently in the user's inventory:
        {json.dumps(context_products)}
        
        If the user mentions a product from this list but doesn't specify the price, use the price from the list to calculate the total amount (amount = quantity * price).
        
        Please perform the following:
        1. Transcribe the audio exactly as spoken (in French).
        2. Analyze the intent and extract structured data.
        
        Return ONLY a JSON object with the following structure:
        {{
            "transcription": "The exact transcription",
            "intent": "create_transaction",
            "data": {{
                "type": "income" or "expense",
                "amount": number (e.g. 500),
                "currency": "FCFA" or other,
                "category": "Category name (e.g. Vente, Alimentation, Transport, Technologie)",
                "name": "Description of the item or service (e.g. 'Vente de 3 Mangues')",
                "date": "YYYY-MM-DD" or null if not specified (assume today if null)
            }}
        }}
        
        Important: If a product price is found in the inventory list, ALWAYS calculate: amount = quantity * unit_price.
        
        If the audio is not in French or English, or is not clear or not related to a transaction, return:
        {{
            "transcription": "...",
            "intent": "unknown",
            "error": "The detected language is not supported. Please speak in French or English."
        }}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text)
            print(f"Gemini AI Voice Result: {result}")
            return result

        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return {
                "transcription": "",
                "intent": "error",
                "error": str(e)
            }

    def process_text_command(self, text, context_products=None):
        """
        Process text input to extract transaction details.
        """
        if context_products is None:
            context_products = []

        prompt = f"""
        You are an AI assistant for a financial app called Akompta.
        Your task is to analyze the user's text command and extract transaction details.
        
        The user might say things like:
        - "J'ai vendu la tomate pour 500FCFA le Kilo" (Income)
        - "J'ai payé un ordinateur à 300000FCFA" (Expense)
        - "Ajoute un produit Tomate à 200FCFA le bol, j'en ai 30 en stock" (Create Product)
        
        Here is the list of products currently in the user's inventory:
        {json.dumps(context_products)}
        
        If the user mentions a product from this list but doesn't specify the price, use the price from the list to calculate the total amount (amount = quantity * price).
        Example: If "Mangue" is in the list at 100 FCFA and the user says "vendu 3 mangues", the amount should be 300.
        
        Please perform the following:
        1. Analyze the intent and extract structured data.
        
        Return ONLY a JSON object with the following structure:
        
        For transactions:
        {{
            "transcription": "The input text",
            "intent": "create_transaction",
            "data": {{
                "type": "income" or "expense",
                "amount": number,
                "currency": "FCFA",
                "category": "Category name",
                "name": "Description (e.g. 'Vente de 3 Mangues')",
                "date": "YYYY-MM-DD"
            }}
        }}
        
        Important: If a product price is found in the inventory list, ALWAYS calculate: amount = quantity * unit_price.
        
        For products/inventory:
        {{
            "transcription": "The input text",
            "intent": "create_product",
            "data": {{
                "name": "Product name",
                "price": number,
                "unit": "Unit (e.g. bol, kg, unit)",
                "description": "Short description",
                "category": "vente" or "depense" or "stock",
                "stock_status": "ok" or "low" or "rupture"
            }}
        }}
        
        If the text is not in French or English, or is not clear, return:
        {{
            "transcription": "...",
            "intent": "unknown",
            "error": "The language is not supported. Please use French or English."
        }}
        """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        parts=[
                            types.Part.from_text(text=f"User command: {text}"),
                            types.Part.from_text(text=prompt)
                        ]
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            result = json.loads(response.text)
            print(f"Gemini AI Result: {result}")
            # Ensure transcription is the input text if not provided by AI
            if not result.get('transcription'):
                result['transcription'] = text
            return result

        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return {
                "transcription": text,
                "intent": "error",
                "error": str(e)
            }

    def process_insights(self, context_data):
        """
        Generate financial insights based on context data.
        """
        prompt = f"""
        Tu es un analyste financier expert pour l'application Akompta.
        Analyse les données suivantes (JSON) :
        {json.dumps(context_data)}

        Génère exactement 3 insights courts et percutants (max 1 phrase chacun) en Français :
        1. Une observation sur les ventes ou revenus.
        2. Une observation sur les dépenses.
        3. Une alerte sur le stock ou une recommandation.

        Format de réponse attendu : Une liste simple de 3 phrases séparées par des sauts de ligne. Pas de markdown complexe, pas de titres.
        """

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt
            )
            
            text = response.text or ""
            items = [line.strip() for line in text.split('\n') if line.strip()]
            return items[:3]

        except Exception as e:
            print(f"Error calling Gemini for insights: {e}")
            return [
                "Analyse des ventes en cours...",
                "Vérification des stocks...",
                "Calcul des marges..."
            ]

import os
import time
import requests
from pathlib import Path
from django.conf import settings

class AssemblyAIService:
    def __init__(self):
        # Try to load from environment first
        self.api_key = os.environ.get("ASSEMBLYAI_API_KEY")
        
        # If not in environment, try loading from .env file directly
        if not self.api_key:
            env_path = Path(__file__).resolve().parent.parent / '.env'
            if env_path.exists():
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith('ASSEMBLYAI_API_KEY='):
                            self.api_key = line.split('=', 1)[1].strip()
                            break
        
        if not self.api_key:
            print("Warning: ASSEMBLYAI_API_KEY not found.")
            
        self.headers = {
            "Authorization": self.api_key,
            "Content-Type": "application/json"
        }
        self.upload_url = "https://api.assemblyai.com/v2/upload"
        self.transcript_url = "https://api.assemblyai.com/v2/transcript"

    def upload_file(self, audio_file):
        """Upload audio file to AssemblyAI"""
        if not self.api_key:
            return None
        try:
            # AssemblyAI expects the raw file content in the body
            audio_file.seek(0)
            response = requests.post(
                self.upload_url,
                headers={"Authorization": self.api_key},
                data=audio_file.read()
            )
            if response.status_code != 200:
                print(f"AssemblyAI Upload Error: {response.status_code} - {response.text}")
                response.raise_for_status()
            return response.json()["upload_url"]
        except Exception as e:
            print(f"Error uploading to AssemblyAI: {e}")
            return None

    def transcribe(self, audio_file, language=None):
        """
        Transcribe audio file using AssemblyAI REST API.
        """
        if not self.api_key:
            return None
            
        try:
            # 1. Upload
            upload_url = self.upload_file(audio_file)
            if not upload_url:
                return None
                
            # Start transcription with required speech model
            lang_to_use = language.lower()[:2] if language else "fr"
            payload = {
                "audio_url": upload_url,
                "language_code": lang_to_use,
                "speech_models": ["universal-3-pro"] # Matches the error suggestion
            }

            response = requests.post(self.transcript_url, json=payload, headers=self.headers)
            if response.status_code != 200 and response.status_code != 201:
                print(f"AssemblyAI error response: {response.text}")
                response.raise_for_status()
                
            transcript_id = response.json()["id"]
            
            # 3. Polling for results
            polling_url = f"{self.transcript_url}/{transcript_id}"
            
            max_attempts = 30
            attempts = 0
            while attempts < max_attempts:
                polling_response = requests.get(polling_url, headers=self.headers)
                polling_response.raise_for_status()
                data = polling_response.json()
                
                if data["status"] == "completed":
                    return data["text"]
                elif data["status"] == "error":
                    print(f"AssemblyAI transcription error: {data.get('error')}")
                    return None
                    
                attempts += 1
                time.sleep(1) # Poll every second
                
            print("AssemblyAI transcription timed out.")
            return None
            
        except Exception as e:
            print(f"Error calling AssemblyAI STT: {e}")
            return None

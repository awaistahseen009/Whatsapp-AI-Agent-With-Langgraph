from config import Config
from elevenlabs import ElevenLabs, VoiceSettings
import asyncio

class TTS:
    def __init__(self):
        self._required_vars = ["ELEVEN_LABS_API_KEY"]
        self.validate_vars()
        self.client = ElevenLabs(
            api_key=Config.ELEVEN_LABS_API_KEY
        )
    
    def validate_vars(self):
        if not Config.ELEVEN_LABS_API_KEY:
            raise ValueError(f"Environment variables f{self._required_vars} are not set.")
        
    async def convert_to_speech(self , text:str)->bytes:

        if not text.strip():
            raise ValueError("Please provide the text")
        
        if len(text) > 5000:
            raise ValueError("Character length should be less than 5000")
        def _generate() -> bytes:
            audio_generator = self.client.text_to_speech.convert(
                voice_id = Config.ELEVEN_LABS_VOICE_ID, 
                model_id = Config.ELEVEN_LABS_MODEL_ID, 
                text=text, 
                voice_settings = VoiceSettings(
                    stability = 0.5 , 
                    similarity_boost =  0.5
                )
            )
            return b"".join(audio_generator)

        try:
            audio_bytes = await asyncio.to_thread(_generate)
            if not audio_bytes:
                raise Exception("Generated audio is empty")
            return audio_bytes
        except Exception as e:
            raise Exception(f"Text-to-speech: FAILED: {str(e)}") from e
        
if __name__ == "__main__":
    text = "I am a boy."
    audio_bytes = asyncio.run(TTS().convert_to_speech(text=text))
    from src.modules.audio.stt.speech_to_text import STT
    generated_text = asyncio.run(STT().convert_to_text(audio=audio_bytes)).text
    if text.strip().lower().replace(".", '') == generated_text.strip().lower().replace(".", ''):
        print("Sucessfully passed the test")
    else:
        print("Test Failed: Text don't match")


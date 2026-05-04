from pydantic import BaseModel , Field
from config import Config
from groq import Groq
from io import BytesIO
import asyncio
import os


class STT:

    def __init__(self):
        self._required_vars = ["GROQ_API_KEY"]
        self._validate_envs()
        self.client = Groq(api_key=Config.GROQ_API_KEY)

    async def convert_to_text(
        self,
        audio: bytes,
        filename: str = "audio.ogg",
        mime_type: str = "audio/ogg",
    ):

        if not audio:
            raise ValueError(f"Please provide the audio bytes:bytes")
        
        return self.client.audio.transcriptions.create(
            model="whisper-large-v3-turbo", 
            file=(filename, BytesIO(audio), mime_type)
        )
        

    def _validate_envs(self):
        if not Config.GROQ_API_KEY:
            raise ValueError(f"Environment variables f{self._required_vars} are not set.")
    



if __name__ == "__main__":
    with open("src/modules/audio/stt/audio_samples/sample.wav", "rb") as f:
        print(asyncio.run(STT().convert_to_text(audio=f.read())).text)
        f.close()

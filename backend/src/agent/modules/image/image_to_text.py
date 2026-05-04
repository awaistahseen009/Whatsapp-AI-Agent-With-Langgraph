from config import Config
from groq import Groq
import base64
import asyncio


class ITT:
    def __init__(self):
        self._required_vars = ["GROQ_API_KEY"]
        self.validate_vars()
        self.client = Groq(
            api_key=Config.GROQ_API_KEY
        )
    
    def validate_vars(self):
        if not Config.GROQ_API_KEY:
            raise ValueError(f"Environment variables f{self._required_vars} are not set.")

    async def convert_image_to_text(self, image_bytes:bytes, prompt:str = None):

        try:
            if not image_bytes:
                raise ValueError("Image bytes cannot be empty")
            if prompt is None:
                prompt = "Please analyze this image and provide insights in structured format of what you see in the image."

            base64_string = base64.b64encode(image_bytes).decode('utf-8')
            messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_string}"},
                            },
                        ],
                    }
                ]
            
            response = self.client.chat.completions.create(
                model = Config.OCR_MODEL,
                messages=messages,
                max_tokens=1000
            )
            if not response.choices:
                raise Exception("No response received from the vision model")
            
            description = response.choices[0].message.content
            return description
        except Exception as e:
            raise Exception(f"Failed to Analyze the image: {str(e)}") from e
        

if __name__ == "__main__":
    with open("src/modules/image/sample_images/boy.jpeg", "rb") as f:
        result = asyncio.run(ITT().convert_image_to_text(f.read()))
    vars_found = [var for var in ['boy', 'tire', 'sunny'] if var in result]
    if len(vars_found) > 1: 
        print("Image details captured, Model Working")
    else:
        raise Exception("Model isnt working , Image detailed didn't capture")
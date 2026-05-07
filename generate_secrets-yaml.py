import base64
import os
from dotenv import dotenv_values

# 1. Load sensitive keys from .env
env_config = dotenv_values(".env")

# 2. Define the consistent password for the cluster
db_pass = "Ih1ffcf123"

# 3. Define fixed Kubernetes Service-based values
# We use f-strings to inject the password into the URLs
internal_configs = {
    "REDIS_HOST": "redis-service",
    "REDIS_PORT": "6379",
    "CHROMA_HOST": "chroma-service",
    "CHROMA_PORT": "8000",
    "DATABASE_URL": f"postgresql+asyncpg://postgres:{db_pass}@postgresql-service:5432/riley",
    "LANGGRAPH_CHECKPOINT_DB_URL": f"postgresql://postgres:{db_pass}@postgresql-service:5432/riley"
}

# Combine: Internal configs take priority for the cluster environment
final_config = {**env_config, **internal_configs}

def b64(value):
    if value is None:
        return ""
    # Ensure value is a string and handle multi-line strings
    str_val = str(value)
    return base64.b64encode(str_val.encode("utf-8")).decode("utf-8")

# 4. Generate the YAML
yaml_content = f"""apiVersion: v1
kind: Secret
metadata:
  name: riley-secrets
  namespace: riley
type: Opaque
data:
  # LLM
  GROQ_API_KEY: {b64(final_config.get('GROQ_API_KEY'))}
  GROQ_MODEL: {b64(final_config.get('GROQ_MODEL'))}
  ANTHROPIC_API_KEY: {b64(final_config.get('ANTHROPIC_API_KEY'))}
  ANTHROPIC_MODEL: {b64(final_config.get('ANTHROPIC_MODEL'))}
  OPENAI_API_KEY: {b64(final_config.get('OPENAI_API_KEY'))}
  OCR_MODEL: {b64(final_config.get('OCR_MODEL'))}

  # Database
  DATABASE_URL: {b64(final_config.get('DATABASE_URL'))}
  LANGGRAPH_CHECKPOINT_DB_URL: {b64(final_config.get('LANGGRAPH_CHECKPOINT_DB_URL'))}

  # Redis
  REDIS_HOST: {b64(final_config.get('REDIS_HOST'))}
  REDIS_PORT: {b64(final_config.get('REDIS_PORT'))}

  # ChromaDB
  CHROMA_HOST: {b64(final_config.get('CHROMA_HOST'))}
  CHROMA_PORT: {b64(final_config.get('CHROMA_PORT'))}

  # Auth
  JWT_KEY: {b64(final_config.get('JWT_KEY'))}
  JWT_ALGORITHM: {b64(final_config.get('JWT_ALGORITHM'))}

  # WhatsApp
  WHATSAPP_TOKEN: {b64(final_config.get('WHATSAPP_TOKEN'))}
  WHATSAPP_PHONE_ID: {b64(final_config.get('WHATSAPP_PHONE_ID'))}
  WHATSAPP_VERIFY_TOKEN: {b64(final_config.get('WHATSAPP_VERIFY_TOKEN'))}

  # Zoom
  ZOOM_CLIENT_ID: {b64(final_config.get('ZOOM_CLIENT_ID'))}
  ZOOM_CLIENT_SECRET: {b64(final_config.get('ZOOM_CLIENT_SECRET'))}
  ZOOM_ACCOUNT_ID: {b64(final_config.get('ZOOM_ACCOUNT_ID'))}

  # Google Calendar
  GOOGLE_PROJECT_ID: {b64(final_config.get('GOOGLE_PROJECT_ID'))}
  GOOGLE_PRIVATE_KEY_ID: {b64(final_config.get('GOOGLE_PRIVATE_KEY_ID'))}
  GOOGLE_PRIVATE_KEY: {b64(final_config.get('GOOGLE_PRIVATE_KEY'))}
  GOOGLE_CLIENT_EMAIL: {b64(final_config.get('GOOGLE_CLIENT_EMAIL'))}
  GOOGLE_CLIENT_ID: {b64(final_config.get('GOOGLE_CLIENT_ID'))}
  GOOGLE_TOKEN_URI: {b64(final_config.get('GOOGLE_TOKEN_URI'))}
  GOOGLE_CALENDAR_ID: {b64(final_config.get('GOOGLE_CALENDAR_ID'))}
  GOOGLE_CALENDAR_OWNER_EMAIL: {b64(final_config.get('GOOGLE_CALENDAR_OWNER_EMAIL'))}

  # ElevenLabs
  ELEVEN_LABS_API_KEY: {b64(final_config.get('ELEVEN_LABS_API_KEY'))}
  ELEVEN_LABS_MODEL_ID: {b64(final_config.get('ELEVEN_LABS_MODEL_ID'))}
  ELEVEN_LABS_VOICE_ID: {b64(final_config.get('ELEVEN_LABS_VOICE_ID'))}

  # Misc
  AGENT_TIMEZONE: {b64(final_config.get('AGENT_TIMEZONE'))}
  POSTGRES_USER: {b64("postgres")}
  POSTGRES_PASSWORD: {b64(db_pass)}
"""

with open("secrets.yaml", "w") as f:
    f.write(yaml_content)

print("✅ Created secrets.yaml with matched password and internal service URLs.")

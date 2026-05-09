import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession
from src.app.models.user import User
from unittest.mock import patch, AsyncMock
import base64
import io
import asyncio
import os
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from src.agent.graph.graph import build_graph
from config import Config

# ─── Real Module Imports ─────────────────────────────────────────────────────
from src.agent.modules.audio.stt.speech_to_text import STT
from src.agent.modules.audio.tts.text_to_speech import TTS
from src.agent.modules.image.image_to_text import ITT

# Create a mock ChromaDB client for graph tests
class MockChromaClient:
    def heartbeat(self):
        return True
    def get_or_create_collection(self, name, **kwargs):
        return MockChromaCollection()
    def get_collection(self, name, **kwargs):
        return MockChromaCollection()

class MockChromaCollection:
    def add_documents(self, docs):
        pass
    def add(self, **kwargs):
        pass
    def as_retriever(self, **kwargs):
        return MockRetriever()
    def get(self, **kwargs):
        return {"ids": []}
    def delete(self, **kwargs):
        pass
    def query(self, **kwargs):
        return {"ids": [[]], "distances": [[]], "documents": [[]], "metadatas": [[]]}
    def upsert(self, **kwargs):
        pass

class MockRetriever:
    def invoke(self, query):
        return []

def mock_get_chroma_client():
    return MockChromaClient()

def mock_get_collection(name):
    return MockChromaCollection()

# Patch ChromaDB to avoid needing ChromaDB server
# This allows testing real graph with real PostgreSQL + real LLM APIs
CHROMA_CLIENT_PATCH = patch('src.agent.modules.memory.chroma_client._get_chroma_client', mock_get_chroma_client)
CHROMA_COLLECTION_PATCH = patch('src.agent.modules.memory.chroma_client.get_collection', mock_get_collection)
MEMORY_PATCH = patch('src.agent.modules.memory.long_term_client_memory.search_client_memories', return_value=[])
STORE_MEMORY_PATCH = patch('src.agent.modules.memory.long_term_client_memory.store_client_memory')
STORE_CHUNK_PATCH = patch('src.agent.modules.memory.long_term_client_memory.store_client_chunk')

@pytest.mark.asyncio
async def test_audio_speech_to_text():
    """Test audio speech-to-text conversion with real Groq API module"""
    stt = STT()
    
    # Test that STT module is properly initialized with API key
    assert stt.client is not None
    assert Config.GROQ_API_KEY is not None
    
    # Test with empty audio - should raise ValueError
    try:
        await stt.convert_to_text(b"")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Please provide the audio bytes" in str(e)

@pytest.mark.asyncio
async def test_audio_text_to_speech():
    """Test audio text-to-speech conversion with real ElevenLabs module"""
    tts = TTS()
    
    # Test that TTS module is properly initialized with API key
    assert tts.client is not None
    assert Config.ELEVEN_LABS_API_KEY is not None
    
    # Test with empty text - should raise ValueError
    try:
        await tts.convert_to_speech("")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Please provide the text" in str(e)
    
    # Test with text too long
    try:
        await tts.convert_to_speech("x" * 5001)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Character length should be less than 5000" in str(e)


@pytest.mark.asyncio
async def test_image_to_text():
    """Test image-to-text conversion with real Groq API module"""
    itt = ITT()
    
    # Test that ITT module is properly initialized with API key
    assert itt.client is not None
    assert Config.GROQ_API_KEY is not None
    
    # Test with empty image - should raise Exception
    try:
        await itt.convert_image_to_text(b"")
        assert False, "Should have raised Exception"
    except Exception as e:
        assert "Image bytes cannot be empty" in str(e) or "Failed to Analyze the image" in str(e)

# ─── Payload Builders (from existing test files) ───────────────────────────────

def make_text_payload(phone: str, message: str) -> dict:
    return {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": phone,
                        "type": "text",
                        "text": {"body": message}
                    }]
                }
            }]
        }]
    }

async def run_turn(graph, phone: str, payload: dict):
    """Run a single turn with the real agent graph"""
    config = {
        "configurable": {
            "thread_id": phone,
            "phone": phone,
            "incoming_payload": payload,
        }
    }
    result = await graph.ainvoke({}, config=config)
    return result

@pytest.mark.asyncio
async def test_agent_real_graph_response():
    """Test agent response using REAL graph with REAL PostgreSQL + REAL LLM APIs"""
    
    with CHROMA_CLIENT_PATCH, CHROMA_COLLECTION_PATCH, MEMORY_PATCH, STORE_MEMORY_PATCH, STORE_CHUNK_PATCH:
        async with AsyncPostgresSaver.from_conn_string(
            Config.LANGGRAPH_CHECKPOINT_DB_URL
        ) as checkpointer:
            await checkpointer.setup()
            graph = build_graph(checkpointer)
            
            # ── Test 1: Onboarding with REAL LLM response ──
            phone1 = "+1234567890"
            payload1 = make_text_payload(phone1, "Hello, I'm looking for a property")
            result1 = await run_turn(graph, phone1, payload1)
            
            assert result1 is not None
            assert "messages" in result1
            assert len(result1["messages"]) > 0
            
            last_message1 = result1["messages"][-1]
            assert last_message1.content is not None
            assert len(last_message1.content) > 0
            assert "test AI response" not in last_message1.content
            
            # ── Test 2: Property search with REAL LLM response ──
            payload2 = make_text_payload(phone1, "Show me 3 bedroom houses in Miami")
            result2 = await run_turn(graph, phone1, payload2)
            
            assert result2 is not None
            assert "messages" in result2
            
            last_message2 = result2["messages"][-1]
            assert last_message2.content is not None
            assert len(last_message2.content) > 0
            assert "test AI response" not in last_message2.content
            
            # ── Test 3: Multimedia-related query with REAL LLM response ──
            phone2 = "+1234567891"
            payload3 = make_text_payload(phone2, "Can you analyze this property image?")
            result3 = await run_turn(graph, phone2, payload3)
            
            assert result3 is not None
            assert "messages" in result3
            assert len(result3["messages"]) > 0
            last_message3 = result3["messages"][-1]
            assert last_message3.content is not None
            assert len(last_message3.content) > 0
            assert "test AI response" not in last_message3.content
            
            # ── Test 4: Graph with exact pattern from test_agent_complete.py ──
            phone3 = "+15551234567"
            payload4 = make_text_payload(phone3, "Hello, I want to buy a house in Miami")
            
            # Config exactly like test_agent_complete.py
            config = {
                "configurable": {
                    "thread_id": phone3,
                    "incoming_payload": payload4
                }
            }
            
            # Invoke with initial messages list (exact pattern)
            result4 = await graph.ainvoke(
                {"messages": []},
                config=config
            )
            
            assert result4 is not None
            assert "messages" in result4
            assert len(result4["messages"]) > 0
            
            last_message4 = result4["messages"][-1]
            assert last_message4.content is not None
            assert len(last_message4.content) > 0
            assert "test AI response" not in last_message4.content
            
            # Second turn - follow up (same pattern)
            payload5 = make_text_payload(phone3, "My budget is around 600k")
            config5 = {
                "configurable": {
                    "thread_id": phone3,
                    "incoming_payload": payload5
                }
            }
            
            result5 = await graph.ainvoke(
                {"messages": []},
                config=config5
            )
            
            assert result5 is not None
            assert "messages" in result5
            assert len(result5["messages"]) > 0
            
            last_message5 = result5["messages"][-1]
            assert last_message5.content is not None
            assert len(last_message5.content) > 0
            assert "test AI response" not in last_message5.content


@pytest.mark.asyncio
async def test_stt_real_audio_conversion():
    """Test STT with REAL sample.wav - calls actual Groq API like module's __main__"""
    stt = STT()
    
    # Use the actual sample file from the module
    sample_path = "src/agent/modules/audio/stt/audio_samples/sample.wav"
    
    with open(sample_path, "rb") as f:
        audio_bytes = f.read()
    
    assert len(audio_bytes) > 0, "Sample WAV file is empty"
    
    # Actually call the STT function with real audio - same as module's __main__
    # This calls the REAL Groq Whisper API
    result = await stt.convert_to_text(audio=audio_bytes)
    
    # Verify we got a real transcription
    assert result is not None
    assert hasattr(result, 'text')
    assert isinstance(result.text, str)
    assert len(result.text) > 0, "STT should return transcribed text"


@pytest.mark.asyncio
async def test_itt_real_image_conversion():
    """Test ITT with REAL boy.jpeg - calls actual Groq API like module's __main__"""
    itt = ITT()
    
    # Use the actual sample file from the module
    sample_path = "src/agent/modules/image/sample_images/boy.jpeg"
    
    with open(sample_path, "rb") as f:
        image_bytes = f.read()
    
    assert len(image_bytes) > 0, "Sample JPEG file is empty"
    
    # Actually call the ITT function with real image - same as module's __main__
    # This calls the REAL Groq Vision API
    result = await itt.convert_image_to_text(image_bytes=image_bytes)
    
    # Verify we got a real description
    assert result is not None
    assert isinstance(result, str)
    assert len(result) > 0, "ITT should return image description"
    
    # Similar validation to module's __main__ - check for meaningful content
    # Module checks for: boy, tire, sunny
    vars_found = [var for var in ['boy', 'person', 'child', 'sitting', 'outside'] if var in result.lower()]
    assert len(vars_found) > 0, f"Image analysis should detect content, got: {result[:100]}..."


@pytest.mark.asyncio
async def test_tts_real_text_to_speech():
    """Test TTS with real text - calls actual ElevenLabs API like module's __main__"""
    tts = TTS()
    
    # Use the same text as the module's __main__
    text = "I am a boy."
    
    # Actually call the TTS function with real text - same as module's __main__
    # This calls the REAL ElevenLabs API
    audio_bytes = await tts.convert_to_speech(text=text)
    
    # Verify we got real audio bytes
    assert audio_bytes is not None
    assert isinstance(audio_bytes, bytes)
    assert len(audio_bytes) > 0, "TTS should return audio bytes"
    
    # The module's __main__ validates by doing STT on the generated audio
    # and checking if it matches the original text
    stt = STT()
    stt_result = await stt.convert_to_text(audio=audio_bytes)
    generated_text = stt_result.text
    
    # Compare like the module's __main__ does
    original = text.strip().lower().replace(".", "")
    transcribed = generated_text.strip().lower().replace(".", "")
    assert original == transcribed, f"TTS->STT roundtrip failed: '{original}' != '{transcribed}'"


@pytest.mark.asyncio
async def test_stt_tts_modules_integration():
    """Test that STT and TTS modules are properly integrated"""
    
    # Verify modules can be imported and instantiated
    stt = STT()
    tts = TTS()
    
    # Verify they have the required attributes
    assert hasattr(stt, 'client')
    assert hasattr(stt, 'convert_to_text')
    assert hasattr(tts, 'client')
    assert hasattr(tts, 'convert_to_speech')
    
    # Verify API keys are configured
    assert Config.GROQ_API_KEY is not None and len(Config.GROQ_API_KEY) > 0
    assert Config.ELEVEN_LABS_API_KEY is not None and len(Config.ELEVEN_LABS_API_KEY) > 0

@pytest.mark.asyncio
async def test_itt_module_integration():
    """Test that ITT module is properly integrated"""
    
    itt = ITT()
    
    # Verify module has required attributes
    assert hasattr(itt, 'client')
    assert hasattr(itt, 'convert_image_to_text')
    
    # Verify API key is configured
    assert Config.GROQ_API_KEY is not None and len(Config.GROQ_API_KEY) > 0
    assert Config.OCR_MODEL is not None

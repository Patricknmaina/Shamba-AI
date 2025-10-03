"""
ShambaAI FastAPI ML Service
"""

import os
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from .retrieval import RetrievalService
from .llm_openai import generate_answer
from .translate_simple import SimpleTranslationService
from .utils import prepare_rag_context, build_rag_prompt, format_sources
from .insights_generator import InsightsGenerator
from .crops import Crop, get_supported_crops

# Load environment variables
load_dotenv()

# Configuration
ML_API_KEY = os.getenv('ML_API_KEY', 'supersecretapexkey')
DATA_DIR = os.getenv('DATA_DIR', './data')

# Initialize services
app = FastAPI(
    title="ShambaAI ML Service",
    description="RAG-powered agricultural advisory API with multilingual support",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev server
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
        "https://shamba-ai.netlify.app",  # Production frontend (fixed: no trailing slash)
        "https://*.netlify.app",  # Allow all Netlify subdomains
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Global service instances (lazy loaded)
retrieval_service: Optional[RetrievalService] = None
translation_service: Optional[SimpleTranslationService] = None
insights_generator: Optional[InsightsGenerator] = None


def get_retrieval_service() -> RetrievalService:
    """Get or initialize retrieval service."""
    global retrieval_service
    if retrieval_service is None:
        retrieval_service = RetrievalService(DATA_DIR)
    return retrieval_service


def get_translation_service() -> SimpleTranslationService:
    """Get or initialize translation service."""
    global translation_service
    if translation_service is None:
        translation_service = SimpleTranslationService()
    return translation_service


def get_insights_generator() -> InsightsGenerator:
    """Get or initialize insights generator."""
    global insights_generator
    if insights_generator is None:
        insights_generator = InsightsGenerator()
    return insights_generator


# Security dependency
def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key from header."""
    if x_api_key != ML_API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


# Request/Response models
class AskRequest(BaseModel):
    question: str = Field(..., description="User's question")
    lang: str = Field(default="en", description="Language code (en, sw, fr, etc.)")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of sources to retrieve")


class Source(BaseModel):
    title: str
    snippet: str
    url: Optional[str] = ""


class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
    latency_ms: int


class InsightsRequest(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)
    crop: Crop = Field(..., description="Crop type (select from supported list)")
    lang: str = Field(default="en")


class InsightsResponse(BaseModel):
    forecast: Dict[str, Any]
    soil: Dict[str, Any]
    tips: List[str]


class CropListResponse(BaseModel):
    crops: List[str]


class IndexDocRequest(BaseModel):
    title: str
    text_md: str
    lang: Optional[str] = "en"
    country: Optional[str] = "Kenya"


class IndexDocResponse(BaseModel):
    message: str
    doc_id: Optional[int] = None


# Health check endpoint (no auth required)
@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "ShambaAI ML Service",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check."""
    try:
        retrieval = get_retrieval_service()
        stats = retrieval.get_stats()
        translation = get_translation_service()

        return {
            "status": "healthy",
            "index_loaded": True,
            "num_documents": stats['num_documents'],
            "num_chunks": stats['num_chunks'],
            "translation_available": translation.is_available()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# Main RAG endpoint
@app.post("/ask", response_model=AskResponse, dependencies=[Depends(verify_api_key)])
async def ask(request: AskRequest):
    """
    Answer questions using RAG with multilingual support.

    Process:
    1. Translate question to English if needed
    2. Retrieve relevant chunks from FAISS index
    3. Generate answer using Claude
    4. Translate answer back to user's language
    """
    start_time = time.time()

    try:
        print(f"[DEBUG] Starting /ask request: question='{request.question[:50]}...', lang={request.lang}")

        print("[DEBUG] Step 1: Initializing services...")
        retrieval = get_retrieval_service()
        translation = get_translation_service()
        print("[DEBUG] Services initialized")

        # Step 1: Translate question to English if needed
        question_en = request.question
        if request.lang != 'en' and translation.is_available():
            print(f"[DEBUG] Translating question from {request.lang} to English")
            question_en = translation.translate_to_english(request.question, source_lang=request.lang)
            print(f"[DEBUG] Translated to: {question_en[:50]}...")

        # Step 2: Retrieve relevant chunks
        print(f"[DEBUG] Step 2: Retrieving top {request.top_k} chunks for: {question_en[:100]}")
        chunks = retrieval.retrieve(question_en, top_k=request.top_k)
        print(f"[DEBUG] Retrieved {len(chunks)} chunks")

        if not chunks:
            raise HTTPException(status_code=404, detail="No relevant information found")

        # Step 3: Build context and generate answer
        print("[DEBUG] Step 3: Building context and prompt...")
        context = prepare_rag_context(chunks)
        prompt = build_rag_prompt(question_en, context)
        print(f"[DEBUG] Prompt length: {len(prompt)} chars")

        print("[DEBUG] Step 4: Generating answer with OpenAI GPT-4o-mini...")
        answer_en = generate_answer(prompt)
        print(f"[DEBUG] Answer generated: {len(answer_en)} chars")

        # Step 4: Translate answer back to user's language
        answer = answer_en
        if request.lang != 'en' and translation.is_available():
            print(f"[DEBUG] Step 5: Translating answer to {request.lang}")
            answer = translation.translate_text(answer_en, target_lang=request.lang)
            print(f"[DEBUG] Translation complete")

        # Format sources
        print("[DEBUG] Step 6: Formatting sources...")
        sources = format_sources(chunks)
        print(f"[DEBUG] Formatted {len(sources)} sources")

        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        print(f"[DEBUG] Request complete in {latency_ms}ms")

        return AskResponse(
            answer=answer,
            sources=[Source(**s) for s in sources],
            latency_ms=latency_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in /ask endpoint: {e}")
        print(f"Full traceback:\n{error_details}")
        raise HTTPException(status_code=500, detail=f"{str(e)}\n\nCheck server logs for full traceback.")


@app.get("/insights", response_model=InsightsResponse, dependencies=[Depends(verify_api_key)])
async def get_insights(
    lat: float,
    lon: float,
    crop: Crop,
    lang: str = "en",
    use_ml_forecast: bool = False
):
    """
    Get agricultural insights for location and crop using ML models.

    Uses:
    - Prophet ML model for rainfall forecasting (if use_ml_forecast=True)
    - Open-Meteo API for weather data
    - Spatial soil database for soil characteristics

    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        crop: Crop type selected from supported list
        lang: Language code (default: en)
        use_ml_forecast: Use Prophet ML forecast (slower but more detailed)
    """
    try:
        print(f"[DEBUG] /insights request: lat={lat}, lon={lon}, crop={crop}, lang={lang}, use_ml={use_ml_forecast}")

        translation = get_translation_service()
        insights_gen = get_insights_generator()

        # Generate insights using ML models
        print("[DEBUG] Generating ML-based insights...")
        crop_value = crop.value if isinstance(crop, Crop) else crop

        try:
            insights = insights_gen.generate_insights(
                lat=lat,
                lon=lon,
                crop=crop_value,
                use_full_forecast=use_ml_forecast
            )
        except ValueError as err:
            raise HTTPException(status_code=400, detail=str(err))

        # Extract forecast and soil data
        forecast = insights['forecast']
        soil = insights['soil']
        tips_en = insights['tips']

        print(f"[DEBUG] Generated {len(tips_en)} tips")

        # Translate tips if needed
        tips = tips_en
        if lang != 'en' and translation.is_available():
            print(f"[DEBUG] Translating tips to {lang}")
            tips = [translation.translate_text(tip, target_lang=lang) for tip in tips_en]

        return InsightsResponse(
            forecast=forecast,
            soil=soil,
            tips=tips
        )

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in /insights endpoint: {e}")
        print(f"Full traceback:\n{error_details}")
        raise HTTPException(status_code=500, detail=f"{str(e)}\n\nCheck server logs for details.")


@app.get("/crops", response_model=CropListResponse)
async def list_crops():
    """Return the list of crops supported by the insights endpoint."""
    return CropListResponse(crops=get_supported_crops())


@app.post("/index_doc", response_model=IndexDocResponse, dependencies=[Depends(verify_api_key)])
async def index_document(request: IndexDocRequest):
    """
    Index a new document (admin only).

    For MVP, this is a placeholder. In production, implement full indexing pipeline.
    """
    # TODO: Implement document indexing
    # 1. Save document to corpus
    # 2. Chunk document
    # 3. Generate embeddings
    # 4. Add to FAISS index
    # 5. Update metadata

    return IndexDocResponse(
        message="Document indexing not yet implemented. Use build_index.py script to rebuild index.",
        doc_id=None
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('ML_PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

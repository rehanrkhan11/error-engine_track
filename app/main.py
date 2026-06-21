import time
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.models import PipelineResponse, InputType
from app.pipeline import run_pipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting Error Engine in [{settings.app_env}] mode")
    logger.info(f"✅ Google API Key loaded: {'*' * 8}{settings.google_api_key[-4:]}")
    logger.info(f"✅ Groq API Key loaded:   {'*' * 8}{settings.groq_api_key[-4:]}")
    yield
    logger.info("🛑 Shutting down Error Engine")


app = FastAPI(
    title="Multi-Agent Error Diagnosis & Execution Engine",
    description="5-agent pipeline for diagnosing and fixing code errors",
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.app_env, "version": "0.2.0"}


@app.post("/api/diagnose", response_model=PipelineResponse)
async def diagnose(
    code_or_error: str = Form(...),
    language: str = Form(default="unknown"),
    image: UploadFile | None = File(default=None),
):
    """
    Main pipeline endpoint. Accepts:
    - code_or_error : the raw error text or code (always required)
    - language      : optional programming language hint
    - image         : optional screenshot (multipart upload)
    """
    image_bytes: bytes | None = None
    input_type = InputType.TEXT

    # Swagger sends image="" (empty string) when no file is chosen — treat as None
    if image is not None and image.filename == "":
        image = None

    if image is not None:
        if not image.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded file must be an image, got: {image.content_type}",
            )
        image_bytes = await image.read()
        input_type = InputType.BOTH if code_or_error else InputType.IMAGE
        logger.info(f"📸 Image received: {image.filename} ({len(image_bytes)} bytes)")

    logger.info(f"📥 Request | type={input_type} | lang={language}")

    try:
        result = await run_pipeline(
            code_or_error=code_or_error,
            language=language,
            image_bytes=image_bytes,
        )
        return result

    except Exception as e:
        logger.error(f"💥 Pipeline failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

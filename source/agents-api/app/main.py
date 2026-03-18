from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import chat_routes
from .routes import feedback_routes
from .utils.logger import logger
from dotenv import load_dotenv

load_dotenv()

# Initialize telemetry (LangSmith tracing) at startup
# This sets LANGCHAIN_TRACING_V2=true and configures the project
from .utils import telemetry  # noqa: F401

logger.info("Telemetry initialized — LangSmith project: IT-Incident-Assistant")

app = FastAPI(title="AI Incident Knowledge Base Assistant")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_routes.router, prefix="/api/v1")
app.include_router(feedback_routes.router, prefix="/api/v1/agents")

@app.get("/")
async def root():
    return {"message": "AI Incident Assistant API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)

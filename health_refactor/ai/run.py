"""Run the product dashboard AI service locally."""
import uvicorn

from ai.src.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "ai.src.main:app",
        host="0.0.0.0",
        port=settings.app_port,
        reload=settings.app_env == "development",
    )

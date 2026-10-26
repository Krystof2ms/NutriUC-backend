from app.core.config import settings
from app.core.logger import logger

SUPPORTED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}
RECIPES_DIR = settings.RESOURCES_DIR / "recipes"

if not RECIPES_DIR.exists():
    logger.warning("Create resources recipes dir")
    RECIPES_DIR.mkdir(parents=True, exist_ok=True)

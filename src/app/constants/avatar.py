from app.core.config import settings
from app.core.logger import logger

MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB
AVATAR_SIZE = 512
AVATAR_DIR = settings.RESOURCES_DIR / "avatars"
if not AVATAR_DIR.exists():
    logger.warning("Create resources avatars dir")
    AVATAR_DIR.mkdir(parents=True, exist_ok=True)

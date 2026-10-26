from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from app.constants.avatar import AVATAR_DIR
from app.core.config import TraceLayer, settings
from app.core.decorator import trace
from app.core.events.manager import event_manager
from app.core.logger import logger
from app.core.queue.avatar import AvatarJobQueue
from app.events import UserAvatarChanged
from app.events.user import UserAvatarRejected
from app.jobs import ProcessUserAvatar
from app.jobs.user import Crop
from app.repositories import UserRepo, db_connection

AVATAR_SIZE = 512
MIN_DIMENSION = 128
MAX_DIMENSION = 4096


@dataclass(frozen=True)
class ImageInfo:
    width: int
    height: int


def process_avatar(
    source_path: Path,
    output_path: Path,
    crop: Crop,
) -> None:
    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image)

        width, height = image.size

        left = int(crop.x * width)
        top = int(crop.y * height)
        size = int(crop.size * min(width, height))

        right = left + size
        bottom = top + size

        image = image.crop((left, top, right, bottom))

        image = image.resize(
            (AVATAR_SIZE, AVATAR_SIZE),
            Image.Resampling.LANCZOS,
        )

        if image.mode not in ("RGB", "RGBA"):
            image = image.convert("RGBA")

        image.save(
            output_path,
            format="WEBP",
            quality=85,
            method=6,
        )


def validate_image(file) -> ImageInfo:
    try:
        image = Image.open(file)

        if image.format not in {"JPEG", "PNG", "WEBP"}:
            raise ValueError("Unsupported image format")

        width, height = image.size

        return ImageInfo(
            width=width,
            height=height,
        )

    except UnidentifiedImageError, OSError:
        raise ValueError("Invalid image")


def validate_crop(crop: Crop, width: int, height: int) -> None:
    if crop.size <= 0:
        raise ValueError("Invalid crop size")

    if crop.x < 0 or crop.y < 0:
        raise ValueError("Invalid crop position")

    if crop.size > min(width, height):
        raise ValueError("Crop is larger than image")

    if crop.x + crop.size > width:
        raise ValueError("Crop exceeds image width")

    if crop.y + crop.size > height:
        raise ValueError("Crop exceeds image height")


class AvatarWorker:
    def __init__(self, queue: AvatarJobQueue) -> None:
        self.queue = queue

    async def run(self) -> None:
        while True:
            job = await self.queue.dequeue()

            try:
                await self.process(job)
            finally:
                self.queue.task_done()

    @trace(TraceLayer.WORKER)
    async def process(self, job: ProcessUserAvatar) -> None:
        try:
            with job.data.source_path.open("rb") as file:
                image_info = validate_image(file)

            validate_crop(
                job.data.crop,
                width=image_info.width,
                height=image_info.height,
            )

            new_avatar_key = f"{job.data.user_id}_{uuid4()}"

            output_path = AVATAR_DIR / f"{new_avatar_key}.webp"

            process_avatar(
                job.data.source_path,
                output_path,
                job.data.crop,
            )

            async with db_connection() as conn:
                print("write connection")
                old_avatar_key = await UserRepo.updateAvatar(
                    conn,  # pyright: ignore[reportArgumentType]
                    job.data.user_id,
                    new_avatar_key,
                )

                if old_avatar_key:
                    old_path = AVATAR_DIR / f"{old_avatar_key}.webp"

                    if old_path.exists():
                        old_path.unlink()

            event = UserAvatarChanged.new()
            await event_manager.publish(job.data.user_id, event)

        except Image.DecompressionBombError:
            event = UserAvatarRejected.new("Image dimensions are too large")
            await event_manager.publish(job.data.user_id, event)

        except Exception as e:  # noqa: BLE001
            event = UserAvatarRejected.new("Image rejected")
            await event_manager.publish(job.data.user_id, event)

            if TraceLayer.WORKER in settings.TRACE_LAYERS:
                logger.error(e)
        finally:
            job.data.source_path.unlink(missing_ok=True)

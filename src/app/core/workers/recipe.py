from uuid import uuid4

from PIL import Image, ImageOps, UnidentifiedImageError

from app.constants.recipe import RECIPES_DIR
from app.core.config import TraceLayer
from app.core.decorator import trace
from app.core.events.manager import event_manager
from app.core.logger import logger
from app.core.queue.recipe import RecipeJobQueue
from app.events.recipe import RecipeImageChanged, RecipeImageRejected
from app.jobs.recipe import ProcessRecipeImage
from app.repositories import db_connection
from app.repositories.errorrs import RepositoryError
from app.repositories.recipe import RecipeRepo

OUTPUT_IMAGE_FORMAT = "WEBP"
OUTPUT_IMAGE_EXTENSION = ".webp"
IMAGE_SIZE = (800, 800)


class RecipeWorker:
    def __init__(self, queue: RecipeJobQueue) -> None:
        self.queue = queue

    async def run(self) -> None:
        while True:
            job = await self.queue.dequeue()

            try:
                await self.process(job)
            finally:
                self.queue.task_done()

    @trace(TraceLayer.WORKER)
    async def process(self, job: ProcessRecipeImage) -> None:
        source_path = job.data.source_path
        user_id = job.data.user_id
        recipe_id = job.data.recipe_id

        try:
            with Image.open(source_path) as image:
                image.verify()

            with Image.open(source_path) as image:
                image = image.convert("RGB")

                image = ImageOps.fit(
                    image,
                    IMAGE_SIZE,
                    method=Image.Resampling.LANCZOS,
                )
                new_image_key = f"{user_id}_{recipe_id}_{uuid4()}"

                output_path = RECIPES_DIR / f"{new_image_key}{OUTPUT_IMAGE_EXTENSION}"

                image.save(
                    output_path,
                    format=OUTPUT_IMAGE_FORMAT,
                )

            try:
                source_path.unlink(missing_ok=True)
            except OSError:
                logger.exception(
                    "Failed to delete recipe_img file: %s",
                    source_path,
                )

            async with db_connection() as conn:
                try:
                    await RecipeRepo.updateImage(conn, recipe_id, user_id, new_image_key)  # pyright: ignore[reportArgumentType]
                except RepositoryError:
                    logger.exception(
                        "Failed to update recipe image_key: %s",
                        source_path,
                    )

            await event_manager.publish(
                user_id,
                RecipeImageChanged.new(),
            )

        except UnidentifiedImageError:
            await event_manager.publish(
                user_id,
                RecipeImageRejected.new("Invalid image file"),
            )

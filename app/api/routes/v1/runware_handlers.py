import logging
from fastapi import APIRouter, HTTPException, status, Request, Header
from api.services.runware_manager import RunwareManager


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    path='/generate_images',
    status_code=status.HTTP_202_ACCEPTED,
)
async def image_generation(
        promts_for_images: list[str],
):
    try:
        runware_manager = RunwareManager()
        result = []
        for promt in promts_for_images:
            image = await runware_manager.generate_image(positive_prompt=promt)
            result.append(image)
            logger.info(f"Generated image: {image}")

        return result

    except Exception as e:
        logger.exception(f'Unexpected error: {str(e)}', exc_info=True)
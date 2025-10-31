from runware import Runware, IImageInference
from settings.settings import settings


class RunwareManager:
    def __init__(
            self,
            max_retries=3,
            positive_prompt='photos about job: ',
            model='runware:101@1',
    ):
        self.client = Runware(api_key=settings.runware_api_key.get_secret_value())
        self.max_retries = max_retries
        self.positive_prompt = positive_prompt
        self.model = model


    async def startup(self) -> None:
        await self.client.connect()


    async def generate_image(
        self,
        positive_prompt: str,
        height: int = 768,
        width: int = 512,
    ) -> str:
        request_image = IImageInference(
            outputFormat='JPG',
            outputType='URL',
            positivePrompt=self.positive_prompt + positive_prompt,
            height=height,
            width=width,
            model=self.model,
            scheduler='DPM++ 3M Karras',
            checkNsfw=False,
            steps=90,
            CFGScale=10.0,
            clipSkip=0,
            numberResults=1,
        )
        images = await self.client.imageInference(requestImage=request_image)
        return images[0].imageURL  # 1 картинка из-за numberResults

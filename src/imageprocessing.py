import os
from pickletools import optimize
import httpx
import PIL
from PIL import Image

class ProcessImage:
    def __init__(self, path, name, artist, album):
        self.path = path
        self.name = name
        self.artist = artist
        self.album = album
    async def img_path(self):
        excluded_extensions = {".flac", ".mp3", ".ogg", ".alac", ".lrc"}
        valid_filenames = {"cover.jpg", "cover.jpeg", "cover.png", "Cover.jpg", "Cover.jpeg", "Cover.png"}
        for entry in os.scandir(self.path):
            if entry.is_file() and not entry.name.lower().endswith(tuple(excluded_extensions)):
                if entry.name.lower() in valid_filenames:
                    image_path = os.path.join(self.path, entry.name)
                    await self.compress_image(image_path)
                    if os.path.getsize(f'{os.getcwd()}/tmp/{self.name}/cover.jpg') < 1 * 1024 * 1024:  # 1MB:
                        return True
                    else:
                        os.remove(f'{os.getcwd()}/tmp/{self.name}/cover.jpg')
                        async with httpx.AsyncClient() as client:
                            deez_res = await client.get(f'https://api.deezer.com/search?q=artist:"{self.artist.lower()}" album:"{self.album.lower()}"')
                            if deez_res.status_code == 200:
                                data = deez_res.json()
                                if data.get("data") and len(data["data"]) > 0:
                                    cover_url = data['data'][0]['album']['cover_xl']
                                    cover = await client.get(cover_url)
                                    with open(f'{os.getcwd()}/tmp/{self.name}/cover.jpg', 'wb') as cover_image:
                                        cover_image.write(cover.content)
                                    return True
                            else:
                                return False
        return False

    async def compress_image(self, image):
        # open the image
        with  Image.open(image) as my_image:
            # the original width and height of the image
            image_height = my_image.height
            image_width = my_image.width

            # print("The original size of Image is: ", round(len(my_image.fp.read())/1024,2), "KB")

            # compressed the image
            my_image = my_image.resize((image_width, image_height), PIL.Image.LANCZOS)

            # save the image
            my_image.save(f'{os.getcwd()}/tmp/{self.name}/cover.jpg')

            # open the compressed image
            # with Image.open(f'{os.getcwd()}/tmp/cover.jpg') as compresed_image:
            #     print("The size of compressed image is: ", round(len(compresed_image.fp.read())/1024,2), "KB")


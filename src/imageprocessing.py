import os
import re
import PIL
import httpx
from PIL import Image


class ProcessImage:
    def __init__(self, path, name, artist, album):
        # Sanitize the path to remove invalid characters or quotes
        self.path = self.sanitize_path(path)
        self.name = name
        self.artist = artist
        self.album = album

    @staticmethod
    def sanitize_path(path: str) -> str:
        """Clean up path without destroying valid Windows separators."""
        # Strip surrounding quotes and spaces
        path = path.strip().strip('"').strip("'")

        # Normalize path (convert relative .\ and / to absolute form)
        path = os.path.normpath(path)

        # Windows paths cannot contain <>:"|?* — but keep \ and /
        invalid_chars = r'[<>:"|?*]'
        path = re.sub(invalid_chars, "", path)

        return path

    async def img_path(self, tracker_dir):
        """Searches for a cover image on the original directory.
        Compresses image if image is too large, fallbacks to Deezer API for image cover.
        """
        excluded_extensions = {".flac", ".mp3", ".ogg", ".alac", ".lrc", ".txt"}
        valid_filenames = {
            "cover.jpg",
            "cover.jpeg",
            "cover.png",
            "Cover.jpg",
            "Cover.jpeg",
            "Cover.png",
        }

        print(f"Scanning for cover in: {repr(self.path)}")  # Debug line

        # Ensure directory exists before scanning
        if not os.path.exists(self.path):
            raise FileNotFoundError(f"Path does not exist: {self.path}")

        for entry in os.scandir(self.path):
            if entry.is_file() and not entry.name.lower().endswith(
                tuple(excluded_extensions)
            ):
                if entry.name.lower() in valid_filenames:
                    image_path = os.path.join(self.path, entry.name)
                    await self.compress_image(image_path, tracker_dir)

                    output_path = os.path.join(
                        os.getcwd(), "tmp", tracker_dir, self.name, "cover.jpg"
                    )
                    if os.path.getsize(output_path) < 1 * 1024 * 1024:  # 1 MB
                        return True
                    else:
                        os.remove(output_path)
                        async with httpx.AsyncClient() as client:
                            deez_res = await client.get(
                                f'https://api.deezer.com/search?q=artist:"{self.artist.lower()}" album:"{self.album.lower()}"'
                            )
                            if deez_res.status_code == 200:
                                data = deez_res.json()
                                if data.get("data"):
                                    cover_url = data["data"][0]["album"]["cover_xl"]
                                    cover = await client.get(cover_url)
                                    os.makedirs(
                                        os.path.dirname(output_path), exist_ok=True
                                    )
                                    with open(output_path, "wb") as cover_image:
                                        cover_image.write(cover.content)
                                    return True
                            return False
        return False

    async def compress_image(self, image, tracker_dir):
        """Compresses cover image and writes a new one to tmp directory."""
        output_path = os.path.join(
            os.getcwd(), "tmp", tracker_dir, self.name, "cover.jpg"
        )
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with Image.open(image) as my_image:
            my_image = my_image.resize(
                (my_image.width, my_image.height),
                PIL.Image.LANCZOS,  # type: ignore
            )
            my_image.save(output_path)

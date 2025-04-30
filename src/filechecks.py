import asyncio
from pathlib import Path
import httpx
from config import config as default


class FilesChecks:
    def __init__(self, name, config):
        self.name = name
        self.config = config

    async def check_tmp_directory(self, tracker_dir):
        """Verify if .torrent exists in tmp directory (handles tmp directory creation)."""
        tmp = Path.cwd() / f'tmp'
        tmp.mkdir(parents=True, exist_ok=True)
        excluded_extensions = {'.jpg', '.jpeg', '.png', '.lrc', '.cue', ".txt"}
        tmp_dir = Path.cwd() / f"tmp/{tracker_dir}/{self.name}"
        files = [entry.name for entry in tmp_dir.iterdir() if
                 entry.is_file() and not entry.suffix.lower() in excluded_extensions]
        if f'{self.name}.torrent' in files:
            return True
        return False

    async def parse_dupes(self, search_name, tracker):
        """Searches for duplicates on given tracker"""
        # TODO deal with the time cache takes to reflect the newly crated posts.
        # BUG sometimes cache takes time to refresh so tracker will keep saying
        # there's a duplicate on the site when in reality there none.
        params = {
            'api_token': default.tracker_tokens[tracker].api_token,
            'name': search_name
        }
        await asyncio.sleep(5)
        async with httpx.AsyncClient() as client:
            response = await client.get(self.config.filter_api, params=params)
        # response = requests.get(self.config.filter_api, params=params)
        if response.status_code == 200:
            data = response.json()
            results = [each['attributes']['name'] for each in data.get("data", [])]
            if results:
                return results
            else:
                return False
        return ["Error Data"]

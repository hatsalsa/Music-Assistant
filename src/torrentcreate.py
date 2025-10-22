import os
import platform
import re
import time
import traceback
from datetime import datetime

import cli_ui
import httpx
import requests
from bs4 import BeautifulSoup
from torf import Torrent as makeTorrent

from config import config as default
from src.console import console as logger
from src.imageprocessing import ProcessImage


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


class Torrent:
    def __init__(self, path, config, name, artist, album):
        self.path = path
        self.config = config
        self.name = name
        self.artist = artist
        self.album = album

    async def create(self, tracker):
        """Creates a .torrent file"""
        start_time = time.time()

        # ✅ Sanitize the directory path before using it
        clean_path = sanitize_path(self.path)

        torrent = makeTorrent(
            path=clean_path,
            trackers=default.tracker_tokens[tracker].announce,
            creation_date=datetime.now(),
            piece_size=4194304,
            private=True,
            source=self.config.source,
            created_by="Music assistant",
            comment="Created with Music Assistant",
        )

        torrent.generate(callback=torf_cb, interval=5)
        torrent.write(
            f"{os.getcwd()}/tmp/{tracker}/{self.name}/{self.name}.torrent",
            overwrite=True,
        )
        torrent.verify_filesize(clean_path)

        finish_time = time.time()
        logger.print(f"torrent created in {finish_time - start_time:.4f} seconds")

        final_file_path = f"{os.getcwd()}/tmp/{tracker}/{self.name}/{self.name}.torrent"
        return final_file_path

    async def upload_torrent(self, tracker):
        """POST action to tracker using API (Uploads .torrent, Creates/Updates tracker post)"""
        torrent_bin = open(
            f"{os.getcwd()}/tmp/{tracker}/{self.name}/{self.name}.torrent", "rb"
        )
        desc = open(
            f"{os.getcwd()}/tmp/{tracker}/{self.name}/DESCRIPTION.txt",
            "r",
            encoding="utf-8",
        ).read()
        files = {"torrent": torrent_bin}
        data = {
            "name": self.name,
            "description": desc,
            "category_id": self.config.category_id,
            "type_id": self.config.type_id,
            "anonymous": 1 if default.tracker_tokens[tracker].anon else 0,
            "personal_release": 1 if default.tracker_tokens[tracker].personal_release else 0,
            "internal": 0,
            "featured": 0,
            "free": 0,
            "doubleup": 0,
            "sticky": 0,
        }
        params = {"api_token": default.tracker_tokens[tracker].api_token}
        headers = {
            "User-Agent": f"Music Assistant/2.2 ({platform.system()} {platform.release()})"
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.upload_api,
                    files=files,
                    data=data,
                    headers=headers,
                    params=params,
                )
                res_json = response.json()
                if res_json.get("success") is True:
                    match = re.search(r"/download/([^.]*)", res_json["data"])
                    if match:
                        torrent_id = match.group(1)
                    torrent_bin.close()
                    logger.print(f"[yellow] Torrent URL: {res_json['data']}")
                    logger.print(f"[yellow] Created torrent with ID: {torrent_id}")
                    patched = await self.patch_torrent(torrent_id, desc, tracker)
                    if not patched:
                        logger.print("Unable to patch torrent, check the site.")
                    else:
                        logger.print("Torrent published and automatically patched.")
                else:
                    raise ValueError(res_json)
        except ValueError as e:
            tb_str = traceback.format_exc()
            logger.print(f"There was an issue: {tb_str}")
            logger.print(f"[bold red] API Response: {e} [/bold red]")

    async def patch_torrent(self, torrent_id, desc, tracker):
        """Automatically updates the cover/banner image of the published torrent."""
        _image = await ProcessImage(
            self.path, name=self.name, artist=self.artist, album=self.album
        ).img_path(tracker)
        if not _image:
            logger.print(
                "[bold orange] Make sure theres a Cover.jpg|Cover.png|Cover.jpeg on the directory"
            )
            return False
        else:
            _csrf_token = await self.parse_csrf_token(torrent_id, tracker)
            files = {
                "torrent-cover": (
                    "cover.jpg",
                    open(f"{os.getcwd()}/tmp/{tracker}/{self.name}/cover.jpg", "rb"),
                    "image/jpeg",
                ),
                "torrent-banner": (
                    "cover.jpg",
                    open(f"{os.getcwd()}/tmp/{tracker}/{self.name}/cover.jpg", "rb"),
                    "image/jpeg",
                ),
            }
            headers = {
                "User-Agent": f"Music Assistant/2.2 ({platform.system()} {platform.release()})"
            }
            cookies = {
                "laravel_cookie_consent": "1",
                "XSRF-TOKEN": default.tracker_tokens[tracker].XSRF_TOKEN,
                "laravel_session": default.tracker_tokens[tracker].session_token,
            }
            data = {
                "_token": _csrf_token,
                "_method": "PATCH",
                "name": str(self.name),
                "category_id": str(self.config.category_id),
                "type_id": str(self.config.type_id),
                "tmdb_movie_id": "0",
                "tmdb_tv_id": "0",
                "imdb": "0",
                "tvdb": "0",
                "mal": "0",
                "igdb": "0",
                "internal": "0",
                "description": desc,
                "personal_release": "1" if default.tracker_tokens[tracker].personal_release else "0",
            }
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        f"{self.config.torrents_url}/{torrent_id}",
                        files=files,
                        data=data,
                        headers=headers,
                        cookies=cookies,
                    )
                    if response.status_code == 413:
                        # TODO fallback to deezer api or local-default image
                        # logger.print(f" Artists : {self.artist.lower()}, Album {self.album.lower()}")
                        logger.print(
                            "Cover image size is too large. Cover not uploaded"
                        )
                return True
            except BaseException as e:
                logger.print(f"[bold red] Critical Error {e} [/bold red]")
                return None

    async def parse_csrf_token(self, torrent_id, tracker):
        """Parse CSRF token from web (Required to update post)"""
        cookies = {
            "laravel_cookie_consent": "1",
            "XSRF-TOKEN": default.tracker_tokens[tracker].XSRF_TOKEN,
            "laravel_session": default.tracker_tokens[tracker].session_token,
        }
        try:
            response = requests.get(
                f"{self.config.torrents_url}/{torrent_id}", cookies=cookies
            )
            parsed = BeautifulSoup(response.text, "html.parser")
            token = parsed.find("meta", attrs={"name": "csrf-token"})["content"]
            return token
        except BaseException as e:
            logger.print(f"[bold red]Something went wrong {e}[/bold red]")
            return None


torf_start_time = time.time()


def torf_cb(torrent, filepath, pieces_done, pieces_total):
    """Handles torrent creation timer"""
    global torf_start_time

    if pieces_done == 0:
        torf_start_time = time.time()  # Reset start time when hashing starts

    elapsed_time = time.time() - torf_start_time

    # Calculate percentage done
    if pieces_total > 0:
        percentage_done = (pieces_done / pieces_total) * 100
    else:
        percentage_done = 0

    # Estimate ETA (if at least one piece is done)
    if pieces_done > 0:
        estimated_total_time = elapsed_time / (pieces_done / pieces_total)
        eta_seconds = max(0, estimated_total_time - elapsed_time)
        eta = time.strftime("%M:%S", time.gmtime(eta_seconds))
    else:
        eta = "--:--"

    # Calculate hashing speed (MB/s)
    if elapsed_time > 0 and pieces_done > 0:
        piece_size = torrent.piece_size / (1024 * 1024)
        speed = (pieces_done * piece_size) / elapsed_time
        speed_str = f"{speed:.2f} MB/s"
    else:
        speed_str = "-- MB/s"

    # Display progress with percentage, speed, and ETA
    cli_ui.info_progress(
        f"Hashing... {speed_str} | ETA: {eta}", int(percentage_done), 100
    )

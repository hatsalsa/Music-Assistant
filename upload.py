import argparse
import asyncio
import os
import sys
import traceback
from src.console import console as logger
from src.filechecks import FilesChecks
from src.mediaparser import MediaParser
from src.torrentcreate import Torrent
from src.torrentname import Setup

try:
    from config import config
except Exception as e:
    if not os.path.exists(f"{os.getcwd()}/config.yml"):
        print(f"Config file not found {e}")
        exit()
    else:
        print(traceback.print_exc())
class Upload:
    def __init__(self, args):
        self.args = args
        pass


    async def do_the_thing(self):
        parser = MediaParser(directory=self.args)
        data = await parser.info_parser()
        name, search_name, artist, album = await Setup(data=data).torrent_name()
        checks = FilesChecks(name, config)
        file_exists = await checks.check_tmp_directory()
        if not file_exists:
            logger.print("[bold green] No .torrent file found")
            dupes = await checks.parse_dupes(search_name)
            if not dupes:
                logger.print("[bold yellow] No Duplicates found")
                logger.print("[bold red] Creating Torrent...")
                torrent = Torrent(self.args, config, name, artist, album)
                file_path = await torrent.create()
                upload = await  torrent.upload_torrent()
            else:
                logger.print(f'[bold red] Duplicate found of: {name}')
                exit()
        elif file_exists:
            logger.print("[bold yellow] .torrent File exists")



async def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("path", help="Enter directory path")
        args, unknown_args = parser.parse_known_args()
        if unknown_args:
            logger.print(f'[red] Error: Unrecognized arguments: {unknown_args}')
            sys.exit(1)
        logger.print(f'[blue] Argument Received: {args.path}')
        upload = Upload(args=args.path)
        await upload.do_the_thing()

    except asyncio.CancelledError:
        logger.print("[red]Tasks were cancelled. Exiting safely.[/red]")
    except KeyboardInterrupt:
        logger.print("[bold red]Program interrupted. Exiting safely.[/bold red]")
    except Exception as e:
        logger.print(f"[bold red]Unexpected error: {e}[/bold red]")
    finally:
        sys.exit()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except(KeyboardInterrupt, SystemExit):
        pass
    except BaseException as e:
        logger.print(f"[bold red]Critical error: {e}[/bold red]")
    finally:
        sys.exit(0)
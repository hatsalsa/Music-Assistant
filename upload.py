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
from beaupy import confirm

try:
    from config import config, filenames, Config
    from utils.collections import load_yaml, merge_dict
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


    async def do_the_thing(self, tracker_config, tracker):
        parser = MediaParser(directory=self.args)
        data = await parser.info_parser()
        create = Setup(data=data)
        name, search_name, artist, album  = await create.torrent_name()
        checks = FilesChecks(name, tracker_config)
        duped = await checks.parse_dupes(search_name, tracker)
        if duped:
            logger.print(f'[bold red] Duplicate found of: {name} on {tracker}, It also may be a cache issue.')
            exit()
        logger.print("[bold yellow] No Duplicates found")
        create_upload = confirm("Would you like to create and upload? (Esc to exit)")
        if create_upload is None:
            exit()
        elif create_upload:
            torrent = Torrent(self.args, tracker_config, name, artist, album)
            await create.create_tmp_dir(name, tracker)
            await create.desc(name, tracker)
            logger.print("[bold green] Temp directory created. [/bold green]")
            logger.print("[bold magenta] Creating .torrent file... [/bold magenta]")
            await torrent.create(tracker)
            await  torrent.upload_torrent(tracker)
        elif not create_upload:
            file_exists = await checks.check_tmp_directory(tracker_dir=tracker)
            torrent = Torrent(self.args, tracker_config, name, artist, album)
            if not file_exists:
                logger.print(f"[bold red] Theres no .torrent file in tmp/{tracker}/{name} directory to upload/overwrite. [/bold red]")
            elif file_exists:
                logger.print(f"[bold yellow] There's a .torrent currently in tmp/{tracker}/{name} [/bold yellow]")
                overwrite = confirm("Would you like to overwrite the .torrent? (ESC to exit)")
                if overwrite is None:
                    exit()
                elif overwrite:
                    logger.print(f"overwriting the current {name}.torrent")
                    await torrent.create(tracker)
                    await torrent.upload_torrent(tracker)
                elif not overwrite:
                    logger.print("Uploading current .torrent file")


async def process_single_tracker(args):
    """Process the array of trackers one by one"""
    upload = Upload(args=args)
    for tracker in config.tracker:
        tracker_config = load_yaml(filenames.tracker_config.format(tracker=tracker.lower()))
        user_config = (load_yaml(filenames.user_tracker_config.format(tracker=tracker.lower())) or load_yaml(filenames.user_tracker_config.format(tracker=tracker)))
        if user_config:
            merge_dict(tracker_config, user_config)
        _tracker = Config(tracker_config)
        await upload.do_the_thing(tracker_config=_tracker, tracker=tracker)

async def main():
    try:
        parser = argparse.ArgumentParser()
        parser.add_argument("path", help="Enter directory path")
        args, unknown_args = parser.parse_known_args()
        if unknown_args:
            logger.print(f'[red] Error: Unrecognized arguments: {unknown_args}')
            sys.exit(1)
        logger.print(f'[blue] Argument Received: {args.path}')
        await process_single_tracker(args.path)

    except asyncio.CancelledError:
        logger.print("[red]Tasks were cancelled. Exiting safely.[/red]")
    except KeyboardInterrupt:
        logger.print("[bold red]Program interrupted. Exiting safely.[/bold red]")
    except Exception as err:
        trace_string = traceback.format_exc()
        logger.print(f'There was an issue: {trace_string}')
        logger.print(f"[bold red]Unexpected error: {err}[/bold red]")
    finally:
        sys.exit()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except(KeyboardInterrupt, SystemExit):
        pass
    except BaseException as e:
        tb_str = traceback.format_exc()
        logger.print(f'[bold red] There was an issue: {tb_str} [/bold red]')
        logger.print(f"[bold red]Critical error: {e}[/bold red]")
    finally:
        sys.exit(0)
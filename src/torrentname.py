import os
from pathlib import Path


class Setup:
    def __init__(self, data):
        self.data = data

    async def torrent_name(self):
        """Parses mediainfo of a file at index 0 to create the .torrent and search name"""
        sampling = ''
        artist = self.data[0]['Artist']
        album = self.data[0]['Album_Title']
        year = str(self.data[0].get('Year', '')).split('-')[0] or None
        track_format = self.data[0]['Format']
        bits = self.data[0]['Bits']
        match self.data[0]['Sampling']:
            case '44100':
                sampling = '44.1kHz'
            case '48000':
                sampling = '48kHz'
            case '24000':
                sampling = '24khZ'
            case '96000':
                sampling = '96kHz'
        torrent_name = f'{artist} {album} {year} {track_format} {bits}bits {sampling}'
        search_name = f'{artist} {album}'
        return torrent_name, search_name, artist, album

    async def desc(self, name, tracker_dir):
        """ Create a description file based on the parsed mediainfo from the files"""
        track_sampling = ''
        with open(f'{os.getcwd()}/tmp/{tracker_dir}/{name}/DESCRIPTION.txt', 'a', encoding="utf-8") as desc:
            desc.write(
                "[table]\n[tr]\n[th] Artists [/th]\n[th] Song Name [/th]\n[th] Track # [/th]\n[th] Format [/th]\n[th] Duration [/th]\n[th] Sampling [/th]\n[th] Bits [/th]\n[/tr]\n")
        for track in self.data:
            track_artist = track['Artist']
            track_name = track['Track_Title']
            track_number = track['Track_Number']
            track_format = track['Format']
            track_duration = track['Duration']
            match track['Sampling']:
                case '44100':
                    track_sampling = '44.1kHz'
                case '48000':
                    track_sampling = '48kHz'
                case '24000':
                    track_sampling = '24khZ'
                case '96000':
                    track_sampling = '96kHz'
            track_bits = track['Bits']
            with open(f'{os.getcwd()}/tmp/{tracker_dir}/{name}/DESCRIPTION.txt', 'a', encoding="utf-8") as desc:
                desc.write(
                    f'[tr][td]{track_artist}[/td]  [td]{track_name} [/td] [td]{track_number} [/td] [td]{track_format}[/td] [td] {track_duration} [/td] [td] {track_sampling} [/td] [td] {track_bits} [/td][/tr] \n')
        with open(f'{os.getcwd()}/tmp/{tracker_dir}/{name}/DESCRIPTION.txt', 'a', encoding="utf-8") as desc:
            desc.write('[/table]')

    @staticmethod
    async def create_tmp_dir(name, tracker_dir):
        """Creates tmp directory """
        Path(f'{Path.cwd()}/tmp/{tracker_dir}/{name}').mkdir(parents=True, exist_ok=True)

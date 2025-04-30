import json
import os

from pymediainfo import MediaInfo


class MediaParser:
    def __init__(self, directory):
        self.directory = directory

    async def info_parser(self):
        """Parses and formats mediainfo data from files."""
        track_data = []
        excluded_extensions = {".jpeg", ".jpg", ".png", ".lrc", ".cue", ".txt"}
        files = [entry.name for entry in os.scandir(self.directory) if
                 entry.is_file() and entry.name.lower().endswith(tuple(excluded_extensions)) is False]
        for file in files:
            media_info = MediaInfo.parse(f'{self.directory}/{file}', output='JSON', full=False)
            info = json.loads(media_info)
            for track in info['media']['track']:
                if track['@type'] == 'General':
                    track_data.append({
                        'Artist': track.get('Performer', {}),
                        'Album_Title': track.get('Album', {}),
                        'Track_Title': track.get('Track', {}),
                        'Track_Number': track.get('Track_Position', {}),
                        'Total_Tracks': track.get('Track_Position_Total', {}),
                    })
                elif track['@type'] == 'Audio':
                    seconds = float(track.get('Duration'))
                    minutes = int(seconds) // 60
                    remaining_seconds = seconds % 60
                    duration = f'{int(minutes)} minutes and {remaining_seconds:.0f} seconds'
                    bps = float(track.get('BitRate'))
                    kbps = f'{int(bps) / 1000:.0f} kb/s'
                    track_data[-1].update({
                        'Format': track.get('Format', {}),
                        'Duration': duration if duration else {},
                        'Sampling': track.get('SamplingRate', {}),
                        'Bits': track.get('BitDepth', {}),
                        'MD5': track.get('extra', {}).get('MD5_Undecoded', {}),
                        "Compression": track.get('Compression_Mode', {}),
                        "Bitrate": kbps if kbps else {}
                    })
        track_data.sort(key=lambda x: int(x['Track_Number']) if str(x['Track_Number']).isdigit() else float('inf'))
        return track_data

import json
from pathlib import Path
from pymediainfo import MediaInfo


class MediaParser:
    def __init__(self, directory: str):
        # Clean and normalize the directory path
        self.directory = Path(directory.strip().strip('"').strip("'")).resolve()

    async def info_parser(self):
        """Parses and formats mediainfo data from files."""
        track_data = []
        excluded_extensions = {".jpeg", ".jpg", ".png", ".lrc", ".cue", ".txt"}

        try:
            # Safely iterate files
            files = [
                entry
                for entry in self.directory.iterdir()
                if entry.is_file() and entry.suffix.lower() not in excluded_extensions
            ]
        except OSError as e:
            print(f"[Error] Cannot read directory: {self.directory} ({e})")
            return []

        for file in files:
            try:
                media_info = MediaInfo.parse(file, output="JSON", full=False)
                info = json.loads(media_info)
            except Exception as e:
                print(f"[Warning] Skipping file {file.name}: {e}")
                continue

            for track in info.get("media", {}).get("track", []):
                if track["@type"] == "General":
                    print(track.get('Recorded_Date',''))
                    track_data.append(
                        {
                            "Artist": track.get("Performer", ""),
                            "Album_Title": track.get("Album", ""),
                            "Track_Title": track.get("Track", ""),
                            "Year": track.get('Recorded_Date', ""),
                            "Track_Number": track.get("Track_Position", ""),
                            "Total_Tracks": track.get("Track_Position_Total", ""),
                        }
                    )
                elif track["@type"] == "Audio" and track_data:
                    try:
                        seconds = float(track.get("Duration", 0))
                        minutes = int(seconds // 60)
                        remaining_seconds = seconds % 60
                        duration = f"{int(minutes)} minutes and {remaining_seconds:.0f} seconds"

                        bps = float(track.get("BitRate", 0))
                        kbps = f"{bps / 1000:.0f} kb/s"
                    except (ValueError, TypeError):
                        duration = ""
                        kbps = ""

                    track_data[-1].update(
                        {
                            "Format": track.get("Format", ""),
                            "Duration": duration,
                            "Sampling": track.get("SamplingRate", ""),
                            "Bits": track.get("BitDepth", ""),
                            "MD5": track.get("extra", {}).get("MD5_Undecoded", ""),
                            "Compression": track.get("Compression_Mode", ""),
                            "Bitrate": kbps,
                        }
                    )

        # Sort by track number, safely ignoring non-numeric values
        track_data.sort(
            key=lambda x: int(x["Track_Number"])
            if str(x["Track_Number"]).isdigit()
            else float("inf")
        )
        return track_data

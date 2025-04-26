## Music Assistant
`Music Assistant` is simple tool written in python to automate the creation of music torrents in UNIT3D trackers.

Install the `requirements`:
```bash
pip install -r requirements.txt
```
Setup:
```bash
mv example.yml config.yml
```

Usage:
```bash
python upload.py /path/to/your/album # e.g. /home/user/music/collection/eminem/Kamikaze
```
> [!NOTE]
> It's a WIP tool so currently it only works with directories and UNIT3D trackers and expect a lot of BUGS.

### To-do: 
- Find a better way to handle the cover/banner image uploading.
- Multi-tracker support (currently is manual setup).
- Extend the Deezer API usage.
- Better file format handling when uploading. (only tested with FLACs).
- Torrent clients support.



# Jellyfin Music Player

AKA jfmp, a minimalist cross-platform gapless music player for Jellyfin.

![screenshot 1](docs/screenshot_03.png)

## Install from sources

### Requirements

As the wheel for music-player-core is not yet provided you have to build it yourself from sources, this is why you need these requirements:

* boost >=1.55.0
* ffmpeg >= 2.0 (including libswresample)
* portaudio >=v19
* chromaprint

#### Debian and derivatives

```bash
apt-get install python-dev libsnappy-dev libtool yasm libchromaprint-dev portaudio19-dev libboost-dev

# FFmpeg
apt-get install libavformat-dev libavresample-dev
```

### Install and build

    git clone https://github.com/n-peugnet/jfmp
    pip install --user pipenv
    pipenv install

_Note: if you want to use your system theme you will have to symlink your virtualenv's `PySide2` folder to your system one. It is probably located around `/usr/lib/python3/dist-packages/PySide2`._

### Run

    pipenv run ./main.py

## Built With

-   [music-player-core](https://github.com/albertz/music-player-core)
-   [jellyfin-apiclient-python](https://github.com/iwalton3/jellyfin-apiclient-python)

## To Do

- [x] Really working cache and streaming system
- [ ] Limit cache to a maximum size (LRU ? FIFO ?)
- [x] Pip package with Wheel dist (using GitHub actions ?)
- [ ] Double click in Queue sets the current playing song
- [ ] List all albums with lazy loading (Check Qt possibilities)
- [ ] Songs & Artists list (Tabs ?)
- [ ] Sort lists (QTableWidgets ?)
- [ ] Quick jump in list (with keyboard keys)
- [ ] Search functionality
- [ ] Playback bar with seek functionality
- [ ] Queue managment (Reorder, Play next, Add to Queue...)
- [ ] Remote Jellyfin control
- [ ] Desktop integration (using DBUS ? Needs research)
- [ ] Packaging (APT first)
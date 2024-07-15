# Youtube Keyword Search Clip Downloader
This is an unofficial Downloader for https://ytks.app

## Description

This downloader allows you to use the results of the Youtube Keyword Search website to download all found clips.
It uses [FFMPEG](https://ffmpeg.org/) to actually download the clips.
## Usage

To download one clip from YTKS click the "Copy link to match" button of a match and paste it into "YTKS Match Url" Field

To download all clips of a search, download the match list on the website via the "Download match list" button (requires plus/pro) and then select it via the "select match list" button in the downloader  

When downloading a single clip it will be downloaded to the same directory the .exe is in.
Ff you're downloading a match list it creates a folder (with the same name as the match list file name) in the same directory the .exe is in and puts all downloaded clips into that folder

## Build from source

1. Make sure you have installed python 3.12 or higher or [install it](https://www.python.org/downloads/)
2. Install the required libraries via ``pip install -r requirements.txt``
3. Wrap the code into an executable by running ``pyinstaller --noconfirm --onefile --console --icon logo.ico ./main.py``

# Youtube Keyword Search Clip Downloader
This is an unofficial Downloader for https://ytks.app

## Description

This downloader allows you to use the results of the Youtube Keyword Search website to download all found clips.
It uses [FFMPEG](https://ffmpeg.org/) to actually download the clips.
## Usage

To download one clip from YTKS click the "Copy link to match" button of a match and paste it into "YTKS Match Url" Field

To donwload all clips of a search download the match list on the website via the "Download match list" button (requires plus/pro) and select then select it via the "select match list" button in the downloader  

## Build from source

1. Make sure you have installed python 3.9 or higher or [install it](https://www.python.org/downloads/)
2. Install the required libraries via ``pip install -r requirements.txt``
3. Wrap the code into an executable by running ``auto-py-to-exe`` and select auto-py-to-exe-config.json under Settings -> Import Config From JSON File

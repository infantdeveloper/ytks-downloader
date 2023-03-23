import math
import os
from threading import Thread

import youtube_dl
import urllib.request
import zipfile

from PyQt6 import QtGui
from PyQt6.QtWidgets import *

# ------------------------------------  GUI ------------------------------------------------------

app = QApplication([])
window = QWidget()
window.setWindowTitle("YTKS Downloader")
window.setFixedSize(320, 150)
layout = QVBoxLayout()
layout.addWidget(QLabel("Enter YTKS match URL: "))
lineEdit = QLineEdit()
layout.addWidget(lineEdit)
group = QWidget()
hbox = QHBoxLayout()
hbox.addWidget(QLabel("Clip Duration (s): "))
durationField = QSpinBox()
durationField.setValue(15)
hbox.addWidget(durationField)
group.setLayout(hbox)
layout.addWidget(group)
downloadButton = QPushButton('Download clip')
downloadButton.setEnabled(False)
layout.addWidget(downloadButton)
window.setLayout(layout)

downloadInProgress = False


def text_changed():
    if downloadInProgress:
        return
    _, _, success = check_url(lineEdit.text())
    if success:
        downloadButton.setEnabled(True)
    else:
        downloadButton.setEnabled(False)


def button_pressed():
    global downloadInProgress
    downloadInProgress = True
    downloadButton.setText("Downloading clip...")
    thread = Thread(target=lambda: process(lineEdit.text(), durationField.value()), daemon=False)
    thread.start()
    downloadButton.setEnabled(False)
    downloadInProgress = False


lineEdit.textChanged.connect(text_changed)
downloadButton.clicked.connect(button_pressed)

# ------------------------------------  Helper funcs  ------------------------------------------------------


def main():
    window.show()
    app.exec()


def check_url(url):
    x0 = url.split("&lvid=")
    if len(x0) < 2:
        return None, None, False
    x1 = x0[1].split("&lmt=")
    if len(x0[1]) < 2:
        return None, None, False
    x2 = x0[1].split("&lmt=")
    id = x1[0]
    timestamp = int(x2[1])
    return id, timestamp, True

# ------------------------------------  Download logic ------------------------------------------------------


def time_in_s_to_time_string(time):
    return str(math.floor(time / 60)) + ":" + str(time % 60)


def process(url, duration):
    id, timestamp, success = check_url(url)
    if not success:
        return

    url_vid = None
    url_aud = None

    done = False
    while not done:
        try:
            with youtube_dl.YoutubeDL({
                'format': 'bestvideo+bestaudio',
                "youtube_include_dash_manifest": False
            }) as ytdl:
                x = ytdl.extract_info("https://www.youtube.com/watch?v="+id, False)
                url_vid = x["requested_formats"][0]["url"]
                url_aud = x["requested_formats"][1]["url"]
                title = x["title"]
                done = True
        except Exception:
            pass
    if not os.path.isfile("./ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe"):
        print("Downloading FFMPEG")
        downloadButton.setText("Downloading FFMPEG...")
        urllib.request.urlretrieve(
            "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip",
            "ffmpeg.zip")
        print("Extracting FFMPEG")
        with zipfile.ZipFile("ffmpeg.zip", 'r') as zip_ref:
            zip_ref.extractall("./")
        try:
            os.remove("ffmpeg.zip")
        except OSError:
            pass
    os.chdir("./ffmpeg-master-latest-win64-gpl/bin")
    start_time_in_s = round((timestamp / 1000)-duration/2)
    command = "ffmpeg.exe -ss " + time_in_s_to_time_string(start_time_in_s) + " -i \"" + url_vid + \
              "\" -ss " + time_in_s_to_time_string(start_time_in_s) + " -i \"" + url_aud + \
              "\" -map 0:v -map 1:a -c:v libx264 -c:a aac -t " + time_in_s_to_time_string(duration) + " -y \"../../" + title + "-" + id + "-" + str(round(timestamp / 1000)) + ".mp4\""
    print(command)
    os.system(command)
    os.chdir("../../")
    downloadButton.setText("Download clip")
    downloadButton.setEnabled(True)


if __name__ == '__main__':
    main()

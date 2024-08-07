import io
import json
import time
import os
import re
from pathlib import Path
from threading import Thread

import yt_dlp
import urllib.request
import zipfile
import webbrowser
import requests

from PyQt6.QtWidgets import *


def get_newest_version():
    response = requests.get("https://github.com/infantdeveloper/ytks-downloader/releases/latest")
    if response is not None and response.history is not None and len(response.history) == 1:
        redirect_response = response.history[0]
        if redirect_response.status_code == 302:
            redirect_url = redirect_response.headers["location"]
            if redirect_url.startswith("https://github.com/infantdeveloper/ytks-downloader/releases/tag/"):
                return redirect_url.replace("https://github.com/infantdeveloper/ytks-downloader/releases/tag/", "")
    return None

# ------------------------------------  GUI ------------------------------------------------------

version = "1.1.12"
newest_version = get_newest_version()

app = QApplication([])
window = QWidget()
window.setWindowTitle("YTKS Downloader - " + version)
window.setFixedSize(400, 330)
layout = QVBoxLayout()

group1 = QWidget()
hbox1 = QHBoxLayout()
repoButton = QPushButton("Downloader Repo")
ytksButton = QPushButton("YTKS.app")
hbox1.addWidget(ytksButton)
hbox1.addWidget(repoButton)
group1.setLayout(hbox1)

layout.addWidget(QLabel("Enter YTKS match URL: "))
lineEdit = QLineEdit()
layout.addWidget(lineEdit)

layout.addWidget(QLabel("Or select a YTKS match list"))
group0 = QWidget()
hbox0 = QHBoxLayout()
fileChooserButton = QPushButton("Select match list")
hbox0.addWidget(fileChooserButton)
resetChosenFileButton = QPushButton("Reset")
resetChosenFileButton.setEnabled(False)
hbox0.addWidget(resetChosenFileButton)
group0.setLayout(hbox0)
layout.addWidget(group0)


group = QWidget()
hbox = QHBoxLayout()
hbox.addWidget(QLabel("Clip Duration (s): "))
durationField = QSpinBox()
durationField.setValue(15)
hbox.addWidget(durationField)
group.setLayout(hbox)
layout.addWidget(group)

infoLabel = QLabel("")
layout.addWidget(infoLabel)
downloadButton = QPushButton('Download clip')
downloadButton.setEnabled(False)
layout.addWidget(downloadButton)
layout.addWidget(group1)

if newest_version is not None and int(newest_version.replace(".", "")) > int(version.replace(".", "")):
    layout.addWidget(QLabel("New version available! Current: (" + version + ") Newest: (" + newest_version + ")"))

window.setLayout(layout)

downloadInProgress = False
chosenFile = ""


def text_changed():
    if len(lineEdit.text()) > 0:
        fileChooserButton.setEnabled(False)
    else:
        fileChooserButton.setEnabled(True)
    if downloadInProgress:
        return
    _, _, success = check_url(lineEdit.text())
    if success:
        downloadButton.setEnabled(True)
    else:
        downloadButton.setEnabled(False)


def button_pressed():
    thread = Thread(target=lambda: button_pressed_action(), daemon=False)
    thread.start()


def button_pressed_action():
    global downloadInProgress
    global chosenFile
    downloadInProgress = True
    downloadButton.setEnabled(False)
    try:
        if chosenFile == "":
            infoLabel.setText("Downloading clip...")
            process(lineEdit.text(), durationField.value()+5)  # Whole function is in seperate thread -> no blocking
        else:
            file = io.open(chosenFile, "r", encoding="utf-8")
            ytks_matches = json.load(file)
            file.close()
            match_list = ytks_matches["matches"]
            folder_name = os.path.basename(chosenFile.replace(".json", ""))
            Path(folder_name).mkdir(parents=True, exist_ok=True)
            currentClip = 1
            totalClips = len(match_list)
            for match in match_list:
                infoLabel.setText("Downloading clip (" + str(currentClip) + "/" + str(totalClips) + ")...")
                print("Processing URL(" + str(currentClip) + "/" + str(totalClips) + "): " + match["matchUrl"])
                # Whole function is in seperate thread -> no blocking
                process(match["matchUrl"], round(match["duration"]/1000)+durationField.value(), folder_name=folder_name)
                currentClip += 1
        infoLabel.setText("")
    except Exception as ex:
        print(ex)
        infoLabel.setText("Error during parsing/downloading. Check if correct file is selected")
    downloadButton.setText("Download clip")
    downloadButton.setEnabled(True)
    downloadInProgress = False


def file_chooser_button_pressed():
    global chosenFile
    result = QFileDialog.getOpenFileName(caption="Open match list", filter="YTKS Match list (*.json)")
    if result and result[0] != "":
        chosenFile = result[0]
        print(result[0])
        lineEdit.setEnabled(False)
        fileChooserButton.setEnabled(False)
        fileChooserButton.setText(os.path.basename(chosenFile))
        resetChosenFileButton.setEnabled(True)
        if not downloadInProgress:
            downloadButton.setEnabled(True)


def reset_chosen_file_button_pressed():
    global chosenFile
    if downloadInProgress:
        return
    chosenFile = ""
    lineEdit.setEnabled(True)
    fileChooserButton.setEnabled(True)
    fileChooserButton.setText("Select match list")
    resetChosenFileButton.setEnabled(False)
    downloadButton.setEnabled(False)


def open_repo():
    webbrowser.open("https://github.com/infantdeveloper/ytks-downloader", new=0, autoraise=True)


def open_ytks():
    webbrowser.open("https://ytks.app", new=0, autoraise=True)


lineEdit.textChanged.connect(text_changed)
fileChooserButton.clicked.connect(file_chooser_button_pressed)
resetChosenFileButton.clicked.connect(reset_chosen_file_button_pressed)
downloadButton.clicked.connect(button_pressed)
repoButton.clicked.connect(open_repo)
ytksButton.clicked.connect(open_ytks)

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


def replace_non_alpha_num(text):
    return re.sub('[^0-9a-zA-Z]+', '_', text)


# ------------------------------------  Download logic ------------------------------------------------------


def time_in_s_to_time_string(value):
    return time.strftime('%H:%M:%S', time.gmtime(value))


def process(url, duration, folder_name=""):
    id, timestamp, success = check_url(url)
    if not success:
        return

    url_vid = None
    url_aud = None

    tries_left = 3
    done = False
    while not done and tries_left > 0:
        tries_left = tries_left - 1
        try:
            with yt_dlp.YoutubeDL({
                'format': 'bestvideo[format_note!=Premium]+bestaudio[format_id=249-0]/bestvideo[format_note!=Premium]+bestaudio[format_id=249]/bestvideo[format_note!=Premium]+bestaudio',
                "youtube_include_dash_manifest": False
            }) as ytdl:
                x = ytdl.extract_info("https://www.youtube.com/watch?v="+id, False)
                url_vid = x["requested_formats"][0]["url"]
                url_aud = x["requested_formats"][1]["url"]
                title = x["title"]
                upload_year, upload_month, upload_day = x["upload_date"][:4], x["upload_date"][4:6], x["upload_date"][6:8]
                done = True
        except Exception as e:
            if e.args[0] == 'ERROR: Private video\nSign in if you\'ve been granted access to this video':
                print("WARNING: Skipping video with id " + str(id) + " because it is private and can't be accessed")
                return
    if not done:
        print("Error: Unable to download clip from video \"" + url + "\"")
        return
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
        downloadButton.setText("Downloading clips...")
    os.chdir("./ffmpeg-master-latest-win64-gpl/bin")
    start_time_in_s = round((timestamp / 1000)-duration/2)
    start_time_in_s = max(start_time_in_s, 0)
    command = "ffmpeg.exe -ss " + time_in_s_to_time_string(start_time_in_s) + " -i \"" + url_vid + \
              "\" -ss " + time_in_s_to_time_string(start_time_in_s) + " -i \"" + url_aud + \
              "\" -map 0:v -map 1:a -c:v libx264 -c:a aac -b:a 320k -t " + time_in_s_to_time_string(duration) + \
              " -y \"" + "../../" + (folder_name + "/" if folder_name != "" else "") + upload_year+"-"+upload_month+"-"+upload_day+"-" + replace_non_alpha_num(
        title.strip()) + "-" + id + "-" + str(round(timestamp / 1000)) + ".mp4\""
    print(command)

    tries_left = 2
    success = False
    while not success and tries_left > 0:
        tries_left = tries_left - 1
        try:
            os.system(command)
            success = True
        except Exception as e:
            pass
    os.chdir("../../")


if __name__ == '__main__':
    main()

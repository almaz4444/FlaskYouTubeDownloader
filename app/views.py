import os
from urllib.parse import quote
from threading import Thread
from time import sleep
import requests

from flask import Flask, render_template, request, send_file, redirect
from pytube import YouTube
from moviepy.editor import *

from . import app, db


posters_get_url = 'https://i.ytimg.com/vi/{}/maxresdefault.jpg'

resolutions = [
    "720",
    "480",
    "360",
    "240",
    "144"
]

@app.route('/')
def index():
    return render_template('index.html', video_path='', resolutions=resolutions)

@app.route('/download/video', methods=['GET'])
def download_video():
    resolution = request.args.get("resolution")
    name = request.args.get('name')

    video = video_download(url, resolution)
    path = video.get_file_path()

    return send_file(f"static\\videos\\({resolution}) {path.replace(os.getcwd(), '')[1::]}", as_attachment=True)
    

@app.route('/submit', methods=['POST'])
def submit():
    url = request.form['url']
    return redirect(f'/search?url={url}')

@app.route('/search', methods=['GET'])
def search_video():
    url = request.args.get('url')
    
    video_path = get_static_path(download_videos(url), "720p")
    poster_path = get_poster(get_video_id_by_url(url), get_name_by_path(video_path))
    
    return render_template('index.html', video_path=video_path, poster_path=poster_path, resolutions=resolutions, video_url=url)

def download_videos(url):
    yt = YouTube(url)
    path = f"{os.getcwd()}\\app\\static\\videos"
    main_video_path = ''

    for resolution in resolutions:
        video = yt.streams.filter(res=f"{resolution}p").first()
        video.download(output_path=path, filename_prefix=f"({video.resolution}) ")
        if(resolution == "720"):
            main_video_path = video.get_file_path()
    
    return main_video_path

def get_static_path(file_path, resolution):
    return f'videos/({resolution}) {file_path.replace(f"{os.getcwd()}", "")[1:-1]}4'.replace("\\", "/")

    
def get_poster(video_id, name):
    fielname = name.replace('(720p) ', '').replace(".mp4", "")
    with open(f"app\\static\\images\\{fielname}.jpg", "wb") as f:
        f.write(requests.get(posters_get_url.format(video_id)).content)
    return f'images/{fielname}.jpg'

def get_video_id_by_url(url):
    return url.split("/")[-1]

def get_name_by_path(path):
    return path.split("/")[-1]

def resize_clip(clip, width=None, height=None):
    if width is None and height is None:
        return clip
    new_size = None
    if width is not None and height is not None:
        new_size = (width, height)
    elif width is not None:
        new_size = (width, round(clip.size[1] * width / clip.size[0]))
    else:
        new_size = (round(clip.size[0] * height / clip.size[1]), height)

    with open("log.txt", "w") as f:
        f.write(f"{new_size[0]}, {new_size[1]}")

    return clip.resize(new_size)

def remove_file_for(time, path):
    while True:
        try:
            sleep(time)
            os.remove(path)
            break
        except:
            pass

def debug(log):
    with open("log.txt", "w", encoding="utf-8") as f:
        f.write(log)

def shielding(string):
    return string.replace(":", "_").replace("/", "_").replace("\\", "_").replace("\"", "_").replace("*", "_").replace("?", "_").replace("<", "_").replace(">", "_").replace("|", "_")
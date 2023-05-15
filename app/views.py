import os
from threading import Thread
import requests

from flask import Flask, render_template, request, send_file, redirect
from pytube import YouTube

from . import app
from .models import Video
from .util import *


posters_get_url = 'https://i.ytimg.com/vi/{}/maxresdefault.jpg'


@app.route('/')
def index():
    return render_template('index.html', video_path='')

@app.route('/download/video', methods=['GET'])
def download_video():
    url = request.args.get("url")
    resolution = request.args.get("resolution")

    main_video_stream = YouTube(url).streams.filter(progressive=True)[-1]
    is_main_video = main_video_stream.resolution == resolution
    video = get_video(url, resolution, not is_main_video)
    video_name = video.get_file_path().replace(os.getcwd(), '')[1::]
    path = f"static\\videos\\({resolution}) {video_name}"

    return send_file(path, as_attachment=True)
    
@app.route('/download/poster', methods=['GET'])
def download_poster():
    url = request.args.get("url")
    poster = get_poster(get_video_id_by_url(url), YouTube(url).title)
    poster_path = f"static\\{poster}"

    del_poster_th = Thread(target=remove_file_for, args=(5, f"app\\{poster_path}"))

    return send_file(poster_path, as_attachment=True), del_poster_th.start()

@app.route('/get_action', methods=['POST'])
def get_action():
    url = request.form['url']
    url = url.replace("?v=", "/")

    return redirect(f'/search?url={url}')

@app.route('/search', methods=['GET'])
def search_video():
    url = request.args.get('url')
    
    videos = load_videos(url)
    video_path = get_static_path(videos[0].path, videos[0].res)
    poster_path = get_poster(get_video_id_by_url(url), get_name_by_path(video_path))
    
    return render_template('index.html', videos=videos, poster_path=poster_path)

def load_videos(url):
    yt = YouTube(url)
    
    videos = []

    for stream in yt.streams.filter(progressive="True")[::-1]:
        video = yt.streams.get_by_itag(stream.itag)
        videos.append(Video(url,
                            f'({video.resolution}) {yt.title}',
                            video.get_file_path(),
                            get_static_path(video.get_file_path(), video.resolution),
                            video.resolution,
                            video.mime_type.split("/")[-1], 
                            human_format(video.filesize))
                    )

    main_video = get_video(url, videos[0].res, False)
    videos[0].path = main_video.get_file_path()
    videos[0].static_path = get_static_path(main_video.get_file_path(), main_video.resolution)

    return videos

def on_complete_download_function(stream, file_path):
    Thread(target=remove_file_for, args=(5, file_path)).start()
    
def get_video(url, resolution, is_deletable=True):
    yt = YouTube(url, on_complete_callback=on_complete_download_function if is_deletable else None)

    video = yt.streams.filter(res=resolution).first()
    video.download(output_path="app/static/videos", filename_prefix=f"({video.resolution}) ")
    
    return video


def get_poster(video_id, name):
    fielname = shielding(name.replace('(720p) ', '').replace(".mp4", ""))
    with open(f"app/static/images/{fielname}.jpg", "wb") as f:
        f.write(requests.get(posters_get_url.format(video_id)).content)
    return f'images/{fielname}.jpg'

import os
from threading import Thread
import requests

from flask import Flask, render_template, request, send_file, redirect, flash, make_response
from pytube import YouTube

from . import app, db
from .models import Video, Comment
from .util import *


posters_get_url = 'https://i.ytimg.com/vi/{}/maxresdefault.jpg'


@app.route('/')
def index():
    return render_template('index.html', comments=Comment.query.all())

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

@app.route('/search', methods=['GET'])
def search_video():
    url = request.args.get('url')
    is_no_load = request.args.get('IS_NO_LOAD')
    
    if not is_no_load:
        videos, main_video_index = load_videos(url)
        if videos:
            video_path = videos[main_video_index].static_path
            debug(video_path)
            poster_path = get_poster(get_video_id_by_url(url), get_name_by_path(video_path))
            
            return render_template('index.html', videos=videos, poster_path=poster_path, comments=Comment.query.all())
    
    return render_template('index.html', comments=Comment.query.all())

@app.route('/send_comment', methods=['GET', 'POST'])
def send_comment():
    if request.method == 'POST':
        comment_text = request.form['comment']

        author = 'Anonymous'

        if len(comment_text.split(':')) != 1:
            author, *text = comment_text.split(':')
        else:
            text = comment_text

        if text:
            comment = Comment()
            comment.author = author
            comment.text = ':'.join(text)

            db.session.add(comment)
            db.session.commit()

            response = make_response()
            response.headers['IS_NO_LOAD'] = 'True'
            
            return redirect(request.headers.get('Referer'), Response=response)
    else:
        return render_template('index.html', comments=Comment.query.all())
    

@app.route('/get_action', methods=['POST'])
def get_action():
    url = request.form['url']
    url = url.replace("?v=", "/")

    return redirect(f'/search?url={url}')

def load_videos(url):
    try: 
        yt = YouTube(url)
        if yt.check_availability():
            raise
    except:
        return None, flash('Неверный URL', 'error')
    
    videos = []
    main_video_index = 0

    for i, stream in enumerate(yt.streams.filter(progressive=True)[::-1]):
        video = yt.streams.get_by_itag(stream.itag)

        if i == 0:
            video = get_video(url, video.resolution, False)

        videos.append(Video(url,
                            f'({video.resolution}) {yt.title}',
                            video.get_file_path(),
                            get_static_path(video.get_file_path(), video.resolution),
                            video.resolution,
                            video.mime_type.split("/")[-1], 
                            human_format(video.filesize))
                    )

    return videos, main_video_index

def complete_download_function(stream, file_path):
    Thread(target=remove_file_for, args=(5, file_path)).start()
    
def get_video(url, resolution, is_deletable=True):
    yt = YouTube(url, on_complete_callback=complete_download_function if is_deletable else None)

    video = yt.streams.filter(res=resolution).first()
    video.download(output_path="app\\static\\videos", filename_prefix=f"({video.resolution}) ")
    
    return video


def get_poster(video_id, name):
    fielname = shielding(name.replace('(720p) ', '').replace(".mp4", ""))
    with open(f"app/static/images/{fielname}.jpg", "wb") as f:
        f.write(requests.get(posters_get_url.format(video_id)).content)
    return f'images/{fielname}.jpg'
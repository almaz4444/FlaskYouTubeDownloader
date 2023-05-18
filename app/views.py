import os
from threading import Thread
import requests

from flask import Flask, render_template, request, send_file, redirect, flash, make_response
from pytube import YouTube

from . import app, db
from .models import Video, Poster, Audio, Comment
from .util import *


posters_get_url = 'https://i.ytimg.com/vi/{}/maxresdefault.jpg'


@app.route('/')
def index():
    return render_template('index.html', comments=Comment.query.all())

@app.route('/download/video', methods=['GET'])
def download_video():
    url = request.args.get("url")
    resolution = request.args.get("resolution")

    yt = YouTube(url)
    streams = yt.streaming_data['formats'][::-1]
    stream = list(filter(lambda data: data['qualityLabel'] == resolution, streams))[0]
    video_path, video_filesize = get_video(stream, yt.title)

    return send_file(video_path.replace('app\\', ''), as_attachment=True)

@app.route('/download/audio', methods=['GET'])
def download_audio():
    url = request.args.get("url")

    yt = YouTube(url)
    streams = yt.streaming_data['formats'][::-1]
    audio = get_audio(get_video_id_by_url(url), YouTube(url).title)

    return send_file(poster_path, as_attachment=True), del_poster_th.start()
    
@app.route('/download/poster', methods=['GET'])
def download_poster():
    url = request.args.get("url")
    poster = get_poster(get_video_id_by_url(url), YouTube(url).title)
    poster_path = f"static\\{poster.path}"

    return send_file(poster_path, as_attachment=True), del_poster_th.start()

@app.route('/search', methods=['GET'])
def search_video():
    url = request.args.get('url')
    answer_to_id = request.args.get('answer_to_id')

    if not answer_to_id:
        answer_to_id = 0
    
    videos, main_video_index = load_videos(url)
    if videos:
        video_name = videos[main_video_index].name
        poster = get_poster(get_video_id_by_url(url), video_name)
        
        return render_template('index.html', videos=videos, poster=poster, answer_to_id=int(answer_to_id), comments=Comment.query.all())

@app.route('/send_comment', methods=['GET', 'POST'])
def send_comment():
    if request.method == 'POST':
        comment_text = request.form['comment']

        author = 'Anonymous'

        if len(comment_text.split(':')) != 1:
            author, *text = comment_text.split(':')
            text = ':'.join(text)
        else:
            text = comment_text

        if len(text.strip()):
            comment = Comment()
            comment.author = author
            comment.text = text

            db.session.add(comment)
            db.session.commit()
            
        return redirect(request.headers.get('Referer'))
    else:
        return redirect('/')

@app.route('/answer', methods=['GET', 'POST'])
def answer_comment():
    if request.method == 'GET':
        answer_id = request.args.get('comment_id')
        url = request.headers.get('Referer')

        if answer_id:
            url += f'&answer_to_id={answer_id}'

        return redirect(url)
    else:
        return redirect('/')

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

    streams = yt.streaming_data['formats'][::-1]

    for i, stream in enumerate(streams):
        res = stream["qualityLabel"]
        mime_type = stream["mimeType"].split(";")[0].split("/")[-1]

        if i == 0:
            video_path, video_filesize = get_video(stream, yt.title, mime_type)
        else:
            head = requests.head(stream['url'])
            video_filesize = int(head.headers.get('Content-Length', 0))

        videos.append(Video(url = url,
                            name = f'({res}) {yt.title}',
                            static_path = video_path.replace('app\\static', '').replace('\\', '/'),
                            res = res,
                            mime_type = mime_type, 
                            file_size = human_format(video_filesize))
                    )

    return videos, main_video_index

def complete_download_function(stream, file_path):
    Thread(target=remove_file_for, args=(5, file_path)).start()
    
def get_video(stream: dict, name: str, mime_type: str):
    path = f'app\\static\\videos\\({stream["qualityLabel"]}) {shielding(name)}.{mime_type}'
    filesize = 0

    response = requests.get(stream['url'])

    with open(path, "wb") as file:
        file.write(response.content)
        filesize = file.__sizeof__()

    return path, filesize

def get_audio(stream: dict, name: str, mime_type: str):
    path = f'app\\static\\audio\\({stream["qualityLabel"]}) {shielding(name)}.{mime_type}'
    filesize = 0

    response = requests.get(stream['url'])

    with open(path, "wb") as file:
        file.write(response.content)
        filesize = file.__sizeof__()

    return Audio(path, mime_type, filesize)

def get_poster(video_id, name):
    fielname = shielding(name.replace('(720p) ', '').replace(".mp4", ""))
    filesize = 0

    with open(f"app/static/images/{fielname}.jpg", "wb") as file:
        file.write(requests.get(posters_get_url.format(video_id)).content)
        filesize = file.__sizeof__()

    return Poster(f'images/{fielname}.jpg', 'jpg', human_format(filesize))
import os
from threading import Thread
import requests
import smtpd

from flask import Flask, render_template, request, send_file, redirect, flash
from pytube import YouTube, exceptions

from . import app, db
from .models import Video, Poster, Audio, Comment, AnsweredCommentsId
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
    video_path = get_video(stream, yt.title)
    
    del_video_th = Thread(target=remove_file_for, args=(10, video_path))

    return send_file(video_path.replace('app\\', ''), as_attachment=True), del_video_th.start()

@app.route('/download/audio', methods=['GET'])
def download_audio():
    url = request.args.get("url")

    yt = YouTube(url)
    streams = yt.streaming_data['formats'][::-1]
    audio = get_audio(get_video_id_by_url(url), YouTube(url).title)

    return send_file(poster_path, as_attachment=True)
    
@app.route('/download/poster', methods=['GET'])
def download_poster():
    url = request.args.get("url")

    poster = get_poster(get_video_id_by_url(url), shielding(YouTube(url).title))
    del_poster_th = Thread(target=remove_file_for, args=(10, f'app\\{poster.url}'))

    return send_file(poster.url, as_attachment=True), del_poster_th.start()

@app.route('/search', methods=['GET'])
def search_video():
    url = request.args.get('url')
    answered_id = request.args.get('answered_id', default=0)

    if not url:
        return redirect('/')
    
    videos, poster = load_videos(url)
    
    if not videos:
        return redirect('/')
    else:
        return render_template('search.html', videos=videos, poster=poster, answered_id=int(answered_id), comments=Comment.query.all())

@app.route('/send_comment', methods=['GET', 'POST'])
def send_comment():
    if request.method == 'POST':
        comment_text = request.form['comment']
        answered_id = request.headers.get('Referer').split('answered_id=')[-1]
        url = request.headers.get('Referer').split("&")[0]

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
            comment.is_answer = "answered_id" in request.headers.get('Referer')

            if comment.is_answer:
                comment = Comment.query.get(int(answered_id))

                answer = AnsweredCommentsId()
                answer.author = author
                answer.text = text

                comment.answered_messages_id = [*comment.answered_messages_id, answer]

            db.session.add(comment)
            db.session.commit()
            
        return redirect(url)
    else:
        return redirect('/')

@app.route('/login', methods=["GET", "POST"])
def login():
    return render_template('login.html')

@app.route('/sign_up', methods=["GET", "POST"])
def sign_up():
    login = request.form['login']
    password = request.form['password']

    return redirect('/')

@app.route('/answer', methods=['GET', 'POST'])
def answer_comment():
    if request.method == 'GET':
        answer_id = request.args.get('comment_id')
        url = request.headers.get('Referer')

        if answer_id and "search" in url:
            return redirect(f"{url.split('&')[0]}&answered_id={answer_id}")
        else:
            return redirect('/')
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

    try:
        streams = yt.streaming_data['formats'][::-1]
    except exceptions.AgeRestrictedError:
        return None, flash('Данное видео не доступно!', 'error')

    for i, stream in enumerate(streams):
        res = stream["qualityLabel"]
        mime_type = stream["mimeType"].split(";")[0].split("/")[-1]
        raw_url = stream['url']
        video_head = requests.head(raw_url)
        video_filesize = int(video_head.headers.get('Content-Length', 0))

        videos.append(Video(url = url,
                            raw_url=raw_url,
                            name = f'({res}) {yt.title}',
                            res = res,
                            mime_type = mime_type,
                            file_size = human_format(video_filesize))
                    )
    

    video_id = get_video_id_by_url(url)
    poster_url = posters_get_url.format(video_id)
    poster_head = requests.head(poster_url)
    poster_filesize = int(poster_head.headers.get('Content-Length', 0))

    poster = Poster(poster_url, 'jpg', human_format(poster_filesize))

    return videos, poster

def complete_download_function(stream, file_path):
    Thread(target=remove_file_for, args=(5, file_path)).start()

def get_video(stream: dict, name: str):
    mime_type = stream["mimeType"].split(";")[0].split("/")[-1]
    path = f'app\\static\\videos\\({stream["qualityLabel"]}) {shielding(name)}.{mime_type}'

    response = requests.get(stream['url'])

    with open(path, "wb") as file:
        file.write(response.content)

    return path

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

    return Poster(f'static\\images\\{fielname}.jpg', 'jpg', human_format(filesize))
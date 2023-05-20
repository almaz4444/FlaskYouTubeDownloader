import os
from threading import Thread
import requests
import subprocess

from flask import Flask, render_template, request, send_file, redirect, flash
from pytube import YouTube, exceptions

from . import app, db
from .models import Video, Poster, Audio, Comment, AnsweredCommentsId
from .util import *


posters_get_url = 'https://i.ytimg.com/vi/{}/maxresdefault.jpg'
TimeOfDeleteFile = 10


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
    video_path = get_video(stream=stream, name=shielding(yt.title))
    
    del_video_th = Thread(target=remove_file_for, args=(TimeOfDeleteFile, video_path))

    return send_file(video_path.replace('app\\', ''), as_attachment=True), del_video_th.start()

@app.route('/download/audio', methods=['GET'])
def download_audio():
    url = request.args.get("url")

    yt = YouTube(url)
    stream = yt.streaming_data['formats'][-1]
    audio_path = get_audio(stream, YouTube(url).title)
    
    del_audio_th = Thread(target=remove_file_for, args=(TimeOfDeleteFile, audio_path))

    return send_file(audio_path.replace('app\\', ''), download_name=f'{yt.title}.mp3', as_attachment=True), del_audio_th.start()
    
@app.route('/download/poster', methods=['GET'])
def download_poster():
    url = request.args.get("url")

    poster = get_poster(get_video_id_by_url(url), shielding(YouTube(url).title))

    del_poster_th = Thread(target=remove_file_for, args=(TimeOfDeleteFile, f'app\\{poster.url}'))

    return send_file(poster.url, as_attachment=True), del_poster_th.start()

@app.route('/search', methods=['GET'])
def search_video():
    url = request.args.get('url')
    answered_id = request.args.get('answered_id', default=0)

    if not url:
        return redirect('/')
    
    media = load_media(url)
    
    if not media:
        return redirect('/')
    else:
        videos, poster, audio = media
        return render_template('search.html', videos=videos, poster=poster, audio=audio, answered_id=int(answered_id), comments=Comment.query.all())

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

def load_videos(yt: YouTube, streams: list, url: str):
    videos = []
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

    return videos

def load_poster(yt: YouTube, url: str):
    video_id = get_video_id_by_url(url)
    poster_url = posters_get_url.format(video_id)
    poster_head = requests.head(poster_url)
    poster_filesize = int(poster_head.headers.get('Content-Length', 0))

    poster = Poster(poster_url, 'jpg', human_format(poster_filesize))

    return poster

def load_audio(yt: YouTube):
    head = requests.head(yt.streaming_data['adaptiveFormats'][-1]['url'])
    filesize = int(head.headers.get('Content-Length', 0))

    audio = Audio("mp3", human_format(filesize))

    return audio

def load_media(url):
    try: 
        yt = YouTube(url)
        if yt.check_availability():
            raise
    except:
        return flash('Неверный URL', 'error')

    try:
        streams = yt.streaming_data['formats'][::-1]
    except exceptions.AgeRestrictedError:
        return flash('Данное видео не доступно!', 'error')

    videos = load_videos(yt, streams, url)
    poster = load_poster(yt, url)
    audio = load_audio(yt)

    return videos, poster, audio

def get_audio(stream: dict, name: str):
    url = stream['url']
    name = shielding(name).replace('&', '_').replace(' ', '_')
    output_path = f"app\\static\\audios\\{name}.mp3"

    video_file_path = get_video(name=f"{name}.mp4", url=url)
    extract_audio(video_file_path, output_path)
    os.remove(video_file_path)

    return output_path

def complete_download_function(stream, file_path):
    Thread(target=remove_file_for, args=(5, file_path)).start()

def get_video(name: str, stream: dict = None, url: str = None):
    path = f'app\\static\\videos\\{name}'
    if not url:
        url = stream['url']
        mime_type = stream["mimeType"].split(";")[0].split("/")[-1]
        path = f'app\\static\\videos\\({stream["qualityLabel"]}) {name}.{mime_type}'

    with open(path, "wb") as file:
        response = requests.get(url)
        file.write(response.content)

    return path

def extract_audio(video_file_path, audio_file_path):
    command = f"ffmpeg -i {video_file_path} -vn -ab 128k -ar 44100 -y {audio_file_path}"
    subprocess.run(command, shell=True, check=True)

def get_poster(video_id, name):
    fielname = shielding(name.replace('(720p) ', '').replace(".mp4", ""))
    filesize = 0

    with open(f"app/static/images/{fielname}.jpg", "wb") as file:
        file.write(requests.get(posters_get_url.format(video_id)).content)
        filesize = file.__sizeof__()

    return Poster(f'static\\images\\{fielname}.jpg', 'jpg', human_format(filesize))
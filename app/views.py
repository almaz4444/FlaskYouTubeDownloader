import os
from threading import Thread
import subprocess

from flask import Flask, render_template, request, send_file, redirect, flash, current_app, _app_ctx_stack
from pytube import YouTube, exceptions
import requests

from . import app, db
from .models import Video, Poster, Audio, Comment, AnsweredCommentsId
from .util import *
from .settings import *

@app.route('/')
def index():
    return render_template('index.html', comments=Comment.query.all())

@app.route('/download/video', methods=['GET', 'POST'])
def download_video():
    id = request.args.get("id")
    itag = int(request.args.get("itag"))

    yt = YouTube(f"https://youtu.be/{id}")

    try:
        streaming_data_format = 'formats'
        streams = yt.streaming_data['formats']
        stream = list(filter(lambda data: data['itag'] == itag, streams))[0]
    except:
        streaming_data_format = 'adaptiveFormats'
        streams = yt.streaming_data['adaptiveFormats']
        stream = list(filter(lambda data: data['itag'] == itag, streams))[0]

    if streaming_data_format == 'formats':
        video_path = get_video(stream=stream, name=shielding(yt.title))
    else:
        video_path = get_video_high_qality(yt, stream, shielding(yt.title))
    
    del_video_thread = Thread(target=remove_file_for, args=(TimeOfDeleteFile, video_path))

    return send_file(video_path.replace('app\\', ''), as_attachment=True), del_video_thread.start()


@app.route('/download/audio', methods=['GET'])
def download_audio():
    id = request.args.get("id")

    yt = YouTube(f"https://youtu.be/{id}")
    stream = get_best_audio(yt.streaming_data['adaptiveFormats'])
    audio_path = get_audio(stream, yt.title)
    
    del_audio_thread = Thread(target=remove_file_for, args=(TimeOfDeleteFile, audio_path))

    return send_file(audio_path.replace('app\\', ''), download_name=f'{yt.title}.mp3', as_attachment=True), del_audio_thread.start()
    
@app.route('/download/poster', methods=['GET'])
def download_poster():
    id = request.args.get("id")
    yt = YouTube(f"https://youtu.be/{id}")

    poster = get_poster(id, shielding(yt.title))

    del_poster_thread = Thread(target=remove_file_for, args=(TimeOfDeleteFile, f'app\\{poster.path}'))

    return send_file(poster.path, as_attachment=True), del_poster_thread.start()

@app.route('/search', methods=['GET'])
def search_video():
    id = request.args.get('id')
    answered_id = request.args.get('answered_id', default=0)

    if not id:
        return redirect('/')
    
    media = load_media(id)
    
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
    url = url.replace("?v=", "/").replace('?feature=share', '')
    id = get_video_id_by_url(url)

    return redirect(f'/search?id={id}')

def find_best_video(video_formats):
    best_video_index = None
    for i, video_format in enumerate(video_formats):
        if 'video' in video_format['mimeType']:
            if not best_video_index or int(video_format['qualityLabel'].replace('p', '')) > int(video_formats[best_video_index]['qualityLabel'].replace('p', '')):
                best_video_index = i
    return best_video_index

def load_videos(yt: YouTube, adaptive_streams: list, normal_streams: list, id: str):
    videos = []
    for i, stream in enumerate(adaptive_streams):
        mime_type = get_mime_type(stream)
        if not 'webm' in mime_type:
            res = stream["qualityLabel"]

            video_filesize = get_filesize_by_url(stream['url'])

            normal_stream_list = list(filter(lambda stream_data: stream_data['qualityLabel'] == res, normal_streams))
            if len(normal_stream_list):
                stream = normal_stream_list[0]
                mime_type = get_mime_type(stream)
            else:
                audio_stream = get_best_audio(yt.streaming_data['adaptiveFormats'])
                audio_filesize = get_filesize_by_url(audio_stream['url'])
                video_filesize += audio_filesize

            videos.append(Video(id = id,
                                raw_url = stream['url'],
                                name = f'({res}) {yt.title}',
                                res = res,
                                mime_type = mime_type,
                                file_size = human_format(video_filesize),
                                itag = stream['itag'],
                                with_audio = len(normal_stream_list))
                        )

    return videos

def load_poster(yt: YouTube, id: str):
    poster_url = posters_get_url.format(id)
    poster_filesize = human_format(get_filesize_by_url(poster_url))

    poster = Poster(url=poster_url, mime_type='jpg', file_size=poster_filesize)

    return poster

def get_best_audio(audio_formats):
    best_audio = None
    for audio_format in audio_formats:
        if 'audio' in audio_format['mimeType']:
            if not best_audio or audio_format['bitrate'] > best_audio['bitrate']:
                best_audio = audio_format
    return best_audio

def load_audio(yt: YouTube):
    url = yt.streaming_data['adaptiveFormats'][-1]['url']
    file_size = human_format(get_filesize_by_url(url))

    audio = Audio("mp3", file_size)

    return audio

def load_media(id):
    try: 
        yt = YouTube(f"https://youtu.be/{id}")
        if yt.check_availability():
            raise
    except:
        return flash('Неверный URL', 'error')

    try:
        adaptive_streams = list(filter(lambda stream_data: 'video' in stream_data['mimeType'], yt.streaming_data['adaptiveFormats']))
        normal_streams = list(filter(lambda stream_data: 'video' in stream_data['mimeType'], yt.streaming_data['formats']))
    except exceptions.AgeRestrictedError:
        return flash('Данное видео не доступно!', 'error')

    videos = load_videos(yt, adaptive_streams, normal_streams, id)
    poster = load_poster(yt, id)
    audio = load_audio(yt)

    return videos, poster, audio

def get_audio(stream: dict, name: str):
    url = stream['url']
    name = shielding(name).replace('&', '_').replace(' ', '_')
    output_path = f"app\\temp\\audios\\{name}.mp3"

    video_file_path = get_video(name=f"{name}.mp4", url=url)
    extract_audio(video_file_path, output_path)
    os.remove(video_file_path)

    return output_path

def complete_download_function(stream, file_path):
    Thread(target=remove_file_for, args=(5, file_path)).start()

def get_video(name: str, stream: dict = None, url: str = None, mime_type: str = None):
    path = f'app\\temp\\videos\\{name}'
    if not url:
        url = stream['url']
        mime_type = mime_type if mime_type else get_mime_type(stream)
        path = f'app\\temp\\videos\\({stream["qualityLabel"]}) {name}.{mime_type}'

    with open(path, "wb") as file:
        response = requests.get(url)
        file.write(response.content)

    return path

def get_video_high_qality(yt: YouTube, stream: dict, name: str):
    mime_type = get_mime_type(stream)
    video_name = f'(no audio) {name}'

    video_path = f'app\\temp\\videos\\({stream["qualityLabel"]}) {video_name}.{mime_type}'
    audio_path = f'app\\temp\\audios\\{shielding(name).replace("&", "_").replace(" ", "_")}.mp3'
    output_path = f"app\\temp\\videos\\({stream['qualityLabel']}) {name}.mp4"

    video_download_thread = Thread(target=get_video, kwargs={'name': video_name, 'stream': stream, 'mime_type': mime_type})
    audio_download_thread = Thread(target=get_audio, args=(get_best_audio(yt.streaming_data['adaptiveFormats']), name))

    video_download_thread.start()
    audio_download_thread.start()
    video_download_thread.join()
    audio_download_thread.join()

    # if mime_type == 'webm':
    #     new_video_path = video_path.replace('.webm', '.mp4')
        
    #     command = ['ffmpeg', '-y', '-i', video_path, '-c:v', 'libx264', '-c:a', 'aac', "-pix_fmt", "yuv420p", new_video_path]
    #     subprocess.call(command, shell=True)

    #     # os.remove(video_path)
    #     video_path = new_video_path

    # print('-'*100)

    command = ["ffmpeg", "-y", "-i", video_path, "-i", audio_path, "-c:v", "copy", "-c:a", "aac", "-strict", "experimental", "-pix_fmt", "yuv420p", output_path]
    subprocess.call(command, shell=True)

    os.remove(video_path)
    os.remove(audio_path)

    return output_path

def extract_audio(video_file_path, audio_file_path):
    command = f"ffmpeg -i {video_file_path} -vn -ab 128k -ar 44100 -y {audio_file_path}"
    subprocess.run(command, shell=True, check=True)

def get_poster(video_id, name):
    fielname = shielding(name.replace('(720p) ', '').replace(".mp4", ""))
    filesize = 0

    with open(f"app\\temp\\images\\{fielname}.jpg", "wb") as file:
        file.write(requests.get(posters_get_url.format(video_id)).content)
        filesize = file.__sizeof__()

    return Poster(path=f'temp\\images\\{fielname}.jpg', mime_type='jpg', file_size=human_format(filesize))
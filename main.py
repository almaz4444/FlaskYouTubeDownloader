from pytube import YouTube
from pytube.cli import on_progress

url = 'www.youtube.com/watch/58P97YgDV6o'

yt=YouTube(url)
video = yt.streams.filter(res="720p").first()
filesize = video.filesize

def progress_function(chunk, file_handle, bytes_remaining):
    global filesize
    current = ((filesize - bytes_remaining)/filesize)
    percent = ('{0:.1f}').format(current*100)
    print(f'\r{percent}%', end='')

yt=YouTube(url, on_progress_callback=progress_function)
video = yt.streams.filter(res="720p").first()

video.download(skip_existing=False)

print()
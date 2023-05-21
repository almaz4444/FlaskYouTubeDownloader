import os
from time import sleep

import requests

def get_static_path(file_path, resolution):
    return f'videos/({resolution}) {file_path.replace(f"{os.getcwd()}", "")[1::]}'.replace("\\", "/")
    
def human_format(byte_size):
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    for unit in units:
        if byte_size < 1024:
            return f'{round(byte_size, 2)} {unit}'
        byte_size /= 1024
    return f'{round(byte_size, 2)} PB'

def get_video_id_by_url(url):
    return url.split("/")[-1]

def get_name_by_path(path):
    return shielding(path.split("/")[-1])

def remove_file_for(time, path):
    while True:
        try:
            sleep(time)
            os.remove(path)
            break
        except Exception as e:
            debug(e)

def debug(log):
    with open("log.txt", "w", encoding="utf-8") as f:
        f.write(str(log))

def get_mime_type(stream):
    return stream['mimeType'].split(";")[0].split("/")[-1]

def get_filesize_by_url(url: str):
    head = requests.head(url)
    filesize = int(head.headers.get('Content-Length', 0))
    return filesize

def shielding(string):
    return string.replace(":", "_").replace("/", "_").replace("\\", "_").replace("\"", "_").replace("*", "_").replace("?", "_").replace("<", "_").replace(">", "_").replace("|", "_")
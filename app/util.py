import os
from time import sleep

# https://www.youtube.com/watch?v=KkIgpz26mjc

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

def shielding(string):
    return string.replace(":", "_").replace("/", "_").replace("\\", "_").replace("\"", "_").replace("*", "_").replace("?", "_").replace("<", "_").replace(">", "_").replace("|", "_")
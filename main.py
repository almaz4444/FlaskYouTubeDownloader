import requests

with open("button.svg", "wb") as file:
    file.write(requests.get('https://work.220youtube.ru/images/button_search.svg').content)
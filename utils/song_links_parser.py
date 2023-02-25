from bs4 import BeautifulSoup
import requests


class Settings:
    url: str = 'https://ruo.morsmusic.org/artist/229?page={}'


def parse():
    urls = []
    for pagination in range(1, 4):
        page = requests.get(Settings.url.format(pagination)).content
        soup = BeautifulSoup(page, 'lxml')
        for link in soup.find_all('a', class_='track-download'):
            urls.append('https://ruo.morsmusic.org' + link['href'])
    return urls


print(parse())

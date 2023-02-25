from bs4 import BeautifulSoup
import requests

url = 'https://ruo.morsmusic.org/artist/229?page={}'
urls = []

for _ in range(1, 4):
    page = requests.get(url.format(_)).content
    soup = BeautifulSoup(page, 'lxml')
    for link in soup.find_all('a', class_='track-download'):
        urls.append('https://ruo.morsmusic.org' + link['href'])
print(urls)

from .scraper import Scraper
import json

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, quote, quote_plus

import re
from loguru import logger

class Manhwa18Webs(Scraper):
  def __init__(self):
    super().__init__()
    self.url = "https://manhwa18.cc/"
    self.bg = None
    self.sf = "ma18"
    self.headers = {
      "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    }

  async def search(self, query: str = ""):
    url = f"https://manhwa18.cc/search?q={quote_plus(query)}"
    mangas = await self.get(url)

    bs = BeautifulSoup(mangas, "html.parser") if mangas else None

    container = bs.find('div', {'class': 'manga-lists'}) if bs else None

    cards = container.find_all("div", {"class": "manga-item"}) if container else None

    results = []
    for card in cards:
      data = {}
      data['url'] = urljoin(self.url, card.findNext("a").get("href"))
      data['title'] = card.findNext("a").get("title")

      data['poster'] = card.findNext("img").get("src")
      
      results.append(data)

    return results

  async def get_chapters(self, data, page: int=1):
    results = data

    content = await self.get(results['url'])
    bs = BeautifulSoup(content, "html.parser") if content else None

    container = bs.find(class_="genres-content") if bs else None
    geners = container.text.strip() if container else "N/A"

    msg = f"<b>{results['title']}</b>\n"
    msg += f"<b>Url</b>: {results['url']}\n"

    msg += f"<b>Geners</b>: <code>{geners}</code>\n\n"
    container = bs.find(class_="dsct")

    des = container.text.strip() if container else "N/A"
    msg += f"<b>Description</b>: <code>{des}</code>\n"

    results['msg'] = msg

    chapters = bs.find("ul", {"class": "row-content-chapter"})
    chapters = chapters.find_all("li", {"class": "a-h"}) if chapters else []

    results['chapters'] = chapters

    return results


  def iter_chapters(self, data, page: int=1):
    chapters_list = []

    if 'chapters' in data:
     for card in data['chapters']:
       chapters_list.append({
         "title": card.find_next("a").text.strip(),
         "url": urljoin(self.url, card.find_next("a")['href']),
         "manga_title": data['title'],
         "poster": data['poster'] if 'poster' in data else None,
         })

    return chapters_list[(page - 1) * 60:page * 60] if page != 1 else chapters_list

  async def get_pictures(self, url, data=None):
    content = await self.get(url)

    bs = BeautifulSoup(content, "html.parser")

    container = bs.find("div", {"class": "read-content wleft tcenter"}) if bs else None
    cards = container.find_all("img") if container else None
    
    images_url = [quote(containers.get("src"), safe=':/%') for containers in cards] if cards else None
    
    return images_url

  async def get_updates(self, page:int=1):
    output = []
    while page < 3:
      url = f"https://manhwa18.cc/page/{page}/"
      try: content = await self.get(url)
      except: content = None
      if content:
        bs = BeautifulSoup(content, "html.parser")

        cards = bs.find_all("div", {"class": "data wleft"})
        if cards:
          for card in cards:
            try:
              data = {}
              data['url'] = urljoin(self.url, card.find_next("a").get("href"))
              data['manga_title'] = card.find_next("a").get("title")

              #data['poster'] = card.find_next("img")['src']
              span_tag = card.find_next("a", class_="btn-link")

              data['title'] = span_tag.text.strip()
              data['chapter_url'] = urljoin(self.url, span_tag.find_next("a").get('href'))

              output.append(data)
              #print(data)
            except:
              continue

      page += 1

    return output

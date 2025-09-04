
from .scraper import Scraper
import json

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, quote, quote_plus

import re
from loguru import logger

class ManhwaClanWebs(Scraper):
  def __init__(self):
    super().__init__()
    self.url = "https://manhwaclan.com/"
    self.bg = None
    self.sf = "mwc"
    self.headers = {
      #"Accept": "*/*",
      "Connection": "keep-alive",
      "Host":"manhwaclan.com/",
      "Referer": "https://manhwaclan.com/",
      "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": "Windows",
      "Sec-Fetch-Dest": "empty",
      "Sec-Fetch-Mode": "cors",
      "Sec-Fetch-Site": "same-origin",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    }

  async def search(self, query: str = ""):
    url = f"https://manhwaclan.com/?s={quote_plus(query)}&post_type=wp-manga"
    mangas = await self.get(url)

    bs = BeautifulSoup(mangas, "html.parser") if mangas else None
    con = bs.find(class_="tab-content-wrap") if bs else None
    
    cards = con.find_all(class_="tab-thumb c-image-hover") if con else None
    cards = [card.findNext('a') for card in cards] if cards else None
    results = []
    if cards:
      for card in cards:
        data = {}
        data['url'] = card.get('href').strip()
        
        data['poster'] = card.findNext("img").get("src").strip()
        data['title'] = card.findNext("img").get("alt").strip()

        results.append(data)

    return results

  async def get_chapters(self, data, page: int=1):
    results = data
    
    content = await self.get(results['url'])
    bs = BeautifulSoup(content, "html.parser") if content else None
    if bs:
      con = bs.find(class_="summary_content")

      generes = con.find_next(class_="genres-content")
      generes = ", ".join([g.text.strip() for g in generes.find_all("a")]) if generes else "N/A"

      des = bs.find(class_="summary__content show-more").text.strip() if bs.find(class_="summary__content show-more") else "N/A"

      results['msg'] = f"<b>{results['title']}</b>\n\n"
      results['msg'] += f"<b>Url:</b> {results['url']}\n"
      results['msg'] += f"<b>Genres:</b> <code>{generes}</code>\n"
      results['msg'] += f"<b>Description:</b> <code>{des}</code>\n"

    chapters = bs.find(class_="page-content-listing single-page") if bs else []
    results['chapters'] = chapters if chapters else []
    
    return results

  def iter_chapters(self, data, page: int=1):
    chapters_list = []

    if data['chapters']:
      cards = data['chapters'].find_all("a")
      for card in cards:
        link = card.get("href", ":")
        if link and link.startswith("https://manhwaclan.com/manga"):
          chapters_list.append({
            "title": card.text.strip(),
            "url": link,
            "manga_title": data['title'],
            "poster": data['poster'] if 'poster' in data else None,
          })
    
    return chapters_list[(page - 1) * 60:page * 60] if page != 1 else chapters_list

  async def get_pictures(self, url, data=None):
    response = await self.get(url)
    bs = BeautifulSoup(response, "html.parser")

    cards = bs.find_all(class_="page-break no-gaps")

    mangas = [card.findNext('img') for card in cards]

    image_links = [manga.get("src").strip() for manga in mangas]
    
    return image_links


  async def get_updates(self, page:int=1):
    output = []
    while page < 5:
      url = f"https://manhwaclan.com/page/{page}/"
      results = await self.get(url)

      bs = BeautifulSoup(results, "html.parser")
      container = bs.find(class_="c-blog__content")

      #container = container.find(class_="c-blog__content")
      mangas = container.find_all(class_="page-listing-item") if container else None
      if mangas:
        for manga in mangas:
          if manga:
            cards = manga.find_all(class_="col-6 col-md-3 badge-pos-1")
            if cards:
              for card in cards:
                try:
                  data = {}
                  a_tag = card.find_next("h3", {"class": "h5"}).find_next("a")

                  data['url'] = a_tag.get("href")
                  data['manga_title'] = a_tag.text.strip()

                  span_tag = card.find_next("span", {"class": "chapter font-meta"}).find_next("a")

                  data['chapter_url'] = span_tag.get("href")
                  data['title'] = span_tag.text.strip()

                  output.append(data)
                except:
                  continue

      page += 1

    return output

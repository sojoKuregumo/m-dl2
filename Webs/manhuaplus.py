
from .scraper import Scraper
import json

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, quote, quote_plus

import re
from loguru import logger

class ManhuaplusWebs(Scraper):
  def __init__(self):
    super().__init__()
    self.url = "https://manhuaplus.org/"
    self.bg = None
    self.sf = "mhpu"
    self.headers = {
      "accept": "application/json, text/javascript, */*; q=0.01",
      #"accept-encoding": "gzip, deflate, br, zstd",
      "accept-language": "en-GB,en-US;q=0.9,en;q=0.8",
      "connection": "keep-alive",
      #"content-length": "11",
      "content-type": "application/x-www-form-urlencoded; charset=UTF-8",
      "host": "manhuaplus.org",
      "origin": "https://manhuaplus.org",
      "referer": "https://manhuaplus.org/search?keyword=",
      "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
      "x-requested-with": "XMLHttpRequest",
    }

  async def search(self, query: str = ""):
    url = f"https://manhuaplus.org/ajax/search"
    params = {
      "search": quote_plus(query)
    }
    mangas = await self.post(url, params=params, rjson=True, headers=self.headers)
    
    results = []
    if mangas and "list" in mangas:
      for card in mangas['list']:
        card['title'] = card.pop("name")
        card['poster'] = urljoin(self.url, card.pop("cover"))
        
        results.append(card)
    
    return results

  async def get_chapters(self, data, page: int=1):
    results = data
    results['msg'] = f"<b>{results['title']}</b>\n\n"
    results['msg'] += f"<b>Url:</b> {results['url']}\n\n"
    results['msg'] += f"<b>Lastest:</b> <code>{results['last']}</code>\n"
    results['msg'] += f"<b>Description:</b> <code>{results['description']}</code>\n"
    
    content = await self.get(results['url'], cs=True)
    bs = BeautifulSoup(content, "html.parser") if content else None
    if bs:
      con = bs.find(class_="bc-fff s1 r2 p-13")
      cards = con.find_all("a") if con else None
      chapters = []
      if cards:
        for card in cards:
          chapters.append({
            "title": card.text.strip(),
            "url": card.get("href"),
            "manga_title": data['title'],
            "poster": data['poster'] if 'poster' in data else None,
          })
      
      results['chapters'] = chapters if chapters else []

    return results

  def iter_chapters(self, data, page: int=1):
    return data['chapters'][(page - 1) * 60:page * 60] if page != 1 else data['chapters']
    
  def get_chapter_id(self, content):
    pattern = r"const CHAPTER_ID = (\d+);"
    match = re.search(pattern, content)
    if match:
      return match.group(1)
      
  async def get_pictures(self, url, data=None):
    images_url = []
    content = await self.get(url, headers=self.headers)

    bs = BeautifulSoup(content, "html.parser") if content else None
    id_tag = bs.find("script", text=re.compile("document.body.classList.add")) if bs else None
    chapter_id = self.get_chapter_id(id_tag.text.strip()) if id_tag else None
    if chapter_id:
      request_url = f"https://manhuaplus.org/ajax/image/list/chap/{chapter_id}"
      headers = self.headers
      
      headers['referer'] = url
      content = await self.get(request_url, rjson=True, headers=self.headers)
      bs = BeautifulSoup(content['html'], "html.parser") if content and 'html' in content else None
      cards = bs.find_all("img") if bs else None
      if cards:
        images_url = [card.get("src") for card in cards]
    
    return images_url

  async def get_updates(self, page:int=1):
    output = []
    results = []
    
    headers = self.headers
    headers['referer'] = "https://manhuaplus.org/home"
    while page < 4:
      url = f"https://manhuaplus.org/all-manga/{page}"
      try: content = await self.get(url, headers=headers)
      except: content = None
      
      if content:
        bs = BeautifulSoup(content, "html.parser")
        div_tag = bs.find(class_='grid gtc-f141a gg-20 p-13 mh-77vh') if bs else None
        
        cards = div_tag.find_all_next("div") if div_tag else None
        if div_tag:
          for card in cards:
            try:
              rdata = card.find_next("div").find_next("a")
              data = {}
              url = urljoin(self.url, rdata['href'])
              if not url in results:
                data['url'] = url
                data['manga_title'] = rdata['title']
                data['poster'] = urljoin(self.url, card.find_next("img")['data-src'])
                
                a_tags = card.find_next("a", class_="clamp toe oh")
                data['chapter_url'] = urljoin(self.url, a_tags['href'])
                data['title'] = a_tags.text.strip()
                
                output.append(data)
                results.append(url)
            except:
              continue
              
      page += 1 
      
    return output

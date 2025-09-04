
from .scraper import Scraper, to_thread
import json

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, quote, quote_plus, urlencode

import re
from loguru import logger
import asyncio

class WeebCentralWebs(Scraper):
  def __init__(self):
    super().__init__()
    self.url = "https://weebcentral.com/"
    self.bg = None
    self.sf = "weebc"
    self.headers = {
      "Accept": "*/*",
      "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
      "Connection": "keep-alive",
      "Content-Type": "application/x-www-form-urlencoded",
      "Host": "weebcentral.com",
      "HX-Request": "true",
      "Origin": "https://weebcentral.com",
      "Referer": "https://weebcentral.com/",
      "sec-ch-ua": '"Google Chrome";v="137", "Chromium";v="137", "Not/A)Brand";v="24"',
      "sec-ch-ua-mobile": "?0",
      "sec-ch-ua-platform": "Windows",
      "Sec-Fetch-Dest": "empty",
      "Sec-Fetch-Mode": "cors",
      "Sec-Fetch-Site": "same-origin",
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    }

  async def search(self, query: str = ""):
    results = []
    
    request_url = "https://weebcentral.com/search/simple?location=main"
    
    params = {"text": query}
    
    headers = self.headers
    headers['Content-Length'] = str(len(query))
    headers["HX-Current-URL"] = "https://weebcentral.com/"
    headers["HX-Target"] = "quick-search-result"
    headers["HX-Trigger"] = "quick-search-input"
    headers["HX-Trigger-Name"] = "text"
    
    content = await to_thread(self.scraper.post, request_url, params, headers=headers)
    if content.status_code == 200:
      bs = BeautifulSoup(content.text, "html.parser")
      
      cards = bs.find_all("a")
      for card in cards:
        data = {}
        data['url'] = card.get('href').strip()
        
        data['poster'] = card.findNext("img")['src'].strip()
        data['title'] = card.findNext("div").findNext("div").text.strip()
        
        results.append(data)

    return results

  async def get_chapters(self, data, page: int=1):
    results = data
    #headers = self.headers
    
    link = data['url'].split("/")
    new_link = "/".join(link[:-1]) + "/full-chapter-list"
    
    #headers['hx-current-url'] = data['url']
    #headers['hx-target'] = "chapter-list"
    #headers['referer'] = data['url']
    
    chapters = await self.get(data['url'], cs=True)
    if chapters:
      bs = BeautifulSoup(chapters, "html.parser")
      
      tags_= bs.find(class_="flex flex-col gap-4")
      msg = f"<b>{data['title']}</b>\n\n"
      tags_ = tags_.find_all("li")
      if tags_:
        for tag in tags_:
          tag_fornt = tag.findNext("strong").text.strip()
          tag_back = tag.find_all("span")
          tag_back = [i.text.strip() for i in tag_back]
          tag_back = ' '.join(tag_back) if tag_back else None
          if tag_back and tag_fornt:
            msg += f"<b>{tag_fornt}</b> <code>{tag_back}</code>\n"
      
      desc = bs.find("section", class_="md:w-8/12 flex flex-col gap-4")
      des = desc.find(class_="flex flex-col gap-4") if desc else None
      
      des = des.find_next("li") if des else None
      des = des.text.strip() if des else None
      
      msg += f"<b>Description:</b> <code>{des}</code>\n"
      results['msg'] = msg
    
    try: chapters = await self.get(new_link, cs=True)#, headers=headers)
    except: chapters = None
    if chapters:
      bs = BeautifulSoup(chapters, "html.parser")

      results['chapters'] = bs.find_all("a", class_="hover:bg-base-300 flex-1 flex items-center p-2")
      
    return results

  def iter_chapters(self, data, page: int=1):
    chapters_list = []
    
    params = {
        'is_prev': 'False',
        'current_page': '1',  # Ensure this is correctly named
        'reading_style': 'long_strip'
    }
    
    if 'chapters' in data:
      for card in data['chapters']:
        title = card.find('span', string=lambda text: "Ch" in text or "Ep" in text or "Vol" in text or "#" in text or "Mi" in text)
        
        chapters_list.append({
          "title": title.text.strip(),
          "url": f"{card['href']}/images?{urlencode(params)}",
          "manga_title": data['title'],
          "poster": data['poster'] if 'poster' in data else None,
        })
    
    return chapters_list[(page - 1) * 60:page * 60] if page != 1 else chapters_list

  async def get_pictures(self, url, data=None):
    image_links = []
    
    url = url.replace("%C2%", "&")
    response = await self.get(url, cs=True)#, headers=self.headers)
    if response:
      bs = BeautifulSoup(response, "html.parser")
      for i in bs.find_all("img"):
        img = i.get('src', "None")
        if "manga" in img or img != '/static/images/brand.png':
          image_links.append(img)

    return image_links


  async def get_updates(self, page:int=1):
    output = []
    while page < 4:
      url = f"https://weebcentral.com/latest-updates/{page}"
      try:
        content = await self.get(url, cs=True)
        bs = BeautifulSoup(content, "html.parser")
        cards = bs.find_all("article")
        for card in cards:
          data = {}
          data['manga_title'] = card.get("data-tip")
          data['url'] = card.findNext("a").get('href')
          data['chapter_url'] = card.findNext("a").findNext("a").get('href')
          data['title'] = card.find_next("span").text.strip()
          output.append(data)
      except:
        pass
      
      page += 1
    
    return output

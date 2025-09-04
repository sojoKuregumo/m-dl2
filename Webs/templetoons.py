
from .scraper import Scraper
import json

from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin, quote, quote_plus

import re
from loguru import logger

class TempleToonsWebs(Scraper):
  def __init__(self):
    super().__init__()
    self.url = "https://templetoons.com/"
    self.api_url = "https://api.templetoons.com/api/allComics"
    self.bg = None
    self.sf = "tt1"
    self.headers = {
      "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36",
    }

  async def search(self, query: str = ""):
    results = []
    mangas = await self.get(self.api_url, cs=True, rjson=True)
    if mangas:
      for card in mangas:
        if query.lower() in card['title'].lower():
          data = {}
          data['title'] = card["title"]

          data['poster'] = card['thumbnail']
          data['url'] = f"https://templetoons.com/comic/{card['series_slug']}"

          results.append(data)

    return results

  async def get_chapters(self, data, page: int=1):
    results = data

    content = await self.get(results['url'], cs=True)
    bs = BeautifulSoup(content, "html.parser") if content else None
    if bs:
      con = bs.find(class_="px-5 py-7 rounded-b-xl text-white/90 shadow-red-400 shadow-md bg-black/50")
      msg = f"<b>{results['title']}</b>\n\n"
      msg += f"<b>Url:</b> {results['url']}\n\n"
      if con:
        for i in con.find_all("p"):
          if i:
            msg += i.text.strip()
            msg += "\n"
            msg += "\n"

      results['msg'] = msg
      results['chapters'] = bs.find_all(
        "a", class_="col-span-full sm:col-span-3 lg:col-span-2 flex flex-row gap-2 bg-[#131212] rounded-lg h-[90px] overflow-hidden"
      )

    return results

  def iter_chapters(self, data, page: int=1):
    chapters_list = []

    if data['chapters']:
      for card in data['chapters']:
        chapter_slug = card["href"].strip("/").split("/")[-1]
        url = data['url'].split("/")[-1]

        chapters_list.append({
            "title": card.find("h1", class_="text-sm md:text-normal").text.strip(),
            "url": f"{self.url}/comic/{url}/{chapter_slug}",
            "manga_title": data['title'],
            "poster": data['poster'] if 'poster' in data else None,
        })  

    return chapters_list[(page - 1) * 60:page * 60] if page != 1 else chapters_list

  async def get_pictures(self, url, data=None):
    images_urls = []
    try:
      data = await self.get(url, cs=True)
      bs = BeautifulSoup(data, 'html.parser')

      imgs_tags = bs.find("script", string=lambda text: "images" in text)
      imgs_dump = json.dumps(imgs_tags.text.strip())
      while True:
        imgs_dump = imgs_dump.replace('\n', ' ')
        imgs_dump = imgs_dump.replace('\\', ' ')
        imgs_dump = imgs_dump.replace('"self.__next_f.push(', ' ')
        imgs_dump = imgs_dump.replace(')"', ' ')
        imgs_dump = imgs_dump.replace(' ', '')
        if '\\' not in imgs_dump:
          break

      imgs_dump = json.dumps(imgs_dump)
      pattern = r'https?://[^\s"]+\.jpg'

      # Find all matches
      image_links = re.findall(pattern, imgs_dump)
      for images_link in image_links:
        img_len = images_link.split('/')
        if len(img_len) > 8:
          images_urls.append(images_link)

    except Exception as e:
      logger.exception(f"Error processing images: {e}")

    return images_urls


  async def get_updates(self, page:int=1):
    output = []
    results = await self.get(self.api_url, cs=True, rjson=True)
    if results:
      for data in results:
        try:
          rdata = {}

          rdata['url'] = f'https://templetoons.com/comic/{data["series_slug"]}'
          rdata['manga_title'] = data['title']

          rdata['chapter_url'] = f'https://templetoons.com/comic/{data["series_slug"]}/{data["Chapter"][0]["chapter_slug"]}'
          rdata['title'] = data['Chapter'][0]['chapter_name']

          rdata['poster'] = data['thumbnail']
          output.append(rdata)
        except:
          continue

    return output

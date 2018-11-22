# -*- coding: utf-8 -*-
"""
    Koober Downloader - Lite Version
"""

from io import BytesIO

import requests
import argparse
import base64
import eyed3
import tqdm
import sys
import os

req = requests.Session()
headers = {'User-Agent' : 'Koober/1 CFNetwork/811.5.4 Darwin/16.6.0', 'Referer': 'https://koober.com/fr'}

def arguments():
  parser = argparse.ArgumentParser()
  parser.add_argument("-d", "--dlpath", type=str, help="Download path", default="./ebooks")
  parser.add_argument("-u", "--url", type=str, help="File URL", required=False)
  parser.add_argument("-f", "--filename", type=str, help="Ouput filename", required=False)
  parser.add_argument("-a", "--all", action='store_true', help="Download All Koobs", required=False)
  args = parser.parse_args()
  return args

def image_to_bytes(url):
  print("\t\t\t • Fetching image")
  buffered = BytesIO(req.get(url).content)
  return buffered.getvalue()

def write_tags(dl_path, filename, book_informations):
  print("\t\t • Writing tags")
  audio_file = eyed3.load("{}/{}".format(dl_path, filename))
  if audio_file is None:
    tag = eyed3.id3.Tag()
    tag.title = book_informations.get('title')
    tag.artist = book_informations.get('writer')
    tag.album = book_informations.get('category')
    tag.album_artist = "Koober".decode('utf-8')
    image = image_to_bytes(book_informations.get('img_url'))
    tag.images.set(3, image, 'image/jpeg')
    tag.save(filename="{}/{}".format(dl_path, filename), version=eyed3.id3.ID3_V2_3, encoding='utf-8')
  else:
    if (audio_file.tag == None):
      audio_file.initTag()
    audio_file.tag.title = book_informations.get('title')
    audio_file.tag.artist = book_informations.get('writer')
    audio_file.tag.album = book_informations.get('category')
    audio_file.tag.album_artist = "Koober".decode('utf-8')
    if not audio_file.tag.images:
      image = image_to_bytes(book_informations.get('img_url'))
      audio_file.tag.images.set(3, image, 'image/jpeg')
    audio_file.tag.save(version=eyed3.id3.ID3_V2_3, encoding='utf-8')

def download_all(dl_path):
  categories_url = "https://koober.com/fr/api/koobs/categories/tous?orderby=&page="
  for s in range(1, 15):
    print("• Fetching page {}".format(s))
    r = req.get("{}{}".format(categories_url, s))
    if r.status_code == 200:
      for item in r.json():
        if item['audio']:
          url = item['audio_url']
          filename = os.path.basename(url)
          book_informations = item['book']
          print("\t • \"{}\" by \"{}\"".format(book_informations.get('title').encode('utf-8'), book_informations.get('writer').encode('utf-8')))
          download_audio(headers, dl_path, filename, url)
          write_tags(dl_path, filename, book_informations)

def download_audio(headers, dl_path, filename, url):
  if not os.path.isfile("{}/{}".format(dl_path, filename)):
    print("\t\t • Downloading")
    audio_file_req = req.get(url, headers=headers, allow_redirects=True, stream=True)
    if audio_file_req.headers.get('content-length'):
      audio_file_length = int(audio_file_req.headers.get('content-length'))
      with open("{}/{}".format(dl_path, filename), 'wb') as item:
        for chunk in tqdm.tqdm(
          audio_file_req.iter_content(chunk_size=1024),
          total=int(audio_file_length / 1024),
          unit='KB',
          desc=filename,
          leave=True
        ):
          item.write(chunk)
    else:
      print("\t\t\t • Unable to download it")
  else:
    print("\t\t • File already exists")
    return False

def main(argv):
  args = arguments()
  filename = ""

  try:
    if args.all:
      download_all(args.dlpath)
    else:
      if not args.filename:
        if not args.url:
          raise Exception('You must enter a valid URL')
        filename = os.path.basename(args.url)
      else:
        filename = args.filename

      download_audio(headers, args.dlpath, filename, args.url)
  except Exception as err:
    print(err)


if __name__ == "__main__":
  main(sys.argv[1:])

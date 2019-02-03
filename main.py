#!/usr/bin/env python
import os
from time import sleep
from urllib import parse
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from redis import Redis
from telegram import Bot, ParseMode

HEADERS = {
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
}

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
CHANNEL_NAM = os.environ.get('CHANNEL_NAM')
ROOT_URL = "https://www.hostloc.com/forum.php?mod=forumdisplay&fid=45&filter=author&orderby=dateline"
BOT = Bot(token=TELEGRAM_BOT_TOKEN)
REDIS_CONN = Redis(host='redis', db=0)


def send_telegram_message(title, url):
    """
    发送telegram消息通知
    :param title: 标题
    :param url: 地址
    """
    try:
        BOT.send_message(CHANNEL_NAM,
                         text="[{}]({})".format(title, url),
                         parse_mode=ParseMode.MARKDOWN,
                         disable_web_page_preview=True)
    except Exception:
        send_telegram_message(title, url)


def get_response():
    """
    获取页面返回的response
    """
    try:
        response = requests.get(ROOT_URL, headers=HEADERS)
        if response.status_code == 200:
            return response
    except Exception:
        return get_response()


if __name__ == '__main__':
    while True:
        resp = get_response()
        soup = BeautifulSoup(resp.text, 'lxml')
        posts = soup.find("table", id="threadlisttableid").findAll("tbody")
        for item in posts:
            if item.get("id") and item["id"].startswith("normalthread"):
                post_a_tag = item.find("a", class_="xst")
                tid = dict(parse.parse_qsl(parse.urlsplit(post_a_tag["href"]).query)).get("tid")  # 获取文章ID
                post_url = urljoin(ROOT_URL, "/thread-{}-1-1.html".format(tid))
                post_title = post_a_tag.get_text()
                if REDIS_CONN.get(tid) is None:
                    send_telegram_message(post_title, post_url)
                    REDIS_CONN.set(tid, post_title, ex=12 * 60 * 60)
        sleep(5)

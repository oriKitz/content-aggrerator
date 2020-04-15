from bs4 import BeautifulSoup
import requests
import datetime
import sqlite3
from dateutil.parser import parse


BBC = 'https://www.bbc.com'
DB = 'news.db'
TABLE_NAME = 'top_stories'


def ts_to_datetime(ts):
    return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=ts)


def scrape_ynet_secondary_news():
    res = requests.get('https://www.ynet.co.il')


def scrape_techcrunch_items():
    res = requests.get('https://techcrunch.com')
    h = BeautifulSoup(res.text, 'html.parser')
    posts = h.find_all(attrs={'class': 'post-block'}, recursive=True)
    for post in posts:
        # print(post)
        headline = post.header.h2.a.string.strip()
        summary = post.find('div', recursive=False).string.strip()
        link = post.header.h2.a['href']
        dt = parse(post.header.div.div.time['datetime']) + datetime.timedelta(hours=10)

        news_item = NewsItem('TechCrunch', headline, summary, link, dt)
        news_item.update_db()


def scrape_bbc_news():
    res = requests.get('https://www.bbc.com/news')
    h = BeautifulSoup(res.text, 'html.parser')
    top_stories = h.html.body.find_all('div', id='orb-modules')[0].find_all('div', recursive=False)[0].find_all(
        'div', id='latest-stories-tab-container')[0].find_all('div', id='news-top-stories-container')[0].div.\
        div.div.div.find_all('div', ['nw-c-top-stories__secondary-item', 'nw-c-top-stories__primary-item'], recursive=False)
    for story in top_stories:
        if 'nw-c-top-stories__secondary-item--1' not in story['class']:
            headline = story.div.find('div', 'gs-c-promo-body').div.a.h3.string
            summary = story.div.find('div', 'gs-c-promo-body').div.p.string
            link = BBC + story.div.find('div', 'gs-c-promo-body').div.a['href']
            try:
                ts = story.div.find('div', 'gs-c-promo-body').ul.li.span.time['data-seconds']
                dt = ts_to_datetime(int(ts)) + datetime.timedelta(hours=3)
            except:
                dt = datetime.datetime.now()

            news_item = NewsItem('BBC', headline, summary, link, dt)
            # print(news_item)
            news_item.update_db()


def create_empty_table():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(f"""create table {TABLE_NAME} (website text, headline text, summary text, link text, publish_time timestamp)""")
    con.commit()
    con.close()


class NewsItem:
    def __init__(self, website, headline, summary, link, publish_time):
        self.website = website
        self.headline = headline
        self.summary = summary
        self.link = link
        self.publish_time = publish_time

    def __repr__(self):
        return f'{self.headline}: {self.summary}\r\n{self.link}\r\n{self.publish_time}'

    @property
    def article_in_db(self):
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute(
            f"""select 1 from {TABLE_NAME} where link = '{self.link}'""")
        results = cur.fetchall()
        con.commit()
        con.close()
        # print(results)
        return bool(len(results))

    @staticmethod
    def solve_escaping(data):
        return data.replace("'", "''")

    def update_db(self):
        if self.article_in_db:
            # print('here')
            return
        con = sqlite3.connect(DB)
        cur = con.cursor()
        # print(f"""insert into {TABLE_NAME} values ('{self.website}', '{self.solve_escaping(self.headline)}', '{self.solve_escaping(self.summary)}', '{self.link}', '{self.publish_time}')""")
        cur.execute(f"""insert into {TABLE_NAME} values ('{self.website}', '{self.solve_escaping(self.headline)}', '{self.solve_escaping(self.summary)}', '{self.link}', '{self.publish_time}')""")
        con.commit()
        con.close()


if __name__ == '__main__':
    scrape_techcrunch_items()

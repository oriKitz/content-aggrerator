from bs4 import BeautifulSoup
import requests
import datetime
import sqlite3
from dateutil.parser import parse


DB = 'db/news.db'
TABLE_NAME = 'top_stories'


def running_message_decorator(func):
    def messager():
        func()
        print(f'finished running {func.__name__} at {datetime.datetime.now()}')
    return messager


def ts_to_datetime(ts):
    return datetime.datetime(1970, 1, 1) + datetime.timedelta(seconds=ts)


def get_ynet_article_date(link):
    article_page = requests.get(link)
    article_html = BeautifulSoup(article_page.text, 'html.parser')
    try:
        publish_time = article_html.find_all(attrs={'class': 'art_header_footer_author'})[1].string
        publish_time = publish_time[publish_time.find(':') + 1:]
    except:
        try:
            publish_time = article_html.find(attrs={'class': 'author-small'}).string.splitlines()[2].strip().replace('|', '')
        except:
            try:
                publish_time = article_html.find(attrs={'class': 'date'}).contents[1]
            except:
                print(f'error extracting date from {link}')
                publish_time = datetime.datetime.now()
                return publish_time
    publish_time = parse(publish_time)
    return publish_time


def scrape_ynet_main_article(html):
    main_article = html.find_all(attrs={'class': 'block B6'})[2]
    main_article = main_article.div.div.div.find_all('div')[1]
    link = 'https://www.ynet.co.il' + main_article.a['href']
    headline = main_article.a.span.string
    summary = main_article.find_all('a')[1].string
    publish_time = get_ynet_article_date(link)

    news_item = NewsItem('ynet', headline, summary, link, publish_time)
    return news_item


def scrape_ynet_primary_articles(html):
    articles = html.find_all(attrs={'class': 'block B6'})[4]
    primary_articles = articles.div.div.find_all(attrs={'class': 'B3'})[:-1]
    news_items = []

    for article in primary_articles:
        headline = article.div.find(attrs={'class': 'cwide'}).a.div.div.string
        summary = article.div.find(attrs={'class': 'cwide'}).a.div.find_all('div')[1].string
        link = 'https://www.ynet.co.il' + article.div.find(attrs={'class': 'cwide'}).a['href']
        publish_time = get_ynet_article_date(link)

        news_item = NewsItem('ynet', headline, summary, link, publish_time)
        news_items.append(news_item)

    return news_items


def scrape_ynet_secondary_articles(html):
    articles = html.find_all(attrs={'class': 'block B6'})[4]
    secondary = articles.div.div.find_all(attrs={'class': 'hpstrip3spanFloatR'})[1:]
    news_items = []

    for article in secondary:
        link = article.a['href']
        if 'ynet.co' not in link:
            link = 'https://www.ynet.co.il' + link
        # headline = article.div.a.div.string
        headline = article.div.a.find_all('div')[1].string
        summary = ''
        publish_time = get_ynet_article_date(link)

        news_item = NewsItem('ynet', headline, summary, link, publish_time)
        news_items.append(news_item)

    return news_items


@running_message_decorator
def scrape_ynet():
    res = requests.get('https://www.ynet.co.il/home/0,7340,L-8,00.html')
    html = BeautifulSoup(res.text, 'html.parser')
    news_items = [scrape_ynet_main_article(html)]
    news_items.extend(scrape_ynet_primary_articles(html))
    news_items.extend(scrape_ynet_secondary_articles(html))

    for news_item in news_items:
        news_item.update_db()


@running_message_decorator
def scrape_techcrunch_items():
    res = requests.get('https://techcrunch.com')
    h = BeautifulSoup(res.text, 'html.parser')
    posts = h.find_all(attrs={'class': 'post-block'}, recursive=True)

    for post in posts:
        headline = post.header.h2.a.string.strip()
        summary = post.find('div', recursive=False).string.strip()
        link = post.header.h2.a['href']
        dt = parse(post.header.div.div.time['datetime']) + datetime.timedelta(hours=10)

        news_item = NewsItem('TechCrunch', headline, summary, link, dt)
        news_item.update_db()


@running_message_decorator
def scrape_bbc_news():
    res = requests.get('https://www.bbc.com/news')
    h = BeautifulSoup(res.text, 'html.parser')
    top_stories = h.find_all('div', ['nw-c-top-stories__secondary-item', 'nw-c-top-stories__primary-item'])

    for story in top_stories:
        if 'nw-c-top-stories__secondary-item--1' not in story['class']:
            headline = story.div.find('div', 'gs-c-promo-body').div.a.h3.string
            summary = story.div.find('div', 'gs-c-promo-body').div.p.string
            link = 'https://www.bbc.com' + story.div.find('div', 'gs-c-promo-body').div.a['href']
            try:
                ts = story.div.find('div', 'gs-c-promo-body').ul.li.span.time['data-seconds']
                dt = ts_to_datetime(int(ts)) + datetime.timedelta(hours=3)
            except:
                dt = datetime.datetime.now()

            news_item = NewsItem('BBC', headline, summary, link, dt)
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
        return f'{self.headline}: {self.summary}\r\n{self.link}\r\n{self.publish_time}\r\n'

    @property
    def article_in_db(self):
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute(f"""select 1 from {TABLE_NAME} where link = '{self.link}'""")
        results = cur.fetchall()
        con.commit()
        con.close()
        return bool(len(results))

    @staticmethod
    def solve_escaping(data):
        return data.replace("'", "''")

    def update_db(self):
        if self.article_in_db:
            return
        con = sqlite3.connect(DB)
        cur = con.cursor()
        cur.execute(f"""insert into {TABLE_NAME} values ('{self.website}', '{self.solve_escaping(self.headline)}', '{self.solve_escaping(self.summary)}', '{self.link}', '{self.publish_time}')""")
        con.commit()
        con.close()


if __name__ == '__main__':
    scrape_ynet()

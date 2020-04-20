from bs4 import BeautifulSoup
import requests
import datetime
import sqlite3
from dateutil.parser import parse
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from .news import NewsItem, DB


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
    link = main_article.a['href'].replace('#autoplay', '')
    if 'ynet.co' not in link:
        link = 'https://www.ynet.co.il' + link
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
        link = article.div.find(attrs={'class': 'cwide'}).a['href'].replace('#autoplay', '')
        if 'ynet.co' not in link:
            link = 'https://www.ynet.co.il' + link
        publish_time = get_ynet_article_date(link)

        news_item = NewsItem('ynet', headline, summary, link, publish_time)
        news_items.append(news_item)

    return news_items


def scrape_ynet_secondary_articles(html):
    articles = html.find_all(attrs={'class': 'block B6'})[4]
    secondary = articles.div.div.find_all(attrs={'class': 'hpstrip3spanFloatR'})[1:]
    news_items = []

    for article in secondary:
        link = article.a['href'].replace('#autoplay', '')
        if 'ynet.co' not in link:
            link = 'https://www.ynet.co.il' + link
        # headline = article.div.a.div.string
        headline = article.div.a.find_all('div')[1].string
        summary = ''
        publish_time = get_ynet_article_date(link)

        news_item = NewsItem('ynet', headline, summary, link, publish_time)
        news_items.append(news_item)

    return news_items


def scrape_ynet():
    res = requests.get('https://www.ynet.co.il/home/0,7340,L-8,00.html')
    html = BeautifulSoup(res.text, 'html.parser')
    news_items = [scrape_ynet_main_article(html)]
    news_items.extend(scrape_ynet_primary_articles(html))
    news_items.extend(scrape_ynet_secondary_articles(html))

    for news_item in news_items:
        news_item.update_db()


def scrape_techcrunch_items():
    res = requests.get('https://techcrunch.com')
    h = BeautifulSoup(res.text, 'html.parser')
    posts = h.find_all(attrs={'class': 'post-block'}, recursive=True)

    for post in posts:
        headline = post.header.h2.a.string.strip()
        try:
            summary = post.find('div', recursive=False).string.strip()
        except:
            summary = ''
        link = post.header.h2.a['href']
        try:
            dt = parse(post.header.div.div.time['datetime']) + datetime.timedelta(hours=10)
        except:
            dt = datetime.datetime.now()

        news_item = NewsItem('TechCrunch', headline, summary, link, dt)
        news_item.update_db()


def scrape_bbc_news():
    res = requests.get('https://www.bbc.com/news')
    h = BeautifulSoup(res.text, 'html.parser')
    articles = h.html.find_all(attrs={'class': 'gs-c-promo-body'})

    for i, article in enumerate(articles):
        if i > 5:
            break
        try:
            headline = article.div.a.h3.string
            summary = article.div.p.string
            link = 'https://www.bbc.com' + article.div.a['href']
            try:
                ts = article.ul.li.span.time['data-seconds']
                dt = ts_to_datetime(int(ts)) + datetime.timedelta(hours=3)
            except:
                dt = datetime.datetime.now()

            news_item = NewsItem('BBC', headline, summary, link, dt)
            news_item.update_db()
        except Exception as e:
            print(e)


def create_empty_table():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(f"""create table {TABLE_NAME} (website text, headline text, summary text, link text, publish_time timestamp)""")
    con.commit()
    con.close()


def events_listener(event):
    if event.exception:
        print(f'Job {event.job_id} failed with error {event.exception} at {datetime.datetime.now()}')
    else:
        print(f'Job {event.job_id} finished running successfully at {datetime.datetime.now()}')


def scrape():
    scheduler = BackgroundScheduler()
    soon = datetime.datetime.now() + datetime.timedelta(seconds=15)
    scheduler.add_job(scrape_bbc_news, 'interval', minutes=15, id='bbc_scraper', next_run_time=soon)
    scheduler.add_job(scrape_techcrunch_items, 'interval', minutes=15, id='techcrunch_scraper', next_run_time=soon)
    scheduler.add_job(scrape_ynet, 'interval', minutes=15, id='ynet_scraper', next_run_time=soon)
    scheduler.add_listener(events_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler.start()

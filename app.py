from flask import Flask, render_template, url_for, request, jsonify
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from scrape_content import scrape_bbc_news, scrape_techcrunch_items, scrape_ynet, NewsItem
from collections import defaultdict


DB = 'news.db'
TABLE_NAME = 'top_stories'


app = Flask(__name__)


@app.route('/')
def main():
    return render_template('main_page.html', data=get_data())


def get_data():
    raw_data = get_raw_data()
    news_items = defaultdict(list)
    for line in raw_data:
        news_items[line[0]].append(NewsItem(*line))
    return {k: reserve_first_items_of_list(v, 8) for k, v in news_items.items()}


def reserve_first_items_of_list(l, n_items):
    return sorted(l, key=lambda x: x.publish_time, reverse=True)[:n_items]


def get_raw_data():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(f"""select * from {TABLE_NAME} where publish_time > date('now', '-1 days') order by publish_time desc""")
    data = cur.fetchall()
    con.commit()
    con.close()
    return data


def scrape():
    scheduler = BackgroundScheduler()
    scheduler.add_job(scrape_bbc_news, 'interval', minutes=5, id='cnn_scraper')
    scheduler.add_job(scrape_techcrunch_items, 'interval', minutes=5, id='techcrunch_scraper')
    scheduler.add_job(scrape_ynet, 'interval', minutes=5, id='ynet_scraper')
    scheduler.start()


if __name__ == '__main__':
    scrape()
    app.run(port=8080, threaded=True)#, debug=True)

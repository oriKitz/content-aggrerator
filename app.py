from flask import Flask, render_template, url_for, request, jsonify
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from collections import defaultdict
import datetime
from threading import Thread
import re
from scrape_content import scrape_bbc_news, scrape_techcrunch_items, scrape_ynet
from news import NewsItem, DB, TABLE_NAME


WEBSITES_ORDER = ['BBC', 'ynet', 'TechCrunch']


app = Flask(__name__)


@app.route('/')
def main():
    return render_template('home.html')


@app.route('/search')
def search():
    search_text = request.args.get('search')
    regex = request.args.get('regex')
    regex = True if regex == 'true' else False
    return jsonify(get_data(search_text, regex))


def get_data(text_limit, use_regex):
    raw_data = get_raw_data(text_limit, use_regex)
    news_items = defaultdict(list)
    for line in raw_data:
        news_items[line[0]].append(NewsItem(*line).__dict__)
    return {k: reserve_first_items_of_list(v, 8) for k, v in news_items.items()}


def reserve_first_items_of_list(l, n_items):
    return sorted(l, key=lambda x: x['publish_time'], reverse=True)[:n_items]


def regexp(expr, item):
    reg = re.compile(expr)
    return reg.search(item) is not None


def get_raw_data(text_limit, use_regex):
    con = sqlite3.connect(DB)
    con.create_function("REGEXP", 2, regexp)
    cur = con.cursor()
    if use_regex:
        condition = f"headline regexp '{text_limit}' or summary regexp '{text_limit}'"
    else:
        condition = f"headline like '%{text_limit}%' or summary like '%{text_limit}%'"
    cur.execute(f"""select * from {TABLE_NAME} 
                    where publish_time > date('now', '-1 days') 
                      and ({condition})
                    order by publish_time desc""")
    data = cur.fetchall()
    con.commit()
    con.close()
    return data


def events_listener(event):
    if event.exception:
        print(f'Job {event.job_id} failed with error {event.exception} at {datetime.datetime.now()}')
    else:
        print(f'Job {event.job_id} finished running successfully at {datetime.datetime.now()}')


def run_all_jobs(scheduler):
    for job in scheduler.get_jobs():
        job.func()


def scrape():
    scheduler = BackgroundScheduler()
    soon = datetime.datetime.now() + datetime.timedelta(seconds=15)
    scheduler.add_job(scrape_bbc_news, 'interval', minutes=15, id='bbc_scraper', next_run_time=soon)
    scheduler.add_job(scrape_techcrunch_items, 'interval', minutes=15, id='techcrunch_scraper', next_run_time=soon)
    scheduler.add_job(scrape_ynet, 'interval', minutes=15, id='ynet_scraper', next_run_time=soon)
    scheduler.add_listener(events_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    scheduler.start()


if __name__ == '__main__':
    scrape()
    app.run(host='127.0.0.1', port=8080, threaded=True, debug=True)

from flask import Flask, render_template, url_for, request, jsonify
import sqlite3
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from collections import defaultdict
import datetime
from dateutil.parser import parse
from threading import Thread
from scrape_content import scrape_bbc_news, scrape_techcrunch_items, scrape_ynet, NewsItem, DB, TABLE_NAME


WEBSITES_ORDER = ['BBC', 'ynet', 'TechCrunch']


app = Flask(__name__)


@app.route('/')
def main():
    return render_template('base.html', data=get_data(), sites=WEBSITES_ORDER, get_date_for_show=get_date_for_show)


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_text = request.form['search']
        return render_template('base.html', data=get_data(search_text), sites=WEBSITES_ORDER, get_date_for_show=get_date_for_show)
    search_text = request.args.get('search')
    return jsonify(get_data(search_text, False))


def get_data(text_limit='', get_news_item_object=True):
    raw_data = get_raw_data(text_limit)
    news_items = defaultdict(list)
    for line in raw_data:
        if get_news_item_object:
            news_items[line[0]].append(NewsItem(*line))
        else:
            news_items[line[0]].append(NewsItem(*line).__dict__)
    if get_news_item_object:
        return {k: reserve_first_items_of_news_items_list(v, 8) for k, v in news_items.items()}
    return {k: reserve_first_items_of_list(v, 8) for k, v in news_items.items()}


def reserve_first_items_of_news_items_list(l, n_items):
    return sorted(l, key=lambda x: x.publish_time, reverse=True)[:n_items]


def reserve_first_items_of_list(l, n_items):
    return sorted(l, key=lambda x: x['publish_time'], reverse=True)[:n_items]


def get_raw_data(text_limit):
    con = sqlite3.connect(DB)
    cur = con.cursor()
    cur.execute(f"""select * from {TABLE_NAME} 
                    where publish_time > date('now', '-1 days') 
                        and (headline like '%{text_limit}%' or summary like '%{text_limit}%')
                    order by publish_time desc""")
    data = cur.fetchall()
    con.commit()
    con.close()
    return data


def get_date_for_show(dt_str):
    dt = parse(dt_str)
    return dt.strftime('%d.%m %H:%M')


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
    scheduler.add_job(scrape_bbc_news, 'interval', minutes=15, id='cnn_scraper')
    scheduler.add_job(scrape_techcrunch_items, 'interval', minutes=15, id='techcrunch_scraper')
    scheduler.add_job(scrape_ynet, 'interval', minutes=15, id='ynet_scraper')
    scheduler.add_listener(events_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
    first_run = Thread(target=run_all_jobs, args=(scheduler,))
    first_run.start()
    scheduler.start()


if __name__ == '__main__':
    scrape()
    app.run(host='127.0.0.1', port=8080, threaded=True, debug=True)

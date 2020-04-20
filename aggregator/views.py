from flask import Flask, render_template, url_for, request, jsonify
import sqlite3
from collections import defaultdict
import re
from aggregator import app
from .news import NewsItem, DB, TABLE_NAME


WEBSITES_ORDER = ['BBC', 'ynet', 'TechCrunch']


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
    print(DB)
    con = sqlite3.connect(DB)
    con.create_function("REGEXP", 2, regexp)
    cur = con.cursor()
    if use_regex:
        condition = f"headline regexp '{text_limit}' or summary regexp '{text_limit}'"
    else:
        condition = f"headline like '%{text_limit}%' or summary like '%{text_limit}%'"
    cur.execute(f"""select * from {TABLE_NAME} 
                    where publish_time > date('now', '-7 days') 
                      and ({condition})
                    order by publish_time desc""")
    data = cur.fetchall()
    con.commit()
    con.close()
    return data


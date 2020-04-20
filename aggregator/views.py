from flask import Flask, render_template, url_for, request, jsonify
import datetime
from collections import defaultdict
import re
from aggregator import app
from .models import NewsItem
from sqlalchemy import or_


@app.route('/')
def main():
    return render_template('home.html')


@app.route('/search')
def search():
    search_text = request.args.get('search')
    regex = request.args.get('regex', None)
    regex = True if regex == 'true' else False
    return jsonify(get_data(search_text, regex))


def get_data(text_limit, use_regex):
    if use_regex:
        matching_articles = NewsItem.query\
            .filter(NewsItem.publish_time > datetime.datetime.now() - datetime.timedelta(days=7))\
            .order_by(NewsItem.publish_time).all()[::-1]
        matching_articles = [article for article in matching_articles if re.compile(text_limit).search(article.summary) or re.compile(text_limit).search(article.headline)]
    else:
        matching_articles = NewsItem.query\
            .filter(or_(NewsItem.summary.contains(text_limit), NewsItem.headline.contains(text_limit)))\
            .filter(NewsItem.publish_time > datetime.datetime.now() - datetime.timedelta(days=7))\
            .order_by(NewsItem.publish_time).all()[::-1]
    news_items = defaultdict(list)
    for article in matching_articles:
        news_items[article.website].append(article.serialize())
    return {k: v[:8] for k, v in news_items.items()}

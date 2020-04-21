from flask import render_template, url_for, request, jsonify, redirect, flash
import datetime
from collections import defaultdict
import re
from aggregator import app, db, bcrypt
from .models import NewsItem, User
from sqlalchemy import or_
from flask_login import login_user, current_user, logout_user, login_required
from aggregator.forms import RegistrationForm, LoginForm


@app.route('/')
@app.route('/home')
def home():
    return render_template('news.html', inner_title='News Portal')


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


@app.route("/register", methods=['GET', 'POST'])
@app.route("/register-page", methods=['GET', 'POST'])
def register_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login_page'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
@app.route("/login-page", methods=['GET', 'POST']) # Use that so flask-security doesn't fuck you up
def login_page():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/account")
@login_required
def account():
    return render_template('account.html', title='Account')

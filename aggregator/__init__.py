from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SECRET_KEY'] = '9ed456ae10f7eb034612afd2a46790bf'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/site.db'
db = SQLAlchemy(app)


from aggregator import views

from flask import Flask

app = Flask(__name__)
app.config['SECRET_KEY'] = '9ed456ae10f7eb034612afd2a46790bf'

from aggregator import views
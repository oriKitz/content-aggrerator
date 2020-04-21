from flask import Flask, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_admin import Admin, helpers
from flask_security import Security, SQLAlchemyUserDatastore


app = Flask(__name__)
app.config['SECRET_KEY'] = '9ed456ae10f7eb034612afd2a46790bf'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db/site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
migrate = Migrate(app, db)
admin = Admin(app, name='aggregator', base_template='my_admin.html', template_mode='bootstrap3')

from .forms import LoginForm
from .models import User, NewsItem
from .utils import MyModelView

admin.add_view(MyModelView(User, db.session))
admin.add_view(MyModelView(NewsItem, db.session))
user_datastore = SQLAlchemyUserDatastore(db, User, role_model=None)
security = Security(app, user_datastore)

@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=helpers,
        get_url=url_for
    )

from aggregator import views

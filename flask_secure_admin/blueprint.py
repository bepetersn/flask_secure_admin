
import os, inspect
from itertools import zip_longest

from flask import Flask, request, url_for, abort, Blueprint
from flask_admin import Admin
from flask_admin import helpers as admin_helpers, AdminIndexView, expose
from flask_security import Security, login_required
from .secure_model_view import SecureModelView
from .security_sqlsoup_user_datastore import SQLSoupUserDataStore
from .str_representation import override___name___on_sqlsoup_model
from .templates import load_master_template
from .utils import encrypt_password

# Inspired by:
# https://flask-admin.readthedocs.io/en/latest/introduction/#using-flask-security


def on_user_change(form, model, is_created):
    model.password = encrypt_password(model.password)

class SecureAdminIndex(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        """ Default index, login is required. """
        return self.render('admin/index.html')


class SecureAdminBlueprint(Blueprint):

    """ Requires that a database with the 'users', 'roles', and
        'users_roles' tables exist. SQLSoup reference to this
        database should be set on app, as explained in `register`.
        There is a create.sql file present which can initialize
        these tables for you in a database of your creating.

        Additionally, the environment variables SECRET_KEY and
        SECURITY_PASSWORD_SALT must be set. There are additional
        SECURITY environment variables which may be overrided.

        Finally, at least a name must be passed in to initialize
        the blueprint.
        """

    DEFAULT_MODELS = ['users', 'roles']
    DEFAULT_VIEW_OPTIONS = [
        dict(on_model_change=on_user_change)
    ]

    def __init__(self, name=None, models=None, view_options=None):
        self.name = name
        assert self.name, "Admin instances must have a name value"
        self.models = models or []
        self.models.extend(self.DEFAULT_MODELS)
        self.view_options = view_options or []
        self.view_options.extend(self.DEFAULT_VIEW_OPTIONS)
        # Initialize the below as a best practice,
        # so they can be referenced before assignment
        self.admin = None
        self.security = None

        super(SecureAdminBlueprint, self).__init__(
            self.name, __name__, template_folder='templates')

    def register(self, app, options, first_registration=False):
        """ `app` should have a SQLSoup database set as its `db` attribute.
            We could easily support a regular SQLAlchemy db as well, but
            this is all we have for now. """

        # Secret key must be set in the environment.
        app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

        # Set config values for Flask-Security.
        # Security passowrd salt must be set in the environment.
        app.config['SECURITY_PASSWORD_HASH'] = \
            os.environ.get('SECURITY_PASSWORD_HASH', 'pbkdf2_sha512')
        app.config['SECURITY_PASSWORD_SALT'] = \
            os.environ['SECURITY_PASSWORD_SALT']
        app.config['SECURITY_REGISTERABLE'] = \
            os.environ.get('SECURITY_REGISTERABLE', False)

        self.admin = self.add_admin(app, app.db)
        self.security = self.add_security(app, app.db)

        @app.teardown_appcontext
        def shutdown_session(exception=None):
            """ Without this, SQLAlchemy pooling errors start to occur
                due to flask-security's usage of the database in tracking
                users. """
            app.db.session.remove()

        # Add stuff to flask-security templates that is needed by flask-admin
        @self.security.context_processor
        def security_context_processor():
            return dict(
                admin_base_template=self.admin.base_template,
                admin_view=self.admin.index_view,
                h=admin_helpers,
                get_url=url_for
            )
        load_master_template(app)

    def add_admin(self, app, db):

        # Add an admin at the /admin route,
        # with a CRUD view for users
        admin = Admin(app, name=self.name, template_mode='bootstrap3',
                            index_view=SecureAdminIndex())

        # Define relationship between these models;
        # this must happen before adding the model views
        # or the relationship won't be acknowledged
        db.users.relate('roles', db.roles,
                        secondary=db.users_roles._table)

        # Add auth views, and for each additional model specified
        # get the model from the database which must be set on app.
        for model_name, view_options_bag in zip_longest(
                self.models, self.view_options, fillvalue={}):
            model = getattr(db, model_name)
            model = override___name___on_sqlsoup_model(model)
            model_view = SecureModelView(model, db.session)
            for option_key, option_value in view_options_bag.items():
                setattr(model_view, option_key, option_value)
            admin.add_view(model_view)

        return admin

    def add_security(self, app, db):
        # Initialize flask-security
        user_datastore = SQLSoupUserDataStore(db, db.users, db.roles)
        return Security(app, user_datastore)

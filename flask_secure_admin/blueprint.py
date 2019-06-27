
import os, inspect
from flask import Flask, request, url_for, abort, Blueprint
from flask_admin import Admin
from flask_admin import helpers as admin_helpers, AdminIndexView, expose
from flask_security import Security, login_required
from .secure_model_view import SecureModelView
from .security_sqlsoup_user_datastore import SQLSoupUserDataStore
from .str_representation import override___name___on_sqlsoup_model
from .templates import load_master_template

# Inspired by:
# https://flask-admin.readthedocs.io/en/latest/introduction/#using-flask-security


class SecureAdminIndex(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        """ Default index, login is required. """
        return self.render('admin/index.html')


class SecureAdminBlueprint(Blueprint):

    """ Requires that a database with the 'users' and 'roles'
        table exists. SQLSoup reference to this database should
        be set on app, as explained in `register`. """

    def __init__(self, name=None, models=None):
        self.name = name
        self.models = models
        self.admin = None
        self.security = None
        super(SecureAdminBlueprint, self).__init__(
            self.name, __name__, template_folder='templates')

    def register(self, app, options, first_registration=False):
        """ `app` should have a SQLSoup database set as its `db` attribute.
            We could easily support a regular SQLAlchemy db as well, but
            this is all we have for now. """

        if self.name is None or self.models is None:
            assert False, "Set a name and models value before registering"

        # Secret key must be set in the environment.
        app.config['SECRET_KEY'] = os.environ['SECRET_KEY']

        # Set config values for Flask-Security.
        # Security passowrd salt must be set in the environment.
        app.config['SECURITY_PASSWORD_HASH'] = 'pbkdf2_sha512'
        app.config['SECURITY_PASSWORD_SALT'] = os.environ['SECURITY_PASSWORD_SALT']
        app.config['SECURITY_REGISTERABLE'] = False

        self.admin = self.add_admin(app, app.db, self.name, self.models)
        self.security = self.add_security(app, app.db)

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

    def add_admin(self, app, db, name, models):
        # Add an admin at the /admin route,
        # with a CRUD view for users
        admin = Admin(app, name=name, template_mode='bootstrap3',
                            index_view=SecureAdminIndex())
        # Add a view for users, and for each other model specified
        models.append('users')
        for model_name in models:
            model = getattr(db, model_name)
            model = override___name___on_sqlsoup_model(model)
            admin.add_view(SecureModelView(model, db.session))
        return admin

    def add_security(self, app, db):
        # Initialize flask-security
        user_datastore = SQLSoupUserDataStore(db, db.users, db.roles)
        return Security(app, user_datastore)

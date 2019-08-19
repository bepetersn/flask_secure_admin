
import os, re, subprocess
from itertools import zip_longest

from flask import Flask, request, url_for, abort, Blueprint, redirect
from flask_admin import Admin
from flask_admin import helpers as admin_helpers, AdminIndexView, expose
from flask_security import Security, login_required
from .secure_model_view import SecureModelView
from .security_sqlsoup_user_datastore import SQLSoupUserDataStore
from .str_representation import override___name___on_sqlsoup_model
from .templates import load_master_template
from .index import SecureDefaultIndex
from .utils import encrypt_password, create_initial_admin_user

# Inspired by:
# https://flask-admin.readthedocs.io/en/latest/introduction/#using-flask-security

def on_user_change(form, model, is_created):
    model.password = encrypt_password(model.password)


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

    def __init__(self, name=None, models=None,
                 view_options=None, index_url=None,
                 *args, **kwargs):
        self.app_name = name
        assert self.app_name, "Admin instances must have a name value"
        self.models = models or []
        self.models.extend(self.DEFAULT_MODELS)
        self.view_options = view_options or []
        self.view_options.extend(self.DEFAULT_VIEW_OPTIONS)

        # Initialize the below as a best practice,
        # so they can be referenced before assignment
        self.admin = None
        self.security = None

        super(SecureAdminBlueprint, self).__init__(
            'secure_admin', __name__, template_folder='templates',
            static_folder='static', static_url_path='/static',
            *args, **kwargs)

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

        self.admin = self.add_admin(app, app.db, options)
        self.security = self.add_security(app, app.db, options)

        self.bootstrap_database(app, app.db)

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
        super(SecureAdminBlueprint, self).register(
            app, options, first_registration)

    def get_index_view(self):
        """ Hook for overriding the admin's IndexView. """
        return SecureDefaultIndex()

    def on_before_add_layout_to_admin(self, admin, app, db, options):
        """ Hook for adding more views, etc., to the admin object.
            If adding views is done in this method, they will appear
            prior to the layout (on the left side of it). """
        return admin

    def on_after_add_layout_to_admin(self, admin, app, db, options):
        """ Hook for adding more views, etc., to the admin object.
            If adding views is done in this method, they will appear
            after the layout (on the right side of it). """
        return admin

    def add_layout_to_admin(self, admin, app, db, options):
        """ Add auth views, and for each additional model specified
            get the model from the database which must be set on app. """
        for model_name, view_options_bag in zip_longest(
                self.models, self.view_options, fillvalue={}):
            model = getattr(db, model_name)
            model = override___name___on_sqlsoup_model(model)
            DerviedModelViewCls = \
                type(f'Secure{model.__name__}View',
                     (SecureModelView,),
                     view_options_bag)
            model_view = DerviedModelViewCls(model, db.session)
            admin.add_view(model_view)
        return admin

    def bootstrap_database(self, app, db):
        # TODO: This only works if the psql command is available
        # and the database is a postgres database
        try:
            database_name = db._metadata._bind.url.database
            command_args = ['psql', database_name, '-c', "select * from users;"]
            try:
                completed = subprocess.run(command_args, capture_output=True)
            except TypeError:
                completed = subprocess.run(command_args, stdout=subprocess.PIPE)
            if re.search('\(0 rows\)', str(completed.stdout)):
                print('Detected first usage of admin.')
                print('Creating initial admin user...')
                create_initial_admin_user(app)
                print('You can now login with the credentials: \n'
                      'user: admin@example.com, password: password')
                print('Have fun!')
        except Exception:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print('Failed to bootstrap database!')
            print(exc_type, fname, exc_tb.tb_lineno)

    def add_admin(self, app, db, options):

        # Add an admin at the /admin route,
        # with a CRUD view for users
        admin = Admin(app, name=self.app_name, template_mode='bootstrap3',
                            index_view=self.get_index_view())

        # Define relationship between these models;
        # this must happen before adding the model views
        # or the relationship won't be acknowledged
        db.users.relate('roles', db.roles,
                        secondary=db.users_roles._table)

        admin = self.on_before_add_layout_to_admin(admin, app, db, options)
        admin = self.add_layout_to_admin(admin, app, db, options)
        admin = self.on_after_add_layout_to_admin(admin, app, db, options)

        return admin

    def add_security(self, app, db, options):
        # Initialize flask-security
        user_datastore = SQLSoupUserDataStore(db, db.users, db.roles)
        return Security(app, user_datastore)

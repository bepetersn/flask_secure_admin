# flask_secure_admin

My little bundling of flask-admin and flask-security. Drawn heavily from the flask-admin example repo, also integrating sqlsoup because when I made it I didn't want to declare any models. Could be adapted to work with flask-sqlalchemy, surely.

## Development

### Uploading the package

```sh
# Update setup.py version number

python setup.py sdist
twine upload dist/flask_secure_admin-x.x.x.tar.gz # use the last version created
```

## Usage

Run the following from a virtual environment:

    pipenv install flask-secure-admin  # Or use pip

Add the following python to your project:

```python
from sqlsoup import SQLSoup
from flask_secure_admin import SecureAdminBlueprint
app.db = SQLSoup(os.environ['DATABASE_URI'])
app.register_blueprint(SecureAdminBlueprint(
    name='Your Project Name',
    url_prefix='secure-admin'))
```

Add sqlsoup models to your admin view by passing a list of their names
as a third argument to `SecureAdminBlueprint`, and a list of view options
for customization of these model views as a fourth argument. For example:
```python
app.register_blueprint(SecureAdminBlueprint(
    name='Your Project Name',
    url_prefix='secure-admin',
    models=['videos', 'captions', 'languages'],
    view_options=[
        dict(
            can_create=False,
            form_overrides=dict(filename=FileUploadField)
        )
    ], {}, {}))
```

See https://flask-admin.readthedocs.io/en/latest/api/mod_contrib_sqla/#flask_admin.contrib.sqla.ModelView
and its parent class, https://flask-admin.readthedocs.io/en/latest/api/mod_model/#flask_admin.model.BaseModelView,
for a list of all configuration options.

### Database Setup

Last, run this to create necessary database tables in your database (PostgreSQL):

    # Turns into, for example: psql yourdatabase < /Users/you/.local/share/virtualenvs/env-aP3G_9r-/lib/python3.7/site-packages/flask_secure_admin/create.sql
    psql yourdatabase < $(dirname $(which pip))/../lib/$(python --version | sed 's/..$//' | sed 's/ //' | awk '{print tolower($0)}')/site-packages/flask_secure_admin/create.sql;    

This will create the tables: users, roles, & users_roles, so if you have any of those, this won't work.
In that case, you're probably best off making sure you have each of the fields required on users and roles.
See the create.sql file for reference.

This project is only setup to work automagically with a postgres database / the `psql` command available. See `SecureAdminBlueprint.bootstrap_database()` in `flask_secure_admin/base.py`. However, you can emulate what it does quickly by just running the following from a python shell, assuming the aforementioned `Flask` app setup:

```python
from yourapp import app
from flask_secure_admin.utils import create_initial_admin_user
create_initial_admin_user(app)
```

At this point, you're set! Run your app, there should now be a protected '/admin' route with a page shown for as many database tables as you have specified.


### Future Plans

I'd love to get this to work with Flask-SQLAlchemy / SQLAlchemy, but I don't have the time right now. Contributions are welcome!

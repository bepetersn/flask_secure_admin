
from jinja2 import Environment, PackageLoader, ChoiceLoader, select_autoescape

def get_loader():
    return PackageLoader('flask_secure_admin', 'templates')

def load_master_template(app):
    secure_admin_loader = get_loader()
    secure_admin_env = Environment(
        loader=PackageLoader('flask_secure_admin', 'templates'),
        autoescape=select_autoescape(['html'])
    )
    app_env = app.jinja_env

    source, filename, uptodate = \
        secure_admin_loader.get_source(secure_admin_env, 'admin/master.html')

    code = app_env.compile(source, 'master.html', filename)
    master_template = app_env.template_class.from_code(
        app_env, code, {}, uptodate)
    app_env.globals['secure_admin_master_template'] = master_template

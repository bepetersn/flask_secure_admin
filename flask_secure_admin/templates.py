
from jinja2 import Environment, PackageLoader, ChoiceLoader, select_autoescape

def get_loader():
    return PackageLoader('flask_secure_admin', 'templates')

def load_master_template(app):
    """
        Put a template object in the app's jinja environment
        called `secure_admin_master_template`, which points
        to secure_admin's 'master.html' template, a drop-in
        replacement for flask_admin's template of the same name.

        The whole reason for loading it directly into the
        jinja environment is that we want it to be able to
        be extended by users of this library, but typically
        that's not possible because it needs to be in a file
        of the same name in order for flask_admin to see it.
    """

    secure_admin_loader = get_loader()
    secure_admin_env = Environment(
        loader=secure_admin_loader,
        autoescape=select_autoescape(['html'])
    )
    app_env = app.jinja_env

    # Cherry-pick the underlying template source
    # from the "secure_admin" environment
    source, filename, uptodate = \
        secure_admin_loader.get_source(secure_admin_env, 'admin/master.html')

    # Compile the underlying template source inside the app's environment
    # (NOT the environment from which it originated!)
    # I suspect strongly that this breaks jinja's helpful feature
    # which allows templates to be updated without restarting the app, FYI
    code = app_env.compile(source, 'master.html', filename)
    master_template = app_env.template_class.from_code(
        app_env, code, {}, uptodate)

    # Put the template where we can use it
    app_env.globals['secure_admin_master_template'] = master_template

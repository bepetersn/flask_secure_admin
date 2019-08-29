
from flask import redirect, url_for, current_app
from flask_admin import AdminIndexView, expose
from flask_security import login_required

DEFAULT_INDEX_TEMPLATE = 'admin/index.html'

class SecureDefaultIndex(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        return self.render(DEFAULT_INDEX_TEMPLATE)


class SecureRedirectIndex(AdminIndexView):

    def __init__(self, *args, **kwargs):
        self.is_visible = lambda: False
        super(SecureRedirectIndex, self).__init__(*args, **kwargs)

    @expose('/')
    @login_required
    def index(self):
        """ Redirects to the first other view found. """
        admin = current_app.extensions['admin'][0]
        try:
            first_view = admin._views[1]
        except IndexError:
            first_view = None
        if first_view:
            first_view_index = f'{first_view.endpoint}.index_view'
            return redirect(url_for(first_view_index))
        else:
            return self.render(DEFAULT_INDEX_TEMPLATE)

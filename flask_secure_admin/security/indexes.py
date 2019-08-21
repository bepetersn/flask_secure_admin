
from flask import redirect
from flask_admin import AdminIndexView, expose
from flask_security import login_required

DEFAULT_INDEX_URL = '/admin'

class SecureDefaultIndex(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        return self.render('admin/index.html')


class SecureRedirectIndex(AdminIndexView):

    def __init__(self, index_url, *args, **kwargs):
        self.index_url = index_url
        super(SecureRedirectIndex, self).__init__(*args, **kwargs)

    @expose('/')
    @login_required
    def index(self):
        """ Allows redirecting to a sub-page as the index,
            when a value is passed for index_url which
            is not the default value. """
        if self.index_url and self.index_url != DEFAULT_INDEX_URL:
            self.is_visible = lambda: False
            return redirect(self.index_url)
        else:
            return self.render('admin/index.html')

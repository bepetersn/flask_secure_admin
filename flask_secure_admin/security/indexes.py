
from flask import redirect
from flask_admin import AdminIndexView, expose
from flask_security import login_required

DEFAULT_INDEX_ENDPOINT = 'admin.index'
DEFAULT_INDEX_TEMPLATE = 'admin/index.html'

class SecureDefaultIndex(AdminIndexView):
    @expose('/')
    @login_required
    def index(self):
        return self.render(DEFAULT_INDEX_TEMPLATE)


class SecureRedirectIndex(AdminIndexView):

    def __init__(self, index_endpoint, *args, **kwargs):
        self.index_endpoint = index_endpoint
        super(SecureRedirectIndex, self).__init__(*args, **kwargs)

    @expose('/')
    @login_required
    def index(self):
        """ Allows redirecting to a sub-page as the index,
            when a value is passed for index_endpoint which
            is not the default value. """
        if self.index_endpoint and \
                self.index_endpoint != DEFAULT_INDEX_ENDPOINT:
            self.is_visible = lambda: False
            return redirect(url_for(self.index_endpoint, _external=True))
        else:
            return self.render(DEFAULT_INDEX_TEMPLATE)

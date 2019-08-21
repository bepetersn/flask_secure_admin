
from flask import request, abort, redirect, url_for, current_app
from flask_admin.contrib import sqla
from flask_security import current_user

from .data import SUPER_ROLE

# Create customized model view class
class SecureModelView(sqla.ModelView):

    def __repr__(self):
        return f"<'{self.name}' ModelView>"

    def rebuild_views_respecting_access(self):
        # Rebuild edit & list views based on who is accessing them
        self._refresh_forms_cache()
        self._list_columns = self.get_list_columns()

    def has_one_accepted_role(self, user):
        return any(
            [current_user.has_role(r)
             for r in self.roles_accepted])

    def is_accessible(self):
        if (current_user.is_active and
                current_user.is_authenticated and
                self.has_one_accepted_role(current_user)):
            self.rebuild_views_respecting_access()
            return True
        else:
            user_ref = 'AnonymousUser' if \
                       current_user.is_anonymous else \
                       current_user.email
            current_app.logger.info(
                f"<User '{user_ref}'> unauthorized to "
                f'access {self}, not showing')
            return False

    def _handle_view(self, name, **kwargs):
        """
        Override builtin _handle_view in order to redirect users when a view is not accessible.
        """
        if not self.is_accessible():
            if current_user.is_authenticated:
                # permission denied
                abort(403)
            else:
                # login
                return redirect(url_for('security.login', next=request.url))

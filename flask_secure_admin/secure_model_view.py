
from flask import request, abort, redirect, url_for, current_app
from flask_admin.contrib import sqla
from flask_security import current_user

# Create customized model view class
class SecureModelView(sqla.ModelView):

    def __str__(self):
        return f"<'{self.name}' ModelView>"

    def is_accessible(self):
        if (current_user.is_active and
                current_user.is_authenticated and
                current_user.has_role('superuser')):
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

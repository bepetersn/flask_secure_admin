
from flask_admin.contrib.sqla.view import ModelView as SQLAModelView
from .data import SUPER_ROLE
from flask_security import current_user
from flask_admin.contrib.sqla.form import get_form as get_sqla_form


def scaffold_list_columns_respecting_roles(self):
    """ Respect a new view option, `role_only_columns`,
        in the list view. Must be a dictionary mapping
        between role names and columns which only users
        with this role are allowed to see. """
    columns = SQLAModelView.scaffold_list_columns(self)
    role_only_columns = self.role_only_columns or dict()
    super_only_columns = role_only_columns.get(SUPER_ROLE) or []
    if current_user and not current_user.has_role(SUPER_ROLE):
        columns = [c for c in columns if c not in super_only_columns]
    return columns


def scaffold_form_respecting_roles(self):
    """ Just like regular SQLAModelView `scaffold_form()`,
        except that we exclude `role_only_columns`
        if user does not have the expected role. """
    exclude = list(self.form_excluded_columns or [])
    role_only_columns = self.role_only_columns or dict()
    super_only_columns = role_only_columns.get(SUPER_ROLE) or []
    if current_user and not current_user.has_role(SUPER_ROLE):
        exclude.extend(role_only_columns)
    converter = self.model_form_converter(self.session, self)
    form_class = get_sqla_form(self.model, converter,
                               base_class=self.form_base_class,
                               only=self.form_columns,
                               exclude=exclude,
                               field_args=self.form_args,
                               ignore_hidden=self.ignore_hidden,
                               extra_fields=self.form_extra_fields)

    if self.inline_models:
        form_class = self.scaffold_inline_form_models(form_class)
    return form_class

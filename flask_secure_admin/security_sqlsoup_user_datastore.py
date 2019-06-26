
from flask import g
from flask_security import SQLAlchemyUserDatastore, RoleMixin, UserMixin


class SuperUserMixin(UserMixin):
    """ I don't have a need for less privileged users
        than superusers to be logged in. """
    @property
    def roles(self):
        return g.roles


class SQLSoupUserDataStore(SQLAlchemyUserDatastore):

    def __init__(self, db, user_model, role_model):
        # You can query directly on the model with sqlsoup
        user_model.query = user_model
        role_model.query = role_model
        SQLAlchemyUserDatastore.__init__(self, db, user_model, role_model)

    def put(self, model):
        # Not sure why they try to add without checking
        if model not in self.db.session:
            self.db.session.add(model)
        return model

    def add_mixin(self, result, mixin_cls):
        self._extend_instance(result, mixin_cls)
        return result

    def get_user(self, identifier):
        user = SQLAlchemyUserDatastore.get_user(self, identifier)
        if user is None: return None
        return self.add_mixin(
            user, SuperUserMixin
        )

    def find_user(self, **kwargs):
        user = SQLAlchemyUserDatastore.find_user(self, **kwargs)
        if user is None: return None
        return self.add_mixin(
            user, SuperUserMixin
        )

    def find_role(self, role):
        user = SQLAlchemyUserDatastore.find_user(self, role)
        if user is None: return None
        return self.add_mixin(
            user, RoleMixin
        )

    @staticmethod
    def _extend_instance(obj, cls):
        """Apply mixins to a class instance after creation """
        base_cls = obj.__class__
        base_cls_name = obj.__class__.__name__
        obj.__class__ = type(base_cls_name, (base_cls, cls), {})


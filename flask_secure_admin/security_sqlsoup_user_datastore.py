
# from flask import g
from funcy import collecting
from flask_security import SQLAlchemyUserDatastore, RoleMixin, UserMixin

def _wrap_user(user):
    return None if user is None else \
        _extend_instance(user, UserMixin)

def _extend_instance(obj, cls):
    """Apply mixins to a class instance after creation """
    base_cls = obj.__class__
    base_cls_name = obj.__class__.__name__
    obj.__class__ = type(base_cls_name, (base_cls, cls), {})
    return obj


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

    def get_user(self, identifier):
        return _wrap_user(
            SQLAlchemyUserDatastore.get_user(self, identifier)
        )

    def find_user(self, **kwargs):
        return _wrap_user(
            SQLAlchemyUserDatastore.find_user(self, **kwargs)
        )

    def find_role(self, role):
        return _extend_instance(
            SQLAlchemyUserDatastore.find_role(self, role),
            RoleMixin
        )

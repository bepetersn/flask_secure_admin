
from funcy import collecting
from flask_security import SQLAlchemyUserDatastore, RoleMixin, UserMixin

from .utils import _extend_instance

def _wrap_user(user):
    return None if user is None else \
        _extend_instance(user, UserMixin)

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

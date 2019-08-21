
import re

SQLSOUP_STR_REGEX = 'Mapped(.*)'

def override___name___on_sqlsoup_model(model):
    def _new__name__():
        str_representation = model.__name__
        match = re.match(SQLSOUP_STR_REGEX, str_representation)
        if match:
            return match.group(1)
        else:
            return str_representation
    model.__name__ = _new__name__()
    return model

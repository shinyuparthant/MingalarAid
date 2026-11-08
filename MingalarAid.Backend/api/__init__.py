from api.admin_api import register_admin_api
from api.auth_api import register_auth_api
from api.public_api import register_public_api


def register_routes(app):
    register_public_api(app)
    register_auth_api(app)
    register_admin_api(app)

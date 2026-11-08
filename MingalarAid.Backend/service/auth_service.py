from werkzeug.security import check_password_hash

from dataaccess import user_repository


def authenticate(username, password, required_role=None):
    user = user_repository.find_by_username(username.strip(), required_role)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None

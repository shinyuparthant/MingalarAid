from flask import Flask

from api import register_routes
from config import FRONTEND_DIR, SECRET_KEY
from dataaccess.database import initialize_database


def create_app():
    app = Flask(
        __name__,
        template_folder=str(FRONTEND_DIR / "templates"),
        static_folder=str(FRONTEND_DIR / "static"),
        static_url_path="/static",
    )
    app.secret_key = SECRET_KEY
    initialize_database()
    register_routes(app)
    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)

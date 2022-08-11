import os

from flask import Flask
from flask_cors import CORS


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)

    # Attempting to allow the React app to hit these APIs on the dev port
    # CORS at a high level to even make requests to the server
    # and supports_credentials so that we can submit the cookies
    CORS(app, supports_credentials=True)

    print(f'This is the flask_env: {os.getenv("FLASK_ENV")}')
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'webshopper.sqlite')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Adding database init
    from . import db
    db.init_app(app)

    # Adding auth registration
    from . import auth
    app.register_blueprint(auth.bp)

    # Adding non-auth endpoints
    from . import location
    app.register_blueprint(location.bp)

    from . import products
    app.register_blueprint(products.bp)

    from . import recipes
    app.register_blueprint(recipes.bp)

    return app
import os

from flask import Flask, render_template


def page_not_found(e):
  return render_template('not_found.html'), 404


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'data.sqlite'),
    )
    app.register_error_handler(404, page_not_found)

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
        print(app.config["DATABASE"])
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import db
    db.init_app(app)

    from . import reference
    app.register_blueprint(reference.bp)
    
    return app

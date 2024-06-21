from robot_cleaner import config
from robot_cleaner.app import app


if __name__ == "__main__":
    app.run(debug=config.IS_DEVELOPMENT, port=5000)

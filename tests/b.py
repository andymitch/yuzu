from flask import Flask

def run_api(data):
    app = Flask('yuzu')
    @app.route("/")
    def hello_world():
        return data
    app.run(port=8000)
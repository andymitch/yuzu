from flask import Flask

def run_api(trader):
    app = Flask('yuzu')

    @app.route("/")
    def get_data():
        return trader.data.to_json()

    app.run(port=8000)
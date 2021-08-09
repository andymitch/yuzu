def run_api(trader):
    from flask import Flask
    app = Flask('yuzu')

    @app.route("/")
    def hello_world():
        return trader.data.to_json()

    app.run(port=8000)
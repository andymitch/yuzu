from flask import Flask, send_from_directory
import os

app = Flask('yaza')

@app.route("/")
def hello():
    return 'hello!'

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

app.run(host='0.0.0.0', port=5000)
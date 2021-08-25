from flask import Flask, send_from_directory, render_template
import os

app = Flask(__name__,template_folder='template')

@app.route("/")
def hello():
    return render_template('hello.html')

app.run(host='0.0.0.0', port=5000, debug=True)
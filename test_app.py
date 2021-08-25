import flask

app = flask.Flask('yaza')

@app.route("/")
def hello():
    return 'hello!'

from gevent.pywsgi import WSGIServer
http_server = WSGIServer(('', 5005), app)
http_server.serve_forever()
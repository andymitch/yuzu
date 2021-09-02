from flask import Flask


ui = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="icon" type="image/png" href="https://andymitch.github.io/yuzu-ghost-icon.png">
    <title>Yuzu</title>
</head>
<body>
    <h1>Hello!</h1>
</body>
</html>
'''

app = Flask(__name__)

@app.route("/")
def hello():
    return ui

app.run(host='0.0.0.0', port=5000, debug=True)

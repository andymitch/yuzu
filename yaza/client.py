def client_app(balance: dict, plot: str) -> str:
    balance = '<ul>' + "".join([f'<li>{k}: {v}<li>' for k,v in balance.items()]) + '</ul>'
    top = '''
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta http-equiv="X-UA-Compatible" content="IE=edge">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Yuzu</title>
        </head>
        <body style="background-color: black; display: flex; flex-direction: column; align-items: center; justify-content: center;">
    '''
    bottom = '''
        </body>
        </html>
    '''
    return top + balance + plot + bottom

def page_not_found() -> str:
    return '<h1>Oh no, this page does not exist!</h1>', 404
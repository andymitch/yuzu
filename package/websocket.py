from websocket import WebSocketApp
import datetime, json


class WebSocket(WebSocketApp):
    def __init__(
        self,
        url,
        header=None,
        on_open=None,
        on_open_send_msg=None,
        on_message=None,
        on_error=None,
        on_close=None,
        on_ping=None,
        on_pong=None,
        on_cont_message=None,
        keep_running=True,
        get_mask_key=None,
        cookie=None,
        subprotocols=None,
        on_data=None,
    ):
        super().__init__(
            url,
            header=header,
            on_open=self.on_open(url, on_open_send_msg) if not on_open else on_open,
            on_message=lambda ws, msg: on_message(ws, json.loads(msg)),
            on_error=lambda ws, err: print(f"[{url}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) {err}") if not on_error else on_error,
            on_close=lambda ws: print(f"[{url}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket closed") if not on_close else on_close,
            on_ping=on_ping,
            on_pong=on_pong,
            on_cont_message=on_cont_message,
            keep_running=keep_running,
            get_mask_key=get_mask_key,
            cookie=cookie,
            subprotocols=subprotocols,
            on_data=on_data,
        )

    def on_open(self, url, on_open_send_msg):
        if on_open_send_msg:
            self.send(on_open_send_msg)
        print(f"[{url}] ({datetime.datetime.now().isoformat(' ', 'seconds')}) websocket opened")

    @override
    def run_forever(
        self,
        sockopt=None,
        sslopt=None,
        ping_interval=0,
        ping_timeout=None,
        ping_payload="",
        http_proxy_host=None,
        http_proxy_port=None,
        http_no_proxy=None,
        http_proxy_auth=None,
        skip_utf8_validation=False,
        host=None,
        origin=None,
        dispatcher=None,
        suppress_origin=False,
        proxy_type=None,
    ):
        while True:
            return super().run_forever(
                sockopt=sockopt,
                sslopt=sslopt,
                ping_interval=ping_interval,
                ping_timeout=ping_timeout,
                ping_payload=ping_payload,
                http_proxy_host=http_proxy_host,
                http_proxy_port=http_proxy_port,
                http_no_proxy=http_no_proxy,
                http_proxy_auth=http_proxy_auth,
                skip_utf8_validation=skip_utf8_validation,
                host=host,
                origin=origin,
                dispatcher=dispatcher,
                suppress_origin=suppress_origin,
                proxy_type=proxy_type,
            )

# TODO: might be easier just to not inherit and manage ws itself
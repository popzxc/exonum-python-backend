import tornado.concurrent
import tornado.ioloop
import tornado.web
import tornado.platform.asyncio
import tornado.httpclient

# Pylint isn't a friend of Tornado as it seems
# pylint: disable=abstract-method


class _ReqHandler(tornado.web.RequestHandler):
    async def get(self) -> None:
        """Get handler."""
        self.write({"message": "hello world!"})


class RuntimeApi:
    """Python Runtime API implementation."""

    def __init__(self, port: int):
        self._app = tornado.web.Application([(r"/", _ReqHandler)])

        self._app.listen(port)

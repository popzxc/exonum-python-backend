"""Runtime API."""

# Base API

import abc

# Runtime API

import tornado.concurrent
import tornado.ioloop
import tornado.web
import tornado.platform.asyncio
import tornado.httpclient

# Pylint isn't a friend of Tornado as it seems
# pylint: disable=abstract-method

# class EndpointHandler(metaclass=abc.ABCMeta):
#     @abc.abstractmethod
#     def get(self, service, )


class _ReqHandler(tornado.web.RequestHandler):
    async def get(self) -> None:
        """Get handler."""
        query = self.request.query

        print(query)
        self.write({"message": "hello world!"})


class RuntimeApi:
    """Python Runtime API implementation."""

    def __init__(self, port: int):
        self._app = tornado.web.Application([(r"/", _ReqHandler)])

        self._app.listen(port)

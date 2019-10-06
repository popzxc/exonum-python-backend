"""Runtime API."""

import abc
from typing import NamedTuple, Any, Dict, List, Tuple, Awaitable

import http
import json

# import os


import tornado.concurrent
import tornado.ioloop
import tornado.web
import tornado.platform.asyncio
import tornado.httpclient

from tornado.escape import json_encode, json_decode

from exonum_runtime.merkledb.types import Snapshot


class ServiceApiContext(NamedTuple):
    """Configuration of the API"""

    snapshot: Snapshot
    instance_name: str


# Pylint isn't a friend of Tornado as it seems
# pylint: disable=abstract-method


def _call_method(method: Any, args: Tuple[Any, ...]) -> Dict[Any, Any]:
    if not method:
        raise tornado.web.HTTPError(http.client.METHOD_NOT_ALLOWED)

    try:
        result = method(*args)

    except Exception:  # pylint: disable=broad-except
        raise tornado.web.HTTPError(http.client.INTERNAL_SERVER_ERROR)

    if result is None:
        raise tornado.web.HTTPError(http.client.BAD_REQUEST)

    if not isinstance(result, dict):
        raise tornado.web.HTTPError(http.client.INTERNAL_SERVER_ERROR)

    return result


class ServiceApi(metaclass=abc.ABCMeta):
    r"""Base class for service APIs.

    Classes that inherit `ServiceApi` should implement two methods: `public_endpoints` and `private_endpoints`.
    The only difference between those two is that the first should provide a public interface which can
    be accessed by everybody, and the second should provide an administrative interface.

    Those methods should return a description of api for the service in the following format:

    >>>
    {
        r"endpoint/": {
            "http_method_name": handler_function
        }
    }

    For example:

    >>>
    {
        r"/": {
            "get": main_get,
            "post": main_post,
        },
        r"/info/(\d+)": {
            "get": info_get,
        }
    }

    Handlers are async functions which return either a `dict` (in case of successfull API call), or `None`
    (if API call cannot be executed). If `dict` was returned, the status code of response will be OK and
    response will contain returned value as JSON. Otherwise, response status code will be BAD_REQUEST.

    If service was able to process the API request, but however it turned out to be erroneous, it's recommended
    to return a dict like `{"error": "description"}`.

    Types of HTTP methods that are currently supported: "get", "post", "put", "delete".
    For "get" and "delete" methods your handler should accept at least one argument of type `ServiceApiContext`.
    For "post" and "put" methods your handler should accept at least two arguments: `ServiceApiContext` and dict
    value of deserialized `json` from request payload.

    If endpoint contains variables (like `r"/info/(\d+)"` in the example above), those parameters will be passed
    after the mandatory arguments defined above.

    So, the expected signature for POST method of "/" endpoint from the example above would be

    >>> async def main_post(context: ServiceApiContext, payload: Dict[str, Any]) -> Dict[Any, Any]

    and for GET method of "/info/(\d+)" endpoint it would be:

    >>> async def info_get(context: ServiceApiContext, query_string_parameter: str) -> Dict[Any, Any]
    """

    @abc.abstractmethod
    def public_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Provides an public API interface of the service."""

    @abc.abstractmethod
    def private_endpoints(self) -> Dict[str, Dict[str, Any]]:
        """Provides an public API interface of the service."""

    @classmethod
    def _build_endpoint_handler(cls, context: ServiceApiContext, handlers: Dict[str, Any]) -> type:
        for key in handlers:
            if key.lower() not in ["get", "post", "put", "delete"]:
                # TODO write a log warning about incorrect key.
                pass

        class _EndpointHandler(tornado.web.RequestHandler):
            def _parse_json_body(self) -> Dict[Any, Any]:
                if self.request.headers["Content-Type"] != "application/json":
                    # Only json content-type are acceptable for post/put requests.
                    raise tornado.web.HTTPError(http.client.BAD_REQUEST)

                try:
                    data = json_decode(self.request.body)
                except json.decoder.JSONDecodeError:
                    raise tornado.web.HTTPError(http.client.BAD_REQUEST)

                return data

            def get(self, *args: Any) -> None:
                """Wrapper of the get request."""

                if "get" not in handlers:
                    raise tornado.web.HTTPError(http.client.METHOD_NOT_ALLOWED)

                result = _call_method(handlers.get("get"), (context, *args))

                self.write(json_encode(result))

            def delete(self, *args: Any) -> None:
                """Wrapper of the delete request."""

                if "delete" not in handlers:
                    raise tornado.web.HTTPError(http.client.METHOD_NOT_ALLOWED)

                result = _call_method(handlers.get("delete"), (context, *args))

                self.write(json_encode(result))

            def post(self, *args: Any) -> None:
                """Wrapper of the post request."""
                if "post" not in handlers:
                    raise tornado.web.HTTPError(http.client.METHOD_NOT_ALLOWED)

                data = self._parse_json_body()
                result = _call_method(handlers.get("post"), (context, data, *args))

                self.write(json_encode(result))

            def put(self, *args: Any) -> None:
                """Wrapper of the post request."""
                if "put" not in handlers:
                    raise tornado.web.HTTPError(http.client.METHOD_NOT_ALLOWED)

                data = self._parse_json_body()
                result = _call_method(handlers.get("put"), (context, data, *args))

                self.write(json_encode(result))

        return _EndpointHandler

    @classmethod
    def _into_application_config(
        cls, context: ServiceApiContext, config: Dict[str, Dict[str, Any]]
    ) -> List[Tuple[str, type]]:
        return [(endpoint, cls._build_endpoint_handler(context, handler)) for (endpoint, handler) in config.items()]

    def start(self, context: ServiceApiContext, public_port: int, private_port: int) -> None:
        """Starts the service API."""
        # Type check ignored in 2 lines because seems that tornado has incorrect type signature

        public_api_routes = self._into_application_config(context, self.public_endpoints())
        public_api = tornado.web.Application(public_api_routes)  # type: ignore
        public_api_server = public_api.listen(public_port)

        private_api_routes = self._into_application_config(context, self.private_endpoints())
        private_api = tornado.web.Application(private_api_routes)  # type: ignore
        private_api_server = private_api.listen(private_port)

        # `start` is somewhat `__init__`
        # pylint: disable=attribute-defined-outside-init
        self._public_api = public_api_server
        self._private_api = private_api_server

    async def stop(self) -> Tuple[Awaitable[None], Awaitable[None]]:
        """Stops the api. Returns two awaitable object correspoinding to
        coroutines of stopping the servers."""

        self._public_api.stop()
        self._private_api.stop()

        public_closed = self._public_api.close_all_connections()
        private_closed = self._private_api.close_all_connections()

        return (public_closed, private_closed)

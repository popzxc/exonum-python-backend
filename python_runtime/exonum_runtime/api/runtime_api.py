"""Runtime API."""

from typing import NamedTuple, List, Dict
import http
import os


import tornado.concurrent
import tornado.ioloop
import tornado.web
import tornado.platform.asyncio
import tornado.httpclient
from tornado.escape import json_encode

from exonum_runtime.crypto import Hash


class RuntimeApiConfig(NamedTuple):
    """Configuration of the API"""

    artifact_wheels_path: str


# Pylint isn't a friend of Tornado as it seems
# pylint: disable=abstract-method


class _State(tornado.web.RequestHandler):
    async def get(self) -> None:
        """State handler."""

        # TODO provide more helpful information
        self.write({"state": "operating"})


class _Artifact(tornado.web.RequestHandler):
    # pylint: disable=attribute-defined-outside-init
    def initialize(self, config: RuntimeApiConfig) -> None:
        """Store the runtime."""
        self._config = config

    def _get_deployables(self) -> List[str]:
        return os.listdir(self._config.artifact_wheels_path)

    async def get(self) -> None:
        """Gets the list of artifacts available to deploy."""
        deployable_artifacts = self._get_deployables()

        response = json_encode({"deployable": deployable_artifacts})

        self.write(response)

    async def post(self) -> None:
        """Post an artifact into the list of deployable."""

        # Check that "artifacts" key is set
        if not self.request.files.get("artifacts"):
            raise tornado.web.HTTPError(
                http.client.BAD_REQUEST, "No files in request. Ensure that you send files within 'artifact' request key"
            )

        already_uploaded = self._get_deployables()

        # Check that it's not re-uploading and file extension is acceptable
        accepted_exts = [".tar.gz", ".zip", ".whl"]
        for uploaded in self.request.files["artifacts"]:
            if uploaded.filename in already_uploaded:
                raise tornado.web.HTTPError(
                    http.client.BAD_REQUEST, f"Artifact {uploaded.filename} is already uploaded"
                )

            correct_ext = False
            for ext in accepted_exts:
                if uploaded.filename.endswith(ext):
                    correct_ext = True
                    break

            if not correct_ext:
                raise tornado.web.HTTPError(
                    http.client.BAD_REQUEST, f"Artifact {uploaded.filename} has incorrect extension"
                )

        # Save the files (we're doing it only after checking that request is completely valid)

        response: Dict[str, str] = dict()
        for uploaded in self.request.files["artifacts"]:
            response[uploaded.filename] = Hash.hash_data(uploaded.body).hex()

            file_path = os.path.join(self._config.artifact_wheels_path, uploaded.filename)

            with open(file_path, "wb") as output:
                output.write(uploaded.body)

        self.write(response)


class RuntimeApi:
    """Python Runtime API implementation."""

    def __init__(self, port: int, config: RuntimeApiConfig):
        self._config = config

        self._app = tornado.web.Application(
            [(r"/", _State, dict(config=config)), (r"/artifacts", _Artifact, dict(config=config))]
        )

        self._app.listen(port)

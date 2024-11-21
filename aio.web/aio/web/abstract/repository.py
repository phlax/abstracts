
import pathlib
import re
from functools import cached_property

import yaml

from aiohttp import web

import abstracts

from aio.web import exceptions, interface


@abstracts.implementer(interface.IRepositoryRequest)
class ARepositoryRequest(metaclass=abstracts.Abstraction):

    def __init__(self, url, config, request):
        self._url = url
        self.config = config
        self.request = request

    @property
    def requested_repo(self):
        return (
            f"{self.request.match_info['owner']}"
            f"/{self.request.match_info['repo']}")

    @property
    def url(self) -> str:
        return f"https://{self._url}/{self.requested_repo}/{self.path}"

    @property
    def path(self):
        return self.matched["path"]

    @property
    def sha(self):
        return self.matched["sha"]

    @cached_property
    def matched(self) -> dict:
        for repo in self.config:
            if not re.match(repo, self.requested_repo):
                continue

            for path, sha in self.config[repo].items():
                if path == self.request.match_info["extra"]:
                    return dict(path=path, sha=sha)
        return {}

    @property  # type: ignore
    @abstracts.interfacemethod
    def downloader_class(self):
        raise NotImplementedError

    async def fetch(self):
        content = await self.downloader_class(self.url, self.sha).download()
        response = web.Response(body=content)
        response.headers["cache-control"] = "max-age=31536000"
        return response

    def match(self):
        if not self.matched:
            raise exceptions.MatchError()
        return self


@abstracts.implementer(interface.IRepositoryMirrors)
class ARepositoryMirrors(metaclass=abstracts.Abstraction):

    def __init__(self, config_path):
        self.config_path = config_path

    @cached_property
    def config(self):
        return yaml.safe_load(pathlib.Path(self.config_path).read_text())

    @property  # type: ignore
    @abstracts.interfacemethod
    def request_class(self):
        raise NotImplementedError

    async def match(self, request):
        host = request.match_info['host']
        if host not in self.config:
            raise exceptions.MatchError()
        upstream_request = self.request_class(host, self.config[host], request)
        return upstream_request.match()

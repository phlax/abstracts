
from aiohttp import web

import abstracts


class IDownloader(metaclass=abstracts.Interface):

    @abstracts.interfacemethod
    async def download(self) -> web.Response:
        """Download content from the interwebs."""
        raise NotImplementedError


class IChecksumDownloader(IDownloader, metaclass=abstracts.Interface):

    @abstracts.interfacemethod
    async def checksum(self, content: bytes) -> bool:
        """Checksum some content."""
        raise NotImplementedError


class IRepositoryRequest(metaclass=abstracts.Interface):
    pass


class IRepositoryMirrors(metaclass=abstracts.Interface):
    pass

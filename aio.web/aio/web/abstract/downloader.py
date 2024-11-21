
import hashlib

import aiohttp

import abstracts

from aio.web import exceptions, interface


@abstracts.implementer(interface.IDownloader)
class ADownloader(metaclass=abstracts.Abstraction):

    def __init__(self, url: str) -> None:
        self.url = url

    async def download(self) -> bytes:
        """Download content from the interwebs."""
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as resp:
                return await resp.content.read()


@abstracts.implementer(interface.IChecksumDownloader)
class AChecksumDownloader(ADownloader, metaclass=abstracts.Abstraction):

    def __init__(self, url: str, sha: str) -> None:
        super().__init__(url)
        self.sha = sha

    async def checksum(self, content: bytes) -> None:
        """Download content from the interwebs."""
        # do this in a thread
        m = hashlib.sha256()
        m.update(content)
        if m.digest().hex() != self.sha:
            raise exceptions.ChecksumError(
                f"Bad checksum, {m.digest().hex()}, expected {self.sha}")

    async def download(self) -> bytes:
        content = await super().download()
        await self.checksum(content)
        return content

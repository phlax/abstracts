
import asyncio
import pathlib
import sys
from functools import cached_property

import aiohttp

from aio.core.functional import async_property
from aio.run import runner


class ContentFromPath:

    def __init__(self, path):
        self._path = path

    @cached_property
    def path(self):
        if self.path_type == "fs":
            return pathlib.Path(self._path)
        return self._path

    @cached_property
    def path_type(self):
        if self._path.startswith("http://"):
            return "http"
        if self._path.startswith("https://"):
            return "https"
        return "fs"

    def __await__(self):
        return self.fetch().__await__()

    async def fetch(self):
        if self.path_type == "fs":
            return self.path.read_text()
        async with aiohttp.ClientSession() as session:
            response = await session.get(self.path)
            return await response.read()


class DecolorizeRunner(runner.Runner):

    @async_property(cache=True)
    async def input(self):
        if self.args.input:
            return await ContentFromPath(self.args.input)
        reader = await self.reader
        incoming = await reader.read()
        return incoming.decode()

    @async_property(cache=True)
    async def reader(self):
        await self.loop.connect_read_pipe(
            lambda: self.stream_protocol,
            sys.stdin)
        return self.stream_reader

    @cached_property
    def stream_protocol(self) -> asyncio.StreamReaderProtocol:
        return asyncio.StreamReaderProtocol(self.stream_reader)

    @cached_property
    def stream_reader(self) -> asyncio.StreamReader:
        return asyncio.StreamReader()

    def add_arguments(self, parser):
        parser.add_argument("input", nargs="?", default="")
        parser.add_argument("-o", "--output")
        super().add_arguments(parser)

    async def decolorize(self, incoming):
        proc = await asyncio.create_subprocess_exec(
            "sed", "-r", "s/[[:cntrl:]]\[([0-9]{1,3};)*[0-9]{1,3}m//g",
            stdin=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE)
        print((await proc.communicate(incoming))[0].decode())

    async def run(self):
        await self.decolorize(await self.input)

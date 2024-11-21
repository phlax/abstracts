
import asyncio
import logging
import os
import pathlib
import shutil
import tempfile
from functools import cached_property
from typing import Optional

from . import exceptions

logger = logging.getLogger(__name__)


class TarMount:

    def __init__(
            self,
            archive: str | os.PathLike,
            path: Optional[str | os.PathLike] = None) -> None:
        self._archive = archive
        self._path = path

    async def __aenter__(self) -> pathlib.Path:
        try:
            await self.mount()
        except exceptions.TarMountError:
            await self.cleanup()
            raise
        return self.path

    async def __aexit__(self, x, y, z) -> None:
        await self.unmount()

    @cached_property
    def archive(self) -> pathlib.Path:
        return pathlib.Path(self._archive)

    @property
    def mount_cmd(self) -> str:
        return f"{self.ratarmount_path} {self.archive} {self.path}"

    @cached_property
    def path(self) -> pathlib.Path:
        if self._path:
            return pathlib.Path(self._path)
        return pathlib.Path(self.tempdir.name)

    @cached_property
    def tempdir(self) -> tempfile.TemporaryDirectory:
        return tempfile.TemporaryDirectory()

    @property
    def ratarmount_path(self) -> str:
        if cmd_path := shutil.which("ratarmount"):
            return cmd_path
        raise exceptions.TarMountError("Unable to find ratarmount command")

    @property
    def unmount_cmd(self):
        return f"{self.ratarmount_path} -u {self.path}"

    async def cleanup(self):
        if "tempdir" in self.__dict__:
            self.tempdir.cleanup()
            del self.__dict__["tempdir"]

    async def exec(self, cmd):
        proc = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        stdout, stderr = await proc.communicate()
        if stdout:
            print(f'{stdout.decode()}')
        if stderr:
            print(f'{stderr.decode()}')
        return proc.returncode

    async def mount(self):
        logger.info(f"Mounting tar: {self.path}")
        if await self.exec(self.mount_cmd):
            raise exceptions.TarMountError("Error mounting tarfile")

    async def unmount(self):
        logger.info(f"Unmounting tar: {self.path}")
        try:
            if await self.exec(self.unmount_cmd):
                raise exceptions.TarUnmountError("Error unmounting tarfile")
        finally:
            await self.cleanup()

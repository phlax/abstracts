
import sys
from typing import Any, Awaitable, Callable, TextIO, Type

import abstracts

from aio.core import pipe


class IBazelProcessProtocol(
        pipe.IProcessProtocol,
        metaclass=abstracts.Interface):

    # TODO: copy this to aio.core.pipe.interface and fix type
    @abstracts.interfacemethod
    async def process(self, request: Any) -> Any:
        """Process incoming items."""
        raise NotImplementedError


class IBazelWorker(metaclass=abstracts.Interface):

    @property  # type:ignore
    @abstracts.interfacemethod
    def processor_class(self) -> Type["IBazelWorkerProcessor"]:
        raise NotImplementedError

    @property  # type:ignore
    @abstracts.interfacemethod
    def protocol_class(self) -> Type["IBazelProcessProtocol"]:
        raise NotImplementedError


class IBazelWorkerProcessor(
        pipe.IStdinStdoutProcessor,
        metaclass=abstracts.Interface):

    # TODO: copy this to aio.core.pipe.interface and fix type
    @abstracts.interfacemethod
    def __init__(
            self,
            protocol: Callable[
                ["IBazelWorkerProcessor"],
                Awaitable[IBazelProcessProtocol]],
            stdin: TextIO = sys.stdin,
            stdout: TextIO = sys.stdout,
            log: Callable[[str], None] = None) -> None:
        raise NotImplementedError

    # TODO: copy this to aio.core.pipe.interface and fix type
    @abstracts.interfacemethod
    def __call__(self, *args) -> Any:
        raise NotImplementedError


import pytest

from aio.api.bazel import interface


@pytest.mark.parametrize(
    "interface",
    [interface.IBazelProcessProtocol,
     interface.IBazelWorker,
     interface.IBazelWorkerProcessor])
async def test_interfaces(iface, interface):
    await iface(interface).check()

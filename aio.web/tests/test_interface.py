
import pytest

from aio import web


@pytest.mark.parametrize(
    "interface",
    [web.IDownloader,
     web.IChecksumDownloader])
async def test_interfaces(iface, interface):
    await iface(interface).check()

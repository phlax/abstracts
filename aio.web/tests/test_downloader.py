
from aio.web import abstract, downloader


def test_downloader_constructor(patches):
    args = tuple(f"ARG{i}" for i in range(0, 3))
    kwargs = {f"K{i}": f"V{i}" for i in range(0, 3)}
    patched = patches(
        "abstract.ADownloader.__init__",
        prefix="aio.web.downloader")

    with patched as (m_super, ):
        m_super.return_value = None
        dl = downloader.Downloader(*args, **kwargs)

    assert isinstance(dl, abstract.ADownloader)
    assert (
        m_super.call_args
        == [args, kwargs])


def test_checksum_downloader_constructor(patches):
    args = tuple(f"ARG{i}" for i in range(0, 3))
    kwargs = {f"K{i}": f"V{i}" for i in range(0, 3)}
    patched = patches(
        "abstract.AChecksumDownloader.__init__",
        prefix="aio.web.downloader")

    with patched as (m_super, ):
        m_super.return_value = None
        dl = downloader.ChecksumDownloader(*args, **kwargs)

    assert isinstance(dl, abstract.AChecksumDownloader)
    assert (
        m_super.call_args
        == [args, kwargs])

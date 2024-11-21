
import abstracts

from aio.web import abstract


@abstracts.implementer(abstract.ADownloader)
class Downloader:
    pass


@abstracts.implementer(abstract.AChecksumDownloader)
class ChecksumDownloader:
    pass

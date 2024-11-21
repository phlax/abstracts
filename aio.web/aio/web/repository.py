
import abstracts

from aio.web import abstract, downloader


@abstracts.implementer(abstract.ARepositoryRequest)
class RepositoryRequest:

    @property
    def downloader_class(self):
        return downloader.ChecksumDownloader


@abstracts.implementer(abstract.ARepositoryMirrors)
class RepositoryMirrors:

    @property
    def request_class(self):
        return RepositoryRequest


from aio.api import bazel


def test_bazelworkerprocessor_constructor():
    processor = bazel.BazelWorkerProcessor("PROTOCOL")
    assert isinstance(processor, bazel.IBazelWorkerProcessor)


def test_bazelworker_constructor():
    worker = bazel.BazelWorker()
    assert isinstance(worker, bazel.IBazelWorker)
    assert worker.processor_class == bazel.BazelWorkerProcessor

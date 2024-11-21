
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

import abstracts

from aio.api import bazel
from aio.core import pipe
from aio.run import runner


@abstracts.implementer(bazel.IBazelProcessProtocol)
class DummyBazelProcessProtocol(bazel.ABazelProcessProtocol):

    def process(self, request):
        return super().process(request)


@abstracts.implementer(bazel.IBazelWorker)
class DummyBazelWorker(bazel.ABazelWorker):

    @property
    def processor_class(self):
        return super().processor_class


def test_bazelprocessprotocol_constructor():
    with pytest.raises(TypeError):
        bazel.ABazelProcessProtocol("PROCESSOR", "ARGS")

    protocol = DummyBazelProcessProtocol("PROCESSOR", "ARGS")
    assert isinstance(protocol, pipe.IProcessProtocol)

    with pytest.raises(NotImplementedError):
        protocol.process(MagicMock())


def test_bazelprocessprotocol_parser(patches):
    protocol = DummyBazelProcessProtocol("PROCESSOR", "ARGS")
    patched = patches(
        "argparse",
        "ABazelProcessProtocol.add_arguments",
        prefix="aio.api.bazel.abstract.worker")

    with patched as (m_argparse, m_add):
        assert (
            protocol.parser
            == m_argparse.ArgumentParser.return_value)

    assert (
        m_argparse.ArgumentParser.call_args
        == [(), dict(fromfile_prefix_chars="@")])
    assert (
        m_add.call_args
        == [(m_argparse.ArgumentParser.return_value, ), {}])
    assert "parser" in protocol.__dict__


def test_bazelprocessprotocol_add_arguments():
    protocol = DummyBazelProcessProtocol("PROCESSOR", "ARGS")
    parser = MagicMock()
    assert not protocol.add_arguments(parser)
    assert (
        parser.add_argument.call_args_list
        == [[("--in", ), {}],
            [("--out", ), {}]])


def test_bazelworkerprocessor_constructor():
    processor = bazel.ABazelWorkerProcessor("PROTOCOL")
    assert isinstance(processor, pipe.IStdinStdoutProcessor)


async def test_bazelworkerprocessor_process(patches):
    processor = bazel.ABazelWorkerProcessor("PROTOCOL")
    patched = patches(
        "str",
        "utils",
        "pipe.StdinStdoutProcessor.process",
        prefix="aio.api.bazel.abstract.worker")
    captured = MagicMock()
    recv = MagicMock()

    with patched as (m_str, m_utils, m_super):
        (m_utils.captured_warnings
                .return_value.__enter__
                .return_value) = captured
        assert (
            await processor.process(recv)
            == m_str.return_value)

    assert (
        captured.result
        == m_super.return_value)
    assert (
        m_str.call_args
        == [(captured, ), {}])
    assert (
        m_utils.captured_warnings.call_args
        == [(), {}])
    assert (
        m_super.call_args
        == [(recv, ), {}])


async def test_bazelworkerprocessor_recv(patches):
    processor = bazel.ABazelWorkerProcessor("PROTOCOL")
    patched = patches(
        "pipe.StdinStdoutProcessor.recv",
        "ABazelWorkerProcessor._load",
        prefix="aio.api.bazel.abstract.worker")

    with patched as (m_recv, m_load):
        assert (
            await processor.recv()
            == m_load.return_value)

    assert (
        m_load.call_args
        == [(m_recv.return_value, ), {}])


@pytest.mark.parametrize("msg", [None, MagicMock()])
async def test_bazelworkerprocessor_send(patches, msg):
    processor = bazel.ABazelWorkerProcessor("PROTOCOL")
    patched = patches(
        "pipe.StdinStdoutProcessor.send",
        "ABazelWorkerProcessor._dump",
        prefix="aio.api.bazel.abstract.worker")

    with patched as (m_send, m_dump):
        assert not await processor.send(msg)

    assert (
        m_send.call_args
        == [(m_dump.return_value, ), {}])
    assert (
        m_dump.call_args
        == [(msg or "", ), {}])


def test_bazelworkerprocessor__dump(patches):
    processor = bazel.ABazelWorkerProcessor("PROTOCOL")
    patched = patches(
        "dict",
        "json",
        prefix="aio.api.bazel.abstract.worker")
    msg = MagicMock()

    with patched as (m_dict, m_json):
        assert (
            processor._dump(msg)
            == m_json.dumps.return_value)

    assert (
        m_json.dumps.call_args
        == [(m_dict.return_value, ), {}])
    assert (
        m_dict.call_args
        == [(), dict(exit_code=0, output=msg)])


async def test_bazelworkerprocessor__load(patches):
    processor = bazel.ABazelWorkerProcessor("PROTOCOL")
    patched = patches(
        "json",
        ("ABazelWorkerProcessor.protocol",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.worker")
    recv = MagicMock()

    with patched as (m_json, m_proto):
        proto = AsyncMock(return_value=MagicMock())
        m_proto.side_effect = proto
        assert (
            await processor._load(recv)
            == proto.return_value.parser.parse_args.return_value)

    assert (
        proto.return_value.parser.parse_args.call_args
        == [(m_json.loads.return_value.__getitem__.return_value, ), {}])
    assert (
        m_json.loads.call_args
        == [(recv, ), {}])
    assert (
        m_json.loads.return_value.__getitem__.call_args
        == [("arguments", ), {}])


def test_bazelworker_constructor():
    with pytest.raises(TypeError):
        bazel.ABazelWorker()

    worker = DummyBazelWorker()
    assert isinstance(worker, runner.Runner)
    assert worker._use_uvloop is False

    with pytest.raises(NotImplementedError):
        worker.processor_class


def test_bazelworker_persistent(patches):
    worker = DummyBazelWorker()
    patched = patches(
        ("ABazelWorker.args",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.worker")

    with patched as (m_args, ):
        assert (
            worker.persistent
            == m_args.return_value.persistent_worker)

    assert "persistent" not in worker.__dict__


def test_bazelworker_protocol_args(patches):
    worker = DummyBazelWorker()
    patched = patches(
        "argparse",
        ("ABazelWorker.extra_args",
         dict(new_callable=PropertyMock)),
        ("ABazelWorker.protocol_class",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.worker")

    with patched as (m_argparse, m_args, m_protocol):
        assert (
            worker.protocol_args
            == m_argparse.ArgumentParser.return_value.parse_args.return_value)

    assert (
        m_argparse.ArgumentParser.call_args
        == [(), {}])
    assert (
        m_protocol.return_value.add_protocol_arguments.call_args
        == [(m_argparse.ArgumentParser.return_value, ), {}])
    assert (
        m_argparse.ArgumentParser.return_value.parse_args.call_args
        == [(m_args.return_value, ), {}])
    assert "protocol_args" in worker.__dict__


def test_bazelworker_protocol_class(patches):
    worker = DummyBazelWorker()
    patched = patches(
        "utils",
        ("ABazelWorker.args",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.worker")

    with patched as (m_utils, m_args):
        assert (
            worker.protocol_class
            == m_utils.dottedname_resolve.return_value)

    assert (
        m_utils.dottedname_resolve.call_args
        == [(m_args.return_value.protocol, ), {}])
    assert "protocol_class" in worker.__dict__


def test_bazelworker_add_arguments(patches):
    worker = DummyBazelWorker()
    patched = patches(
        "runner.Runner.add_arguments",
        prefix="aio.api.bazel.abstract.worker")
    parser = MagicMock()

    with patched as (m_super, ):
        assert not worker.add_arguments(parser)

    assert (
        parser.add_argument.call_args_list
        == [[("protocol", ), {}],
            [("--persistent_worker", ), dict(action="store_true")]])
    assert (
        m_super.call_args
        == [(parser, ), {}])


async def test_bazelworker_protocol(patches):
    worker = DummyBazelWorker()
    patched = patches(
        ("ABazelWorker.protocol_args",
         dict(new_callable=PropertyMock)),
        ("ABazelWorker.protocol_class",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.worker")
    processor = MagicMock()

    with patched as (m_args, m_class):
        assert (
            await worker.protocol(processor)
            == m_class.return_value.return_value)

    assert (
        m_class.return_value.call_args
        == [(processor, m_args.return_value), {}])


@pytest.mark.parametrize("persistent", [True, False])
async def test_bazelworker_run(patches, persistent):
    worker = DummyBazelWorker()
    patched = patches(
        ("ABazelWorker.persistent",
         dict(new_callable=PropertyMock)),
        ("ABazelWorker.processor_class",
         dict(new_callable=PropertyMock)),
        "ABazelWorker.protocol",
        prefix="aio.api.bazel.abstract.worker")

    with patched as (m_persistent, m_class, m_protocol):
        m_persistent.return_value = persistent
        m_class.return_value.return_value.side_effect = AsyncMock()
        assert not await worker.run()

    if not persistent:
        assert not m_class.called
        return
    assert (
        m_class.return_value.call_args
        == [(m_protocol, ), {}])
    assert (
        m_class.return_value.return_value.call_args
        == [(), {}])

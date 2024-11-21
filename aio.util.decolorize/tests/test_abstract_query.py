
from unittest.mock import MagicMock, PropertyMock

import pytest

import abstracts

from aio.api import bazel


@abstracts.implementer(bazel.ABazelQuery)
class DummyBazelQuery:

    @property
    def bazel_path(self):
        return super().bazel_path

    @property
    def path(self):
        return super().path


@pytest.mark.parametrize("bazel_path", [None, "", "BAZEL PATH"])
def test_base_bazel_query_constructor(bazel_path):
    kwargs = (
        dict(bazel_path=bazel_path)
        if bazel_path is not None
        else {})

    with pytest.raises(TypeError):
        bazel.ABazelQuery("PATH", **kwargs)

    query = DummyBazelQuery("PATH", **kwargs)
    assert query._path == "PATH"
    assert query._bazel_path == bazel_path


@pytest.mark.parametrize(
    "args", [[], [f"ARG{i}" for i in range(0, 5)]])
@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
async def test_base_bazel_query_dunder_call(patches, args, kwargs):
    query = DummyBazelQuery("PATH")
    patched = patches(
        "ABazelQuery.query",
        prefix="aio.api.bazel.abstract.query")

    with patched as (m_query, ):
        assert (
            await query(*args, **kwargs)
            == m_query.return_value)

    assert (
        m_query.call_args
        == [tuple(args), kwargs])


def test_base_bazel_query_super(patches):
    query = DummyBazelQuery("PATH")
    patched = patches(
        ("ABazelCommand.bazel_path",
         dict(new_callable=PropertyMock)),
        ("ABazelCommand.path",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.query")

    with patched as (m_bazel, m_path):
        assert query.bazel_path == m_bazel.return_value
        assert query.path == m_path.return_value


def test_base_bazel_query_query_kwargs(patches):
    query = DummyBazelQuery("PATH")
    patched = patches(
        ("ABazelQuery.path",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.query")

    with patched as (m_path, ):
        assert (
            query.query_kwargs
            == dict(cwd=str(m_path.return_value),
                    encoding="utf-8"))

    assert "query_kwargs" not in query.__dict__


@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
async def test_base_bazel_query_query(patches, kwargs):
    query = DummyBazelQuery("PATH")
    patched = patches(
        "ABazelQuery.handle_query_response",
        "ABazelQuery.run_query",
        prefix="aio.api.bazel.abstract.query")

    with patched as (m_response, m_query):
        assert (
            await query.query("EXPRESSION", **kwargs)
            == m_response.return_value)

    assert (
        m_response.call_args
        == [(m_query.return_value, ), {}])
    assert (
        m_query.call_args
        == [("EXPRESSION", ), kwargs])


@pytest.mark.parametrize("failed", [True, False])
def test_base_bazel_query_handle_query_response(patches, failed):
    query = DummyBazelQuery("PATH")
    patched = patches(
        "ABazelQuery.query_failed",
        prefix="aio.api.bazel.abstract.query")
    response = MagicMock()

    with patched as (m_failed, ):
        m_failed.return_value = failed
        if failed:
            with pytest.raises(bazel.BazelQueryError) as e:
                query.handle_query_response(response)
            assert (
                e.value.args[0]
                == (f"\n{response.stdout.strip.return_value}"
                    f"{response.stderr.strip.return_value}"))
        else:
            assert (
                query.handle_query_response(response)
                == response.stdout.strip.return_value.split.return_value)

    assert (
        m_failed.call_args
        == [(response, ), {}])
    assert (
        response.stdout.strip.call_args
        == [(), {}])
    if failed:
        assert (
            response.stderr.strip.call_args
            == [(), {}])
        assert not response.stdout.strip.return_value.split.called
        return
    assert not response.stderr.called
    assert (
        response.stdout.strip.return_value.split.call_args
        == [("\n", ), {}])


def test_base_bazel_query_query_command(patches):
    query = DummyBazelQuery("PATH")
    patched = patches(
        ("ABazelQuery.bazel_path",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.query")

    with patched as (m_bazel, ):
        assert (
            query.query_command("EXPRESSION")
            == (str(m_bazel.return_value), "query", "EXPRESSION"))


@pytest.mark.parametrize("returncode", [0, 1, 2])
@pytest.mark.parametrize("startswith", [True, False])
def test_base_bazel_query_query_failed(returncode, startswith):
    query = DummyBazelQuery("PATH")
    response = MagicMock()
    response.returncode = returncode
    response.stdout.strip.return_value.startswith.return_value = startswith
    assert (
        query.query_failed(response)
        == bool(returncode or startswith))
    if returncode:
        assert not response.stdout.strip.called
        return
    assert (
        response.stdout.strip.call_args
        == [(), {}])
    assert (
        response.stdout.strip.return_value.startswith.call_args
        == [("[bazel release", ), {}])


@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
async def test_base_bazel_query_run_query(patches, kwargs):
    query = DummyBazelQuery("PATH")
    patched = patches(
        ("ABazelQuery.query_kwargs",
         dict(new_callable=PropertyMock)),
        "ABazelQuery.query_command",
        "ABazelQuery.subproc_run",
        prefix="aio.api.bazel.abstract.query")

    mapping = {
        f"K1{i}": f"V1{i}"
        for i in range(0, 3)}

    with patched as (m_kwargs, m_command, m_run):
        m_kwargs.return_value.copy.return_value = mapping
        assert (
            await query.run_query("EXPRESSION", **kwargs)
            == m_run.return_value)

    expected = {**mapping, **kwargs}
    assert (
        m_run.call_args
        == [(m_command.return_value, ), expected])
    assert (
        m_command.call_args
        == [("EXPRESSION", ), {}])

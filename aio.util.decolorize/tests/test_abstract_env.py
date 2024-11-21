
from unittest.mock import AsyncMock, PropertyMock

import pytest

import abstracts

from aio.api import bazel


@abstracts.implementer(bazel.ABazelEnv)
class DummyBazelEnv:

    @property
    def bazel_path(self):
        return super().bazel_path

    @property
    def bazel_query_class(self):
        return super().bazel_query_class

    @property
    def bazel_run_class(self):
        return super().bazel_run_class

    @property
    def path(self):
        return super().path


@pytest.mark.parametrize("bazel_path", [None, "", "BAZEL PATH"])
def test_base_bazel_env_constructor(bazel_path):
    kwargs = (
        dict(bazel_path=bazel_path)
        if bazel_path is not None
        else {})

    with pytest.raises(TypeError):
        bazel.ABazelEnv("PATH", **kwargs)

    env = DummyBazelEnv("PATH", **kwargs)
    assert env._path == "PATH"
    assert env._bazel_path == bazel_path

    with pytest.raises(NotImplementedError):
        env.bazel_query_class
    with pytest.raises(NotImplementedError):
        env.bazel_run_class


def test_base_bazel_env_bazel_query(patches):
    env = DummyBazelEnv("PATH")
    patched = patches(
        ("ABazelEnv.bazel_query_class",
         dict(new_callable=PropertyMock)),
        ("ABazelEnv.bazel_path",
         dict(new_callable=PropertyMock)),
        ("ABazelEnv.path",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.env")

    with patched as (m_class, m_bazel, m_path):
        assert (
            env.bazel_query
            == m_class.return_value.return_value)

    assert (
        m_class.return_value.call_args
        == [(m_path.return_value, ),
            dict(bazel_path=m_bazel.return_value)])
    assert "bazel_query" in env.__dict__


def test_base_bazel_env_bazel_run(patches):
    env = DummyBazelEnv("PATH")
    patched = patches(
        ("ABazelEnv.bazel_run_class",
         dict(new_callable=PropertyMock)),
        ("ABazelEnv.bazel_path",
         dict(new_callable=PropertyMock)),
        ("ABazelEnv.path",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.env")

    with patched as (m_class, m_bazel, m_path):
        assert (
            env.bazel_run
            == m_class.return_value.return_value)

    assert (
        m_class.return_value.call_args
        == [(m_path.return_value, ),
            dict(bazel_path=m_bazel.return_value)])
    assert "bazel_run" in env.__dict__


@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
async def test_base_bazel_env_query(patches, kwargs):
    env = DummyBazelEnv("PATH")
    patched = patches(
        ("ABazelEnv.bazel_query",
         dict(new_callable=AsyncMock)),
        prefix="aio.api.bazel.abstract.env")

    with patched as (m_query, ):
        assert (
            await env.query("QUERY", **kwargs)
            == m_query.return_value)

    assert (
        m_query.call_args
        == [("QUERY", ), kwargs])


@pytest.mark.parametrize(
    "args", [[], [f"ARG{i}" for i in range(0, 5)]])
@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
async def test_base_bazel_env_run(patches, args, kwargs):
    env = DummyBazelEnv("PATH")
    patched = patches(
        ("ABazelEnv.bazel_run",
         dict(new_callable=AsyncMock)),
        prefix="aio.api.bazel.abstract.env")

    with patched as (m_run, ):
        assert (
            await env.run("COMMAND", *args, **kwargs)
            == m_run.return_value)

    assert (
        m_run.call_args
        == [("COMMAND", ) + tuple(args), kwargs])

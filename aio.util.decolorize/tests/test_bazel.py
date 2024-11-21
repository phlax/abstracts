
from unittest.mock import PropertyMock

import pytest

from aio.api.bazel import Bazel, BazelEnv, BazelQuery, BazelRun


@pytest.mark.parametrize(
    "args", [[], [f"ARG{i}" for i in range(0, 5)]])
@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
def test_bazel_bazel(patches, args, kwargs):
    patched = patches(
        "ABazel.__init__",
        ("ABazel.bazel_path",
         dict(new_callable=PropertyMock)),
        ("ABazel.path",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.bazel")

    with patched as (m_super, m_bazel, m_path):
        m_super.return_value = None
        bazel_impl = Bazel(*args, **kwargs)
        path = bazel_impl.path
        bazel_path = bazel_impl.bazel_path

    assert (
        m_super.call_args
        == [tuple(args), kwargs])
    assert (
        path
        == m_path.return_value)
    assert "path" in bazel_impl.__dict__
    assert (
        bazel_path
        == m_bazel.return_value)
    assert "bazel_path" in bazel_impl.__dict__


@pytest.mark.parametrize(
    "args", [[], [f"ARG{i}" for i in range(0, 5)]])
@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
def test_bazel_bazel_env(patches, args, kwargs):
    patched = patches(
        "ABazelEnv.__init__",
        prefix="aio.api.bazel.bazel")

    with patched as (m_super, ):
        m_super.return_value = None
        bazel_env = BazelEnv(*args, **kwargs)

    assert (
        m_super.call_args
        == [tuple(args), kwargs])
    assert bazel_env.bazel_query_class == BazelQuery
    assert "bazel_query_class" not in bazel_env.__dict__
    assert bazel_env.bazel_run_class == BazelRun
    assert "bazel_run_class" not in bazel_env.__dict__


@pytest.mark.parametrize(
    "args", [[], [f"ARG{i}" for i in range(0, 5)]])
@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
def test_bazel_bazel_query(patches, args, kwargs):
    patched = patches(
        "ABazelQuery.__init__",
        prefix="aio.api.bazel.bazel")

    with patched as (m_super, ):
        m_super.return_value = None
        BazelQuery(*args, **kwargs)

    assert (
        m_super.call_args
        == [tuple(args), kwargs])


@pytest.mark.parametrize(
    "args", [[], [f"ARG{i}" for i in range(0, 5)]])
@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
def test_bazel_bazel_run(patches, args, kwargs):
    patched = patches(
        "ABazelRun.__init__",
        prefix="aio.api.bazel.bazel")

    with patched as (m_super, ):
        m_super.return_value = None
        BazelRun(*args, **kwargs)

    assert (
        m_super.call_args
        == [tuple(args), kwargs])


from unittest.mock import PropertyMock

import pytest

import abstracts

from aio.api import bazel


@abstracts.implementer(bazel.ABazelRun)
class DummyBazelRun:

    @property
    def bazel_path(self):
        return super().bazel_path

    @property
    def path(self):
        return super().path


@pytest.mark.parametrize("bazel_path", [None, "", "BAZEL PATH"])
def test_base_bazel_run_constructor(bazel_path):
    kwargs = (
        dict(bazel_path=bazel_path)
        if bazel_path is not None
        else {})

    with pytest.raises(TypeError):
        bazel.ABazelRun("PATH", **kwargs)

    run = DummyBazelRun("PATH", **kwargs)
    assert run._path == "PATH"
    assert run._bazel_path == bazel_path


@pytest.mark.parametrize(
    "args", [[], [f"ARG{i}" for i in range(0, 5)]])
@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
async def test_base_bazel_run_dunder_call(patches, args, kwargs):
    run = DummyBazelRun("PATH")
    patched = patches(
        "ABazelRun.run",
        prefix="aio.api.bazel.abstract.run")

    with patched as (m_run, ):
        assert (
            await run(*args, **kwargs)
            == m_run.return_value)

    assert (
        m_run.call_args
        == [tuple(args), kwargs])


def test_base_bazel_run_super(patches):
    run = DummyBazelRun("PATH")
    patched = patches(
        ("ABazelCommand.bazel_path",
         dict(new_callable=PropertyMock)),
        ("ABazelCommand.path",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.run")

    with patched as (m_bazel, m_path):
        assert run.bazel_path == m_bazel.return_value
        assert run.path == m_path.return_value


@pytest.mark.parametrize(
    "args", [[], [f"ARG{i}" for i in range(0, 5)]])
@pytest.mark.parametrize("capture", [None, True, False])
@pytest.mark.parametrize("raises", [None, True, False])
@pytest.mark.parametrize("cwd", [None, "", "CWD"])
@pytest.mark.parametrize("returncode", [0, 1, 2])
async def test_base_bazel_run_run(
        patches, args, capture, raises, cwd, returncode):
    run = DummyBazelRun("PATH")
    patched = patches(
        ("ABazelRun.bazel_path",
         dict(new_callable=PropertyMock)),
        "ABazelRun.subproc_run",
        prefix="aio.api.bazel.abstract.run")
    kwargs = {}
    if capture is not None:
        kwargs["capture_output"] = capture
    if cwd is not None:
        kwargs["cwd"] = cwd
    if raises is not None:
        kwargs["raises"] = raises
    else:
        raises = True

    with patched as (m_bazel, m_run):
        m_run.return_value.returncode = returncode
        if returncode and raises:
            with pytest.raises(bazel.BazelRunError) as e:
                await run.run("TARGET", *args, **kwargs)
            assert (
                e.value.args[0]
                == f"Bazel run failed: {m_run.return_value}")
        else:
            assert (
                await run.run("TARGET", *args, **kwargs)
                == m_run.return_value)

    args = (
        ("--", ) + tuple(args)
        if args
        else ())
    assert (
        m_run.call_args
        == [((m_bazel.return_value, "run", "TARGET") + args, ),
            dict(capture_output=capture or False)])

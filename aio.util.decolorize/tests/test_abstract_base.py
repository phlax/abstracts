
from unittest.mock import AsyncMock, PropertyMock

import pytest

import abstracts

from aio.api import bazel


@abstracts.implementer(bazel.ABazel)
class DummyBazel:

    @property
    def bazel_path(self):
        return super().bazel_path

    @property
    def path(self):
        return super().path


@abstracts.implementer(bazel.ABazelCommand)
class DummyBazelCommand(DummyBazel):
    pass


@pytest.mark.parametrize("bazel_path", [None, "", "BAZEL PATH"])
def test_base_bazel_constructor(bazel_path):
    kwargs = (
        dict(bazel_path=bazel_path)
        if bazel_path is not None
        else {})

    with pytest.raises(TypeError):
        bazel.ABazel("PATH", **kwargs)

    base = DummyBazel("PATH", **kwargs)
    assert base._path == "PATH"
    assert base._bazel_path == bazel_path


@pytest.mark.parametrize("bazel_path", [None, "", "BAZEL PATH"])
@pytest.mark.parametrize("which", [None, "", "FOUND BAZEL PATH"])
def test_base_bazel_bazel_path(patches, bazel_path, which):
    base = DummyBazel("PATH")
    patched = patches(
        "pathlib",
        "shutil",
        prefix="aio.api.bazel.abstract.base")
    base._bazel_path = bazel_path

    with patched as (m_plib, m_shutil):
        m_shutil.which.return_value = which

        if not bazel_path and not which:
            with pytest.raises(bazel.BazelError) as e:
                base.bazel_path
            assert (
                e.value.args[0]
                == "No path supplied, and `bazel` command not found")
        else:
            assert base.bazel_path == m_plib.Path.return_value

    assert "bazel_path" not in base.__dict__
    if bazel_path:
        assert not m_shutil.which.called
        assert (
            m_plib.Path.call_args
            == [(bazel_path, ), {}])
        return
    assert (
        m_shutil.which.call_args
        == [("bazel", ), {}])
    if not which:
        assert not m_plib.Path.called
    else:
        assert (
            m_plib.Path.call_args
            == [(which, ), {}])


def test_base_bazel_path(patches):
    base = DummyBazel("PATH")
    patched = patches(
        "pathlib",
        prefix="aio.api.bazel.abstract.base")

    with patched as (m_plib, ):
        assert base.path == m_plib.Path.return_value

    assert (
        m_plib.Path.call_args
        == [("PATH", ), {}])
    assert "path" not in base.__dict__


@pytest.mark.parametrize("bazel_path", [None, "", "BAZEL PATH"])
def test_base_bazel_command_constructor(bazel_path):
    kwargs = (
        dict(bazel_path=bazel_path)
        if bazel_path is not None
        else {})

    with pytest.raises(TypeError):
        bazel.ABazelCommand("PATH", **kwargs)

    command = DummyBazelCommand("PATH", **kwargs)
    assert command._path == "PATH"
    assert command._bazel_path == bazel_path


def test_base_bazel_command_executor(patches):
    command = DummyBazelCommand("PATH")
    patched = patches(
        "concurrent.futures",
        prefix="aio.api.bazel.abstract.base")

    with patched as (m_futures, ):
        assert (
            command.executor
            == m_futures.ThreadPoolExecutor.return_value)

    assert (
        m_futures.ThreadPoolExecutor.call_args
        == [(), {}])
    assert "executor" not in command.__dict__


def test_base_bazel_command_loop(patches):
    command = DummyBazelCommand("PATH")
    patched = patches(
        "asyncio",
        prefix="aio.api.bazel.abstract.base")

    with patched as (m_aio, ):
        assert (
            command.loop
            == m_aio.get_running_loop.return_value)

    assert (
        m_aio.get_running_loop.call_args
        == [(), {}])
    assert "loop" not in command.__dict__


@pytest.mark.parametrize(
    "args", [[], [f"ARG{i}" for i in range(0, 5)]])
@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
async def test_base_bazel_command_subproc_run(patches, args, kwargs):
    command = DummyBazelCommand("PATH")
    patched = patches(
        ("ABazelCommand.executor",
         dict(new_callable=PropertyMock)),
        "ABazelCommand._run_in_executor",
        prefix="aio.api.bazel.abstract.base")

    with patched as (m_exec, m_run):
        assert (
            await command.subproc_run(*args, **kwargs)
            == m_run.return_value)

    assert (
        m_run.call_args
        == [(m_exec.return_value.__enter__.return_value, ) + tuple(args),
            kwargs])


@pytest.mark.parametrize(
    "args", [[], [f"ARG{i}" for i in range(0, 5)]])
@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
async def test_base_bazel_command__run_in_executor(patches, args, kwargs):
    command = DummyBazelCommand("PATH")
    patched = patches(
        "partial",
        ("ABazelCommand.loop",
         dict(new_callable=PropertyMock)),
        "ABazelCommand._subproc_run",
        prefix="aio.api.bazel.abstract.base")

    with patched as (m_partial, m_loop, m_run):
        m_loop.return_value.run_in_executor = AsyncMock()
        assert (
            await command._run_in_executor("POOL", *args, **kwargs)
            == m_loop.return_value.run_in_executor.return_value)

    assert (
        m_loop.return_value.run_in_executor.call_args
        == [("POOL", m_partial.return_value), {}])
    assert (
        m_partial.call_args
        == [(m_run, ) + tuple(args), kwargs])


@pytest.mark.parametrize(
    "args", [[], [f"ARG{i}" for i in range(0, 5)]])
@pytest.mark.parametrize(
    "kwargs", [{}, {f"K{i}": f"V{i}" for i in range(0, 5)}])
@pytest.mark.parametrize("cwd", [None, "CWD"])
@pytest.mark.parametrize("capture", [None, "CAPTURE"])
def test_base_bazel_command__subproc_run(
        patches, args, kwargs, cwd, capture):
    kwargs = kwargs.copy()
    command = DummyBazelCommand("PATH")
    patched = patches(
        "subprocess",
        ("ABazelCommand.path",
         dict(new_callable=PropertyMock)),
        prefix="aio.api.bazel.abstract.base")
    if cwd:
        kwargs["cwd"] = cwd
    if capture:
        kwargs["capture_output"] = capture
    expected = kwargs.copy()

    with patched as (m_subproc, m_path):
        assert (
            command._subproc_run(*args, **kwargs)
            == m_subproc.run.return_value)

    if not cwd:
        expected["cwd"] = m_path.return_value
    else:
        assert not m_path.called
    if not capture:
        expected["capture_output"] = True
    assert (
        m_subproc.run.call_args
        == [tuple(args), expected])

"""Client discovery survives PATH differences and IDE extension replacement."""
import os
from pathlib import Path
import pytest
from intact_backend import ask_ai


@pytest.fixture
def home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    monkeypatch.setattr(ask_ai.shutil, 'which', lambda name: None)
    monkeypatch.delenv('INTACT_CODEX_CLI', raising=False)
    monkeypatch.delenv('INTACT_WINDOWS_HOME', raising=False)
    monkeypatch.setenv('LOCALAPPDATA',str(tmp_path/'AppData/Local'))
    return tmp_path


def executable(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('#!/bin/sh\nexit 0\n')
    path.chmod(0o755)
    return str(path)


def test_standalone_client_found_without_shell_path(home):
    expected = executable(home / '.local/bin'/('codex.exe' if os.name=='nt' else 'codex'))
    assert ask_ai.client_path() == expected
    assert ask_ai.capabilities()['available']


def test_missing_linux_client_explains_windows_wsl_boundary(home):
    status = ask_ai.capabilities()
    assert not status['available']
    if os.name=='nt':assert 'native Windows' in status['setup_message']
    else:
        assert 'Ubuntu/WSL' in status['setup_message']
        assert 'does not install the WSL executable' in status['setup_message']


def test_invalid_explicit_client_is_not_silently_ignored(home, monkeypatch):
    executable(home / '.local/bin'/('codex.exe' if os.name=='nt' else 'codex'))
    monkeypatch.setenv('INTACT_CODEX_CLI', str(home / 'missing'))
    assert ask_ai.client_path() is None


def test_ide_update_picks_newest_linux_binary(home):
    root = home / '.vscode-server/extensions'
    binary='windows-x86_64/codex.exe' if os.name=='nt' else 'linux-x86_64/codex'
    executable(root / ('openai.chatgpt-9.0.0/bin/'+binary))
    expected = executable(root / ('openai.chatgpt-10.0.0/bin/'+binary))
    assert ask_ai.client_path() == expected


@pytest.mark.skipif(os.name=='nt',reason='Windows does not implement POSIX executable mode bits.')
def test_nonexecutable_file_is_not_a_client(home):
    path = home / '.local/bin/codex'
    executable(path)
    path.chmod(0o644)
    assert ask_ai.client_path() is None


def test_windows_binary_is_not_used_as_a_linux_client(home, monkeypatch):
    monkeypatch.setenv('INTACT_CODEX_CLI', executable(home / 'codex.exe'))
    monkeypatch.setattr(ask_ai.sys, 'platform', 'linux')
    assert ask_ai.client_path() is None

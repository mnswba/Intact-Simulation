from hashlib import sha256
import json
from pathlib import Path
import pytest
from intact_backend import desktop

def test_download_checksum_failure_never_becomes_a_valid_runtime(tmp_path,monkeypatch):
    monkeypatch.setattr(desktop.urllib.request,'urlretrieve',lambda url,path:Path(path).write_bytes(b'wrong'))
    target=tmp_path/'runtime.exe'
    with pytest.raises(ValueError,match='checksum mismatch'):desktop.download('https://example.invalid/runtime',target,sha256(b'expected').hexdigest())
    assert not target.exists()

def test_verified_cached_download_needs_no_network(tmp_path,monkeypatch):
    path=tmp_path/'runtime';path.write_bytes(b'verified')
    monkeypatch.setattr(desktop.urllib.request,'urlretrieve',lambda *args:pytest.fail('cached runtime was downloaded again'))
    assert desktop.download('https://example.invalid',path,sha256(b'verified').hexdigest())==path

def test_installed_freecad_receipt_checks_version_hash_and_executable(tmp_path,monkeypatch):
    root=tmp_path/'freecad-1.1.4/root';(root/'bin').mkdir(parents=True);(root/'bin/python.exe').write_bytes(b'fixture')
    (root.parent/'installation.json').write_text(json.dumps({'root':str(root),'version':'1.1.4','sha256':desktop.FREECAD_SHA}))
    monkeypatch.setattr(desktop,'download',lambda *args:pytest.fail('installed FreeCAD downloaded again'))
    assert desktop.freecad(tmp_path)==root

def test_setup_failure_is_reported_instead_of_claiming_ready(tmp_path,monkeypatch):
    monkeypatch.setattr(desktop,'freecad',lambda path:(_ for _ in ()).throw(ValueError('verification failed')))
    setup=desktop.DesktopSetup(tmp_path);setup.prepare()
    assert not setup.status()['ready'] and setup.status()['stage']=='failed'
    with pytest.raises(RuntimeError,match='verification failed'):setup.wait()

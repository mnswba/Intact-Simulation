"""Exercise the real Windows worker boundary, without a CAD or AI mock."""
import json
import os
import socket
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(sys.platform != 'win32', reason='Windows AppContainer checks')


def test_worker_can_write_outputs_but_cannot_read_private_files_or_use_network(tmp_path):
    from intact_backend.windows_sandbox import run, runtime_options

    inputs, outputs = tmp_path/'input', tmp_path/'output'
    inputs.mkdir(); outputs.mkdir()
    private = tmp_path/'private.txt'; private.write_text('private test fixture')
    (inputs/'brief.txt').write_text('read-only brief')
    python, readable, env = runtime_options()
    source = '''
import json,os,socket,sys
from pathlib import Path
from windows_sandbox import in_appcontainer
result={'appcontainer':in_appcontainer()}
inputs=Path(os.environ['INTACT_WORKER_INPUT'])
result['input_read']=(inputs/'brief.txt').read_text()=='read-only brief'
try:
    Path(sys.argv[1]).read_text();result['private_read_denied']=False
except PermissionError:result['private_read_denied']=True
try:
    (inputs/'brief.txt').write_text('changed');result['input_write_denied']=False
except PermissionError:result['input_write_denied']=True
try:
    connection=socket.create_connection(('127.0.0.1',int(sys.argv[2])),timeout=1)
    connection.close();result['network_denied']=False
except (PermissionError,TimeoutError):result['network_denied']=True
Path(os.environ['INTACT_WORKER_OUTPUT'],'result.json').write_text(json.dumps(result))
'''
    with socket.socket() as listener:
        listener.bind(('127.0.0.1',0)); listener.listen(2)
        port = listener.getsockname()[1]
        # A reachable endpoint is required: a closed port cannot prove isolation.
        with socket.create_connection(('127.0.0.1',port),timeout=1):
            connection, _ = listener.accept(); connection.close()
        assert run([python,'-c',source,str(private),str(port)],inputs,outputs,readable,env=env,timeout=15)==0
        listener.settimeout(.2)
        with pytest.raises(socket.timeout):listener.accept()
    result=json.loads((outputs/'result.json').read_text())
    assert result==dict.fromkeys(('appcontainer','input_read','private_read_denied','input_write_denied','network_denied'),True)
    assert (inputs/'brief.txt').read_text()=='read-only brief'


def test_output_limit_is_enforced_even_when_the_worker_exits_immediately(tmp_path):
    from intact_backend.windows_sandbox import run, runtime_options
    inputs,outputs=tmp_path/'input',tmp_path/'output'
    inputs.mkdir();outputs.mkdir()
    python,readable,env=runtime_options()
    code="import os;from pathlib import Path;Path(os.environ['INTACT_WORKER_OUTPUT'],'large.bin').write_bytes(b'x'*4096)"
    with pytest.raises(RuntimeError,match='exceeded its size limit'):
        run([python,'-c',code],inputs,outputs,readable,env=env,timeout=10,max_file_bytes=1024)

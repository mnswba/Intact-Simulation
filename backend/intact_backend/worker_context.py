"""Trusted paths and limits inside an already established OS sandbox."""
import os
import sys

if sys.platform == 'win32':
    from windows_sandbox import in_appcontainer
    if not in_appcontainer():
        raise RuntimeError('Windows geometry workers require an AppContainer. Execution refused.')
    # Windows redirects AppContainer cache paths to a package-specific AC tree.
    # Native libraries such as FreeCAD require these directories to exist.
    from pathlib import Path
    output = Path(os.environ['INTACT_WORKER_OUTPUT']).resolve()
    for variable in ('APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP'):
        directory = Path(os.environ[variable]).resolve()
        if not directory.is_relative_to(output):
            raise RuntimeError('Worker cache path is outside its private output tree.')
        directory.mkdir(parents=True, exist_ok=True)

    class resource:
        # CPU, memory and process limits are applied by the parent Job Object.
        # Output size and wall time are monitored by that same parent.
        RLIMIT_CPU, RLIMIT_AS, RLIMIT_FSIZE, RLIMIT_NOFILE, RLIMIT_NPROC, RLIMIT_CORE = range(6)

        @staticmethod
        def setrlimit(kind, value):
            pass
else:
    import resource


def worker_path(value):
    if value in ('/input','/work'):
        return os.environ.get('INTACT_WORKER_INPUT' if value=='/input' else 'INTACT_WORKER_OUTPUT',value)
    for prefix, variable in (('/input/', 'INTACT_WORKER_INPUT'), ('/work/', 'INTACT_WORKER_OUTPUT')):
        if value.startswith(prefix) and variable in os.environ:
            return os.path.join(os.environ[variable], *value[len(prefix):].split('/'))
    return value

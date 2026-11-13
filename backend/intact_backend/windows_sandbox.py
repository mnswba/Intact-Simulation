"""Native Windows AppContainer workers, without network capabilities.

Each run has its own package SID and Job Object. Only approved runtime/input
trees receive read access; only the private output tree receives write access.
Failure to establish isolation is fatal. There is no unsandboxed fallback.
"""
import ctypes as C
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

_available = None


def runtime_options():
    """Use the real interpreter, not the venv launcher that starts another EXE."""
    python = Path(getattr(sys, '_base_executable', sys.executable)).resolve()
    libraries = Path(os.environ.get('INTACT_PYTHON_LIBS',Path(sys.prefix)/'Lib/site-packages')).resolve()
    code = Path(__file__).parent.resolve()
    readable=[Path(sys.base_prefix), libraries, code]
    gmsh=Path(sys.prefix)/'Lib/gmsh-4.15.dll'
    if gmsh.is_file():readable.append(gmsh)
    return python, readable, {'PYTHONPATH':str(libraries)+os.pathsep+str(code)}


def available():
    global _available
    if _available is not None:return _available
    if sys.platform!='win32':return False
    import tempfile
    try:
        with tempfile.TemporaryDirectory(prefix='intact-isolation-check-') as folder:
            root=Path(folder);input_dir=root/'input';output_dir=root/'output';input_dir.mkdir();output_dir.mkdir()
            python,readable,env=runtime_options()
            code="import json,os;from pathlib import Path;from windows_sandbox import in_appcontainer;Path(os.environ['INTACT_WORKER_OUTPUT'],'probe.json').write_text(json.dumps({'isolated':in_appcontainer()}))"
            result=run([python,'-c',code],input_dir,output_dir,readable,env=env,timeout=10)
            _available=result==0 and json.loads((output_dir/'probe.json').read_text())['isolated'] is True
    except (OSError,ValueError,RuntimeError,subprocess.SubprocessError):_available=False
    return _available


def in_appcontainer():
    if sys.platform != 'win32':
        return False
    adv = C.WinDLL('advapi32', use_last_error=True)
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    adv.OpenProcessToken.argtypes = [W.HANDLE, W.DWORD, C.POINTER(W.HANDLE)]
    adv.GetTokenInformation.argtypes = [W.HANDLE, C.c_int, W.LPVOID, W.DWORD, C.POINTER(W.DWORD)]
    token = W.HANDLE()
    if not adv.OpenProcessToken(kernel.GetCurrentProcess(), 8, C.byref(token)):
        raise C.WinError(C.get_last_error())
    try:
        flag, size = W.DWORD(), W.DWORD()
        if not adv.GetTokenInformation(token, 29, C.byref(flag), C.sizeof(flag), C.byref(size)):
            raise C.WinError(C.get_last_error())
        return bool(flag.value)
    finally:
        kernel.CloseHandle(token)


class SECURITY_CAPABILITIES(C.Structure):
    _fields_ = [('AppContainerSid', W.LPVOID), ('Capabilities', W.LPVOID), ('CapabilityCount', W.DWORD), ('Reserved', W.DWORD)]


class SID_AND_ATTRIBUTES(C.Structure):
    _fields_ = [('Sid', W.LPVOID), ('Attributes', W.DWORD)]


class STARTUPINFO(C.Structure):
    _fields_ = [('cb', W.DWORD), ('lpReserved', W.LPWSTR), ('lpDesktop', W.LPWSTR), ('lpTitle', W.LPWSTR),
                ('dwX', W.DWORD), ('dwY', W.DWORD), ('dwXSize', W.DWORD), ('dwYSize', W.DWORD),
                ('dwXCountChars', W.DWORD), ('dwYCountChars', W.DWORD), ('dwFillAttribute', W.DWORD),
                ('dwFlags', W.DWORD), ('wShowWindow', W.WORD), ('cbReserved2', W.WORD),
                ('lpReserved2', W.LPVOID), ('hStdInput', W.HANDLE), ('hStdOutput', W.HANDLE), ('hStdError', W.HANDLE)]


class STARTUPINFOEX(C.Structure):
    _fields_ = [('StartupInfo', STARTUPINFO), ('lpAttributeList', W.LPVOID)]


class PROCESS_INFORMATION(C.Structure):
    _fields_ = [('hProcess', W.HANDLE), ('hThread', W.HANDLE), ('dwProcessId', W.DWORD), ('dwThreadId', W.DWORD)]


class IO_COUNTERS(C.Structure):
    _fields_ = [(name, C.c_ulonglong) for name in ('ReadOperationCount', 'WriteOperationCount', 'OtherOperationCount', 'ReadTransferCount', 'WriteTransferCount', 'OtherTransferCount')]


class BASIC_LIMIT(C.Structure):
    _fields_ = [('PerProcessUserTimeLimit', C.c_longlong), ('PerJobUserTimeLimit', C.c_longlong),
                ('LimitFlags', W.DWORD), ('MinimumWorkingSetSize', C.c_size_t), ('MaximumWorkingSetSize', C.c_size_t),
                ('ActiveProcessLimit', W.DWORD), ('Affinity', C.c_size_t), ('PriorityClass', W.DWORD), ('SchedulingClass', W.DWORD)]


class EXTENDED_LIMIT(C.Structure):
    _fields_ = [('BasicLimitInformation', BASIC_LIMIT), ('IoInfo', IO_COUNTERS),
                ('ProcessMemoryLimit', C.c_size_t), ('JobMemoryLimit', C.c_size_t),
                ('PeakProcessMemoryUsed', C.c_size_t), ('PeakJobMemoryUsed', C.c_size_t)]


def run(command, input_dir, output_dir, readonly, env=None, cancel_event=None, timeout=120, max_file_bytes=64*1024**2):
    """Use a trusted broker so a private desktop never changes the host station."""
    if sys.platform != 'win32':raise RuntimeError('Windows sandbox requires Windows.')
    config = Path(input_dir)/'sandbox-launch.json'
    config.write_text(json.dumps({'command':list(map(str,command)), 'input_dir':str(input_dir), 'output_dir':str(output_dir), 'readonly':list(map(str,readonly)), 'env':env, 'timeout':timeout, 'max_file_bytes':max_file_bytes}),encoding='utf-8')
    from .platform_support import terminate_tree
    process = subprocess.Popen([sys.executable,'-m','intact_backend.windows_sandbox',str(config)],stdout=subprocess.PIPE,stderr=subprocess.PIPE,creationflags=subprocess.CREATE_NO_WINDOW)
    deadline = time.monotonic()+timeout+120
    try:
        while process.poll() is None:
            if cancel_event and cancel_event.is_set():raise ValueError('Geometry operation cancelled.')
            if time.monotonic()>deadline:raise TimeoutError('Windows sandbox startup or worker timed out.')
            time.sleep(.05)
        stdout,stderr=process.communicate()
        if process.returncode:raise RuntimeError('Windows sandbox broker failed: '+stderr.decode(errors='replace')[-3000:])
        return json.loads(stdout)['returncode']
    finally:
        if process.poll() is None:terminate_tree(process,force=True);process.wait(timeout=10)


class SECURITY_ATTRIBUTES(C.Structure):
    _fields_=[('nLength',W.DWORD),('lpSecurityDescriptor',W.LPVOID),('bInheritHandle',W.BOOL)]


def _run(command, input_dir, output_dir, readonly, env=None, timeout=120, max_file_bytes=64*1024**2):
    if sys.platform != 'win32':
        raise RuntimeError('Windows AppContainer is only available on Windows.')
    import msvcrt
    kernel = C.WinDLL('kernel32', use_last_error=True)
    user = C.WinDLL('userenv', use_last_error=True)
    adv = C.WinDLL('advapi32', use_last_error=True)
    base = C.WinDLL('kernelbase', use_last_error=True)
    ui = C.WinDLL('user32',use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [W.LPVOID, W.LPCWSTR]
    kernel.CreateJobObjectW.restype = W.HANDLE
    kernel.SetInformationJobObject.argtypes = [W.HANDLE, C.c_int, W.LPVOID, W.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [W.HANDLE, W.HANDLE]
    kernel.TerminateJobObject.argtypes = [W.HANDLE, W.UINT]
    kernel.CloseHandle.argtypes = [W.HANDLE]
    kernel.InitializeProcThreadAttributeList.argtypes = [W.LPVOID, W.DWORD, W.DWORD, C.POINTER(C.c_size_t)]
    kernel.UpdateProcThreadAttribute.argtypes = [W.LPVOID, W.DWORD, C.c_size_t, W.LPVOID, C.c_size_t, W.LPVOID, W.LPVOID]
    kernel.DeleteProcThreadAttributeList.argtypes = [W.LPVOID]
    kernel.CreateProcessW.argtypes = [W.LPCWSTR, W.LPWSTR, W.LPVOID, W.LPVOID, W.BOOL, W.DWORD, W.LPVOID, W.LPCWSTR, C.POINTER(STARTUPINFOEX), C.POINTER(PROCESS_INFORMATION)]
    adv.CreateProcessAsUserW.argtypes = [W.HANDLE,*kernel.CreateProcessW.argtypes]
    kernel.ResumeThread.argtypes = [W.HANDLE]
    kernel.WaitForSingleObject.argtypes = [W.HANDLE, W.DWORD]
    kernel.GetExitCodeProcess.argtypes = [W.HANDLE, C.POINTER(W.DWORD)]
    kernel.LocalFree.argtypes = [W.HANDLE]
    user.CreateAppContainerProfile.argtypes = [W.LPCWSTR, W.LPCWSTR, W.LPCWSTR, W.LPVOID, W.DWORD, C.POINTER(W.LPVOID)]
    user.CreateAppContainerProfile.restype = C.c_long
    user.DeleteAppContainerProfile.argtypes = [W.LPCWSTR]
    adv.ConvertSidToStringSidW.argtypes = [W.LPVOID, C.POINTER(W.LPWSTR)]
    adv.FreeSid.argtypes = [W.LPVOID]
    adv.ConvertStringSecurityDescriptorToSecurityDescriptorW.argtypes=[W.LPCWSTR,W.DWORD,C.POINTER(W.LPVOID),W.LPVOID]
    adv.OpenProcessToken.argtypes=[W.HANDLE,W.DWORD,C.POINTER(W.HANDLE)]
    adv.GetTokenInformation.argtypes=[W.HANDLE,C.c_int,W.LPVOID,W.DWORD,C.POINTER(W.DWORD)]
    kernel.GetCurrentProcess.restype=W.HANDLE
    base.DeriveCapabilitySidsFromName.argtypes = [W.LPCWSTR, C.POINTER(C.POINTER(W.LPVOID)), C.POINTER(W.DWORD), C.POINTER(C.POINTER(W.LPVOID)), C.POINTER(W.DWORD)]
    ui.GetProcessWindowStation.restype=W.HANDLE
    ui.SetProcessWindowStation.argtypes=[W.HANDLE]
    ui.CreateWindowStationW.argtypes=[W.LPCWSTR,W.DWORD,W.DWORD,C.POINTER(SECURITY_ATTRIBUTES)]
    ui.CreateWindowStationW.restype=W.HANDLE
    ui.CreateDesktopW.argtypes=[W.LPCWSTR,W.LPCWSTR,W.LPVOID,W.DWORD,W.DWORD,C.POINTER(SECURITY_ATTRIBUTES)]
    ui.CreateDesktopW.restype=W.HANDLE
    ui.CloseDesktop.argtypes=[W.HANDLE]
    ui.CloseWindowStation.argtypes=[W.HANDLE]
    ui.GetUserObjectSecurity.argtypes=[W.HANDLE,C.POINTER(W.DWORD),W.LPVOID,W.DWORD,C.POINTER(W.DWORD)]
    ui.SetUserObjectSecurity.argtypes=[W.HANDLE,C.POINTER(W.DWORD),W.LPVOID]
    adv.ConvertSecurityDescriptorToStringSecurityDescriptorW.argtypes=[W.LPVOID,W.DWORD,W.DWORD,C.POINTER(W.LPWSTR),W.LPVOID]

    def require(ok):
        if not ok:
            raise C.WinError(C.get_last_error())

    name = 'IntactSimulation.Worker.' + uuid.uuid4().hex
    sid = W.LPVOID()
    hr = user.CreateAppContainerProfile(name, 'Intact CAD worker', 'Isolated local geometry worker', None, 0, C.byref(sid))
    if hr < 0:
        raise OSError(f'Cannot create Windows AppContainer: HRESULT {hr & 0xffffffff:08x}')
    sid_text, runtime_text, job, attributes = W.LPWSTR(), W.LPWSTR(), None, None
    groups, capabilities = C.POINTER(W.LPVOID)(), C.POINTER(W.LPVOID)()
    group_count, capability_count = W.DWORD(), W.DWORD()
    info = PROCESS_INFORMATION()
    original_station=ui.GetProcessWindowStation()
    station,desktop,desktop_sd=None,None,W.LPVOID()
    station_original=None
    granted = []
    input_dir, output_dir = Path(input_dir).resolve(), Path(output_dir).resolve()
    log = output_dir / 'worker.log'
    try:
        require(adv.ConvertSidToStringSidW(sid, C.byref(sid_text)))
        sid_string = sid_text.value
        # USER32-linked scientific runtimes need a desktop they can initialize.
        # Use private low-integrity objects, never relax the user's desktop ACL.
        token=W.HANDLE();require(adv.OpenProcessToken(kernel.GetCurrentProcess(),8,C.byref(token)))
        token_size=W.DWORD()
        adv.GetTokenInformation(token,1,None,0,C.byref(token_size))
        token_data=C.create_string_buffer(token_size.value)
        require(adv.GetTokenInformation(token,1,token_data,token_size,C.byref(token_size)))
        owner_sid=C.cast(token_data,C.POINTER(W.LPVOID))[0];owner_text=W.LPWSTR()
        require(adv.ConvertSidToStringSidW(owner_sid,C.byref(owner_text)))
        owner_string=owner_text.value;kernel.LocalFree(owner_text);kernel.CloseHandle(token)
        require(adv.ConvertStringSecurityDescriptorToSecurityDescriptorW(f'D:P(A;;GA;;;{owner_string})(A;;GA;;;SY)(A;;GA;;;{sid_string})S:(ML;;NW;;;LW)',1,C.byref(desktop_sd),None))
        sa=SECURITY_ATTRIBUTES(C.sizeof(SECURITY_ATTRIBUTES),desktop_sd,False)
        desktop=ui.CreateDesktopW(name,None,None,0,0xf01ff,C.byref(sa));require(desktop)
        require(base.DeriveCapabilitySidsFromName('IntactSimulation.CADRuntime.Read', C.byref(groups), C.byref(group_count), C.byref(capabilities), C.byref(capability_count)))
        if capability_count.value != 1:raise RuntimeError('Unexpected runtime capability identity.')
        require(adv.ConvertSidToStringSidW(capabilities[0], C.byref(runtime_text)))
        roots = list(dict.fromkeys(Path(p).resolve() for p in readonly))
        # The shared capability grants only read/execute on public runtime code.
        # Private per-job input/output use the unique package SID below.
        for path in roots:
            if not path.exists() or path.is_symlink():raise ValueError('Invalid runtime access root: ' + str(path))
            # Wheel/portable archive entries may have protected ACLs and never
            # inherit a root-only grant. Apply RX explicitly to the approved
            # runtime tree, including dependencies added since the last run.
            from hashlib import sha256
            from .platform_support import file_lock
            cache = Path(os.environ['LOCALAPPDATA'])/'IntactSimulation/sandbox-acl'
            cache.mkdir(parents=True,exist_ok=True)
            stamp = cache/sha256(str(path).encode()).hexdigest()
            watched = [path, path/'site-packages'] if path.is_dir() else [path]
            signature = {'sid':runtime_text.value,'trees':[(str(p),p.stat().st_mtime_ns) for p in watched if p.exists()]}
            with stamp.with_suffix('.lock').open('a') as guard:
                file_lock.flock(guard,file_lock.LOCK_EX)
                try: cached = json.loads(stamp.with_suffix('.json').read_text())
                except (OSError,ValueError):cached = None
                # JSON uses lists, so compare its serialized representation.
                if json.dumps(cached,sort_keys=True)!=json.dumps(signature,sort_keys=True):
                    libraries = Path(os.environ.get('INTACT_PYTHON_LIBS',Path(sys.prefix)/'Lib/site-packages')).resolve()
                    recursive = path == libraries
                    access = f'*{runtime_text.value}:(OI)(CI)RX' if path.is_dir() and not recursive else f'*{runtime_text.value}:RX'
                    args = ['icacls.exe', str(path), '/grant', access, '/Q']
                    if recursive:args.append('/T')
                    subprocess.run(args, check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
                    stamp.with_suffix('.json').write_text(json.dumps(signature))
        for path, permission in [(input_dir, 'RX'), (output_dir, 'M')]:
            if not path.exists() or path.is_symlink():
                raise ValueError('Invalid sandbox access root: ' + str(path))
            access = f'*{sid_string}:(OI)(CI){permission}' if path.is_dir() else f'*{sid_string}:{permission}'
            args = ['icacls.exe', str(path), '/grant', access, '/Q']
            if path.is_dir():args.append('/T')
            subprocess.run(args, check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
            granted.append(path)
        subprocess.run(['icacls.exe', str(output_dir), '/setintegritylevel', '(OI)(CI)L', '/T', '/Q'], check=True, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        job = kernel.CreateJobObjectW(None, None)
        require(job)
        limits = EXTENDED_LIMIT()
        limits.BasicLimitInformation.LimitFlags = 0x2000 | 0x100 | 0x200 | 0x8 | 0x2
        limits.BasicLimitInformation.ActiveProcessLimit = 8
        limits.BasicLimitInformation.PerProcessUserTimeLimit = int(timeout * 10_000_000)
        limits.ProcessMemoryLimit = 4 * 1024**3
        limits.JobMemoryLimit = 4 * 1024**3
        require(kernel.SetInformationJobObject(job, 9, C.byref(limits), C.sizeof(limits)))
        size = C.c_size_t()
        kernel.InitializeProcThreadAttributeList(None, 2, 0, C.byref(size))
        attributes = C.create_string_buffer(size.value)
        require(kernel.InitializeProcThreadAttributeList(attributes, 2, 0, C.byref(size)))
        runtime_capability = SID_AND_ATTRIBUTES(capabilities[0], 4)
        security = SECURITY_CAPABILITIES(sid, C.cast(C.byref(runtime_capability), W.LPVOID), 1, 0)
        require(kernel.UpdateProcThreadAttribute(attributes, 0, 0x20009, C.byref(security), C.sizeof(security), None, None))
        temporary = output_dir / '.tmp'
        temporary.mkdir(exist_ok=True)
        settings = {k: os.environ[k] for k in ('USERPROFILE','LOCALAPPDATA','APPDATA','HOMEDRIVE','HOMEPATH','SystemDrive','ProgramFiles','ProgramData') if k in os.environ}
        settings.update({'SystemRoot': os.environ['SystemRoot'], 'WINDIR': os.environ['SystemRoot'],
                    'PATH': str(Path(sys.base_prefix)) + os.pathsep + str(Path(os.environ['SystemRoot'])/'System32'),
                    'TEMP': str(temporary), 'TMP': str(temporary),
                    'USERPROFILE': str(temporary), 'HOME': str(temporary),
                    'APPDATA': str(temporary), 'LOCALAPPDATA': str(temporary),
                    'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1', 'PYTHONUTF8': '1',
                    'OPENBLAS_NUM_THREADS': '1', 'OMP_NUM_THREADS': '1', 'MKL_NUM_THREADS': '1',
                    'INTACT_WORKER_INPUT': str(input_dir), 'INTACT_WORKER_OUTPUT': str(output_dir), **(env or {})})
        environment = C.create_unicode_buffer('\0'.join(f'{k}={v}' for k, v in sorted(settings.items())) + '\0\0')
        with open(os.devnull, 'rb') as stdin, log.open('ab') as stdout:
            handles = (W.HANDLE * 2)(msvcrt.get_osfhandle(stdin.fileno()), msvcrt.get_osfhandle(stdout.fileno()))
            for handle in handles:os.set_handle_inheritable(handle, True)
            require(kernel.UpdateProcThreadAttribute(attributes, 0, 0x20002, C.byref(handles), C.sizeof(handles), None, None))
            startup = STARTUPINFOEX()
            startup.StartupInfo.cb = C.sizeof(startup)
            startup.StartupInfo.lpDesktop = 'winsta0\\'+name
            startup.StartupInfo.dwFlags = 0x101
            startup.StartupInfo.wShowWindow = 0
            startup.StartupInfo.hStdInput, startup.StartupInfo.hStdOutput, startup.StartupInfo.hStdError = handles[0], handles[1], handles[1]
            startup.lpAttributeList = C.cast(attributes, W.LPVOID)
            cmd = C.create_unicode_buffer(subprocess.list2cmdline([str(x) for x in command]))
            require(adv.CreateProcessAsUserW(None,str(command[0]), cmd, None, None, True, 0x80000 | 0x400 | 0x4 | 0x10, environment, str(output_dir), C.byref(startup), C.byref(info)))
            require(kernel.AssignProcessToJobObject(job, info.hProcess))
            require(kernel.ResumeThread(info.hThread) != 0xffffffff)
            deadline = time.monotonic() + timeout
            while kernel.WaitForSingleObject(info.hProcess, 100) == 258:
                if time.monotonic() > deadline:raise TimeoutError('Isolated geometry worker timed out.')
                if any(p.stat().st_size > max_file_bytes for p in output_dir.rglob('*') if p.is_file()):
                    raise ValueError('Isolated geometry output exceeded its size limit.')
            code = W.DWORD()
            require(kernel.GetExitCodeProcess(info.hProcess, C.byref(code)))
            if any(p.stat().st_size > max_file_bytes for p in output_dir.rglob('*') if p.is_file()):
                raise ValueError('Isolated geometry output exceeded its size limit.')
            return code.value
    finally:
        if job:
            kernel.TerminateJobObject(job, 1)
        if info.hThread:kernel.CloseHandle(info.hThread)
        if info.hProcess:kernel.CloseHandle(info.hProcess)
        if job:kernel.CloseHandle(job)
        if attributes:kernel.DeleteProcThreadAttributeList(attributes)
        # Never leave a job-specific SID on the runtime or model input after exit.
        for path in reversed(granted):
            args = ['icacls.exe', str(path), '/remove:g', '*' + sid_string, '/Q']
            if path.is_dir():args.append('/T')
            subprocess.run(args, capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if sid_text:kernel.LocalFree(sid_text)
        if runtime_text:kernel.LocalFree(runtime_text)
        for i in range(group_count.value):kernel.LocalFree(groups[i])
        if groups:kernel.LocalFree(groups)
        for i in range(capability_count.value):kernel.LocalFree(capabilities[i])
        if capabilities:kernel.LocalFree(capabilities)
        if sid:adv.FreeSid(sid)
        user.DeleteAppContainerProfile(name)
        if original_station:ui.SetProcessWindowStation(original_station)
        if station_original:
            security_info=W.DWORD(4);ui.SetUserObjectSecurity(original_station,C.byref(security_info),station_original)
        if desktop:ui.CloseDesktop(desktop)
        if station:ui.CloseWindowStation(station)
        if desktop_sd:kernel.LocalFree(desktop_sd)


if __name__=='__main__':
    print(json.dumps({'returncode':_run(**json.loads(Path(sys.argv[1]).read_text(encoding='utf-8')))}))

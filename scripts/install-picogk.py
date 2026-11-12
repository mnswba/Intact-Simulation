"""Install the optional pinned Linux PicoGK TPMS bridge, outside the source checkout."""
import hashlib,json,os,shutil,subprocess,tarfile,tempfile,urllib.request
from pathlib import Path
repo=Path(__file__).resolve().parents[1];base=Path.home()/'.local/share/intact-simulation';dotnet=base/'dotnet';bridge=base/'picogk'
env={**os.environ,'DOTNET_CLI_TELEMETRY_OPTOUT':'1','DOTNET_SKIP_FIRST_TIME_EXPERIENCE':'1','DOTNET_NOLOGO':'1'}
if not (dotnet/'dotnet').exists():
 version='9.0.321';url=f'https://builds.dotnet.microsoft.com/dotnet/Sdk/{version}/dotnet-sdk-{version}-linux-x64.tar.gz'
 expected=urllib.request.urlopen(url+'.sha512').read().decode().strip().split()[0]
 with tempfile.TemporaryDirectory(prefix='intact-dotnet-') as tmp:
  archive=Path(tmp)/'dotnet.tar.gz';urllib.request.urlretrieve(url,archive)
  if hashlib.sha512(archive.read_bytes()).hexdigest()!=expected:raise ValueError('Dotnet SDK checksum mismatch.')
  dotnet.mkdir(parents=True,exist_ok=True)
  with tarfile.open(archive) as tar:tar.extractall(dotnet,filter='data')
with tempfile.TemporaryDirectory(prefix='intact-pico-build-') as tmp:
 source=Path(tmp)/'source';shutil.copytree(repo/'backend/picogk',source,ignore=shutil.ignore_patterns('bin','obj'))
 subprocess.run([str(dotnet/'dotnet'),'publish',str(source/'Intact.PicoGK.csproj'),'-c','Release','-o',str(bridge),'--nologo','-p:RestoreLockedMode=true'],env=env,check=True)
 (bridge/'intact-provenance.json').write_text(json.dumps({'package':'PicoGK','version':'2.4.0-alpha04','upstream':'https://github.com/leap71/PicoGK','license':'Apache-2.0','linux_runtime':'prerelease','source_commit':'pinned NuGet version; no binaries in source repository'}))
print('Optional PicoGK 2.4.0-alpha04 Linux bridge installed; mesh-only geometry.')

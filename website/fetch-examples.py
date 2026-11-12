"""Download only public authored example assets for local website preview."""
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import urlsplit
import json
root=Path(__file__).parent
assets=json.loads((root/'public-assets.json').read_text())
for name,url in assets.items():
 if Path(name).name!=name or not name.endswith(('.zip','.png')):raise ValueError('Unexpected example filename')
 parsed=urlsplit(url)
 if parsed.scheme!='https' or parsed.netloc!='www.intactsimulation.com':raise ValueError('Example origin changed; review before downloading')
 folder=root/'site'/('demo' if name.endswith('.zip') else 'assets');folder.mkdir(parents=True,exist_ok=True)
 target=folder/('intact-logo.png' if name=='logo.png' else name)
 if target.exists():continue
 with urlopen(Request(url,headers={'User-Agent':'Intact-public-examples/1.0'}),timeout=60) as response:data=response.read(20*1024*1024+1)
 if len(data)>20*1024*1024:raise ValueError('Example exceeds download budget')
 if name.endswith('.zip') and not data.startswith(b'PK'):raise ValueError('Example is not ZIP')
 if name.endswith('.png') and not data.startswith(b'\x89PNG\r\n\x1a\n'):raise ValueError('Image is not PNG')
 target.write_bytes(data);print('Downloaded',name)

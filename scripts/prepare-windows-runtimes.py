"""Fetch checksum-pinned portable Python and the official Windows OpenAI client."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tarfile
import urllib.request

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--stage',type=Path,required=True)
args=parser.parse_args()
base=Path(os.environ['LOCALAPPDATA'])/'IntactSimulation'
downloads=base/'downloads';downloads.mkdir(parents=True,exist_ok=True)
artifacts=[
    {'name':'python-3.12.16-windows.tar.gz','url':'https://github.com/astral-sh/python-build-standalone/releases/download/20261110/cpython-3.12.16%2B20261110-x86_64-pc-windows-msvc-install_only_stripped.tar.gz','sha256':'355ee61b8207b91574491b1c6dc9b0ebb4408fc56bfafe498f3ef439314b52dc','destination':'server'},
    {'name':'codex-0.167.2-windows.tar.gz','url':'https://github.com/openai/codex/releases/download/rust-v0.167.2/codex-package-x86_64-pc-windows-msvc.tar.gz','sha256':'20b0f94105f40b617bf209b1679b8674ab6d3d8f303e767ae43cf1860a8705da','destination':'server/client'},
]
for artifact in artifacts:
    archive=downloads/artifact['name']
    if not archive.is_file():urllib.request.urlretrieve(artifact['url'],archive)
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==artifact['sha256'],artifact['name']
    target=args.stage/artifact['destination'];target.mkdir(parents=True,exist_ok=True)
    marker=target/('.'+artifact['name']+'.verified')
    if not marker.is_file():
        with tarfile.open(archive,'r:gz') as tf:tf.extractall(target,filter='data')
        marker.write_text(artifact['sha256'])
    print('Verified',artifact['name'],flush=True)
(args.stage/'runtime-provenance.json').write_text(json.dumps(artifacts,indent=2))

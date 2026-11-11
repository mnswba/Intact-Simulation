"""Export current source into a NEW checkout, excluding private/generated workspace data.

Usage: python3 scripts/prepare-github.py /path/to/Intact-Simulation-github
The destination must not exist. This never copies the original Git history.
"""
import argparse,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE_DIRS={'outputs','node_modules','.venv','__pycache__','.pytest_cache','.git','.openai','.agents','.codex','.wrangler','.sites-runtime','.next','.vinext','dist','work','.state'}
EXCLUDE_SUFFIXES={'.sqlite3','.pyc','.AppImage','.deb','.zip','.pem','.log','.tsbuildinfo'}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('destination',type=Path);args=parser.parse_args();dest=args.destination.resolve()
    if dest.exists():parser.error('Destination already exists. Choose a new directory to preserve existing work.')
    if dest==ROOT or ROOT in dest.parents:parser.error('Choose a destination outside the working repository.')
    names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    copied=[];excluded=[]
    for name in sorted(set(filter(None,names))):
        relative=Path(name);source=ROOT/relative
        if not source.is_file():continue
        if set(relative.parts)&EXCLUDE_DIRS or source.suffix in EXCLUDE_SUFFIXES or (source.name.startswith('.env') and source.name!='.env.example'):
            excluded.append(name);continue
        if source.is_symlink():raise ValueError('Review source symlink before publication: '+name)
        target=dest/relative;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target);copied.append(name)
    subprocess.run(['git','init','--initial-branch=main',str(dest)],check=True,stdout=subprocess.DEVNULL)
    subprocess.run(['git','-C',str(dest),'remote','add','origin','https://github.com/mnswba/Intact-Simulation.git'],check=True)
    print(json.dumps({'destination':str(dest),'source_files':len(copied),'excluded':excluded},indent=2))
if __name__=='__main__':main()

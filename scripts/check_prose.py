"""Run the pinned Vale plugin checker against authored and rendered prose."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plugin-root',type=Path,required=True)
    parser.add_argument('--site',type=Path,default=Path('build/site'))
    args=parser.parse_args()
    checker=(args.plugin_root/'scripts/prose_lint.py').resolve()
    version=subprocess.run(['vale','--version'],capture_output=True,text=True,check=True).stdout.strip()
    if version!='vale version 3.23.0':
        print('Use Vale 3.23.0 to match CI.');return 2
    paths=[Path('README.md'),*Path('docs').glob('*.md'),*Path('content').glob('*.md'),*args.site.rglob('*.html')]
    if not list(args.site.rglob('*.html')):print('Build the site before checking prose.');return 2
    # The plugin excludes generated/ignored directories. Check identical copies,
    # without weakening its policy or changing files in the source snapshot.
    with tempfile.TemporaryDirectory(prefix='catalog-prose-') as directory:
        temp=Path(directory).resolve();names=[]
        for i,path in enumerate(paths):
            name=f'{i:02d}-{path.parent.name}-{path.name}'
            shutil.copyfile(path,temp/name);names.append(name)
        result=subprocess.run([sys.executable,str(checker),'--check',*names],cwd=temp,capture_output=True,text=True)
        output=(result.stdout+result.stderr).replace(str(temp)+'/', '').replace(str(Path.cwd())+'/', '')
        print(output or f'Vale: {len(paths)} files, zero warnings or errors.')
        return result.returncode


if __name__=='__main__':raise SystemExit(main())

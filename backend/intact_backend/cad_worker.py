"""Child process for trusted CAD templates. Not a sandbox for untrusted Python."""
from pathlib import Path
import sys
from .cad import build_in_process
from .spec import DesignSpec

def main():
    if sys.platform!='win32':
        import resource
        resource.setrlimit(resource.RLIMIT_CPU,(55,55))
        # Native geometry libraries reserve large virtual ranges, so use OS/container memory limits in deployment.
        resource.setrlimit(resource.RLIMIT_FSIZE,(100*1024*1024,100*1024*1024))
    build_in_process(DesignSpec.model_validate_json(Path(sys.argv[1]).read_text()),Path(sys.argv[2]))
if __name__=='__main__':main()

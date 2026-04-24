import shlex
import subprocess


def run_user_script(path: str) -> str:
    quoted = shlex.quote(path)
    out = subprocess.run(
        ["bash", "-c", f"wc -l {quoted}"],
        capture_output=True,
        text=True,
        check=False,
    )
    return out.stdout

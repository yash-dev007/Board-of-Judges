import subprocess

ALLOWED = {"status", "version", "uptime"}


def run_admin(cmd: str) -> str:
    if cmd not in ALLOWED:
        raise ValueError(f"disallowed cmd: {cmd!r}")
    out = subprocess.run(
        ["/usr/local/bin/admin", cmd],
        capture_output=True,
        text=True,
        check=False,
    )
    return out.stdout

import subprocess


def ping_host(host: str) -> str:
    out = subprocess.run(
        ["ping", "-c", "1", host],
        capture_output=True,
        text=True,
        check=False,
    )
    return out.stdout

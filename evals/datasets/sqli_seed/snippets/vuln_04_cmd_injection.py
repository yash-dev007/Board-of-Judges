import subprocess


def ping_host(host: str) -> str:
    cmd = "ping -c 1 " + host
    out = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return out.stdout

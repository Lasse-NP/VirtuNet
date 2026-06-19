import subprocess

def run(cmd, check=True):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f'Command failed: {cmd}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}')
    return result
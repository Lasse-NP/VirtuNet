import subprocess

def run(cmd, check=True):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if check and result.returncode != 0:
            raise RuntimeError(f'Command failed: {cmd}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}')
        return result
    except Exception as e:
        return False


def sudo_run(cmd, check=True):
    result = subprocess.run(f"pkexec {cmd}", shell=True, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f'Command failed: {cmd}\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}')
    return result
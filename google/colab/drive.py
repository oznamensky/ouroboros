from pathlib import Path

def mount(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)
    return path

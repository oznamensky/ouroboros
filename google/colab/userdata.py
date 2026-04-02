import os

def get(name: str):
    v = os.environ.get(name)
    if v is None:
        raise KeyError(name)
    return v

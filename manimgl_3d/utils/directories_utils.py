import importlib
import inspect
import os

def get_manimgl_3d_dir() -> str:
    manimgl_3d_module = importlib.import_module("manimgl_3d")
    manimgl_3d_dir = os.path.dirname(inspect.getabsfile(manimgl_3d_module))
    return os.path.abspath(manimgl_3d_dir)

def get_manimgl_3d_shader_dir():
    return os.path.join(get_manimgl_3d_dir(), "shaders")
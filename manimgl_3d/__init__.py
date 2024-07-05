import pkg_resources

__version__ = pkg_resources.get_distribution("manimgl_3d").version

from manimgl_3d.pbr import *
from manimgl_3d.raytracing import *
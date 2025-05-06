import numpy as np
from typing import Union, Optional, Tuple, List
from functools import cache
import moderngl as mgl
from OpenGL.GL import *
import os

from manimgl_3d.utils.gl_utils import image_path_to_texture, get_solid_texture
from manimgl_3d.utils.directories_utils import get_manimgl_3d_dir

PropertyValue = Union[float, Tuple[float], List[float], np.ndarray]
TexturePath = str

class PBRMaterial:
    supported_types = (float, tuple, list, np.ndarray, str)
    property_names = ("albedo", "roughness", "metallic", "ao", "height", "normal")  # also the order of tid
    optional_properties = ("metallic", "ao", "height", "normal")

    def __init__(
            self,
            albedo:     Union[PropertyValue, TexturePath],
            roughness:  Union[PropertyValue, TexturePath],
            metallic:   Union[PropertyValue, TexturePath] = 0.,
            ao:         Union[PropertyValue, TexturePath] = 0.3,
            height:     Union[PropertyValue, TexturePath] = 0.,
            normal:     Union[PropertyValue, TexturePath] = (0.5, 0.5, 1.),  # * 2 - 1
            *,
            height_scale = 1.0
    ):
        for data in (albedo, roughness, metallic, ao, height, normal):
            if not isinstance(data, self.supported_types):
                raise TypeError('Unsupported type for material property:', type(data))
        
        self.height_scale = height_scale
        self._property_data = {
            "albedo": albedo,
            "roughness": roughness,
            "metallic": metallic,
            "ao": ao,
            "height": height,
            "normal": normal,
        }
    
    @cache
    def get_property_texture(self, context: mgl.Context, property_name: str) -> mgl.Texture:
        data = self._property_data[property_name]
        if isinstance(data, str):
            return image_path_to_texture(context, data)
        else:
            return get_solid_texture(context, data)
    
    @cache
    def get_pbr_textures(self, context: mgl.Context) -> list:
        return [(tid, name, self.get_property_texture(context, name)) for tid, name in enumerate(self.property_names)]

    def get_property_data(self): 
        return self._property_data # should not change it
    
    # TODO: release textures?

def find_contain(str_list, flags):
    return [string for string in str_list if any([flag in string for flag in flags])]

def load_material(directory: str, *, height_scale = 1.0) -> PBRMaterial:
    file_list = os.listdir(directory)

    kwargs = {}
    for name in PBRMaterial.property_names:
        matched_files = find_contain(file_list, ['_' + name, '-' + name])
        if len(matched_files) == 1:
            kwargs[name] = os.path.join(directory, matched_files[0])
        elif len(matched_files) > 1:
            raise ValueError(f'multiple {name} texture files found:', matched_files)
        else:
            if name not in PBRMaterial.optional_properties:
                raise FileNotFoundError(f'{name} texture file not found.')
    
    return PBRMaterial(**kwargs, height_scale=height_scale)
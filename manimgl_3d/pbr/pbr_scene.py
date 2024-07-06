from manimlib import *
from manimgl_3d.camera_frame import MyCameraFrame
# from glm import *

# TODO: support multiple light sources and light types (other than point light source)
class PBRCamera(Camera):
    
    CONFIG = {
        'frame_config' : {},
    }

    def init_frame(self) -> None:
        self.frame = MyCameraFrame(**self.frame_config)

    def refresh_perspective_uniforms(self) -> None:
        frame = self.frame
        pw, ph = self.get_pixel_shape()
        fw, fh = frame.get_shape()
        # TODO, this should probably be a mobject uniform, with
        # the camera taking care of the conversion factor
        anti_alias_width = self.anti_alias_width / (ph / fh)
        # Orient light
        rotation = frame.get_inverse_camera_rotation_matrix()

        view_matrix = frame.get_view_matrix()

        self.perspective_uniforms = {
            "frame_shape":              frame.get_shape(),
            "anti_alias_width":         anti_alias_width,

            # for compatibility with Mobject
            "camera_offset":            tuple(frame.get_center()),
            "camera_rotation":          tuple(np.array(rotation).T.flatten()),
            "camera_position":          tuple(frame.get_implied_camera_location()),
            "light_source_position":    tuple(self.light_source.get_location()),
            "focal_distance":           frame.get_focal_distance(),

            # specifically for PBR objects
            "relative_focal_distance":  frame.get_focal_distance() / frame.get_scale(), # FIXED: not sure why unscale it, but it just works!
            "view":                     tuple(view_matrix.T.flatten()) # including frame scaling information
        }


class PBRScene(Scene):
    CONFIG = {
        "camera_class": PBRCamera, # SurfacePBRs should come with CameraPBR
        
        # TODO: delete it. Implemenet standalong light mobject to determine lighting setups.
        "camera_config":{
        "light_source_position" : OUT * 5 + LEFT * 5
        }

    }
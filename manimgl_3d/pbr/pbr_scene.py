from manimlib import *

# __all__ = ["PBRCamera", "PBRScene"]


# TODO: support multiple light sources and light types (other than point light source)
class PBRCamera(Camera): 
    def refresh_perspective_uniforms(self) -> None:
        frame = self.frame
        pw, ph = self.get_pixel_shape()
        fw, fh = frame.get_shape()
        # TODO, this should probably be a mobject uniform, with
        # the camera taking care of the conversion factor
        anti_alias_width = self.anti_alias_width / (ph / fh)
        # Orient light
        rotation = frame.get_inverse_camera_rotation_matrix()

        self.perspective_uniforms = {
            "frame_shape":              frame.get_shape(),
            "anti_alias_width":         anti_alias_width,
            "camera_offset":            tuple(frame.get_center()),
            "camera_rotation":          tuple(np.array(rotation).T.flatten()),
            "camera_position":          tuple(self.frame.get_implied_camera_location()),
            "light_source_position":    tuple(self.light_source.get_location()),
            "focal_distance":           frame.get_focal_distance(),
        }


class PBRScene(Scene):
    CONFIG = {
        "camera_class": PBRCamera, # SurfacePBRs should come with CameraPBR
        
        # TODO: delete it. Implemenet standalong light mobject to determine lighting setups.
        "camera_config":{
        "light_source_position" : OUT * 5 + LEFT * 5
        }

    }
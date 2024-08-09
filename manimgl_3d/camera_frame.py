from manimlib import *
from .shader_compatibility import MobjectShaderCompatibilityMixin

__all__ = ["MyCameraFrame",]

# TODO, rewrite the whole CameraFrame class, which is too counter-intuitive!
class MyCameraFrame(MobjectShaderCompatibilityMixin, CameraFrame):
    def get_scale(self):
        return self.get_height() / self.frame_shape[1] # the frame_shape contains the original shape

    def get_frame_corner(self, direction):
        coords: np.ndarray = np.sign(direction) * np.array([self.frame_shape[0], self.frame_shape[1], 0.0]) / 2.
        matrix: np.ndarray = self.get_inverse_camera_rotation_matrix()
        return self.get_center() + coords.dot(matrix)
    
    # copied from the latest version of manimgl.
    def get_view_matrix(self, refresh=False) -> np.ndarray:
        """
        Returns a 4x4 for the affine transformation mapping a point
        into the camera's internal coordinate system
        """
        # if self._data_has_changed:
        shift = np.identity(4)
        rotation = np.identity(4)
        scale_mat = np.identity(4)

        shift[:3, 3] = -self.get_center()
        rotation[:3, :3] = self.get_inverse_camera_rotation_matrix()
        scale = self.get_scale()  # IMPORTANT: here is where scale come into effect !
        if scale > 0:
            scale_mat[:3, :3] /= self.get_scale()

        self.view_matrix = np.dot(scale_mat, np.dot(rotation, shift))

        return self.view_matrix
# Manim 3D

![Static Badge](https://img.shields.io/badge/license-MIT-red) ![Static Badge](https://img.shields.io/badge/language-Python-blue) ![Static Badge](https://img.shields.io/badge/author-Evans_Li-yellow) ![Static Badge](https://img.shields.io/badge/status-work_in_progress-orange)

An extension for ManimGL, adding advanced rendering features.

**Author**: Evans Li
**Contact**: liangkeshulizi@gmail.com

## Introduction

Manim 3D is an extension for ManimGL that provides advanced rendering capabilities, including physically-based rendering (PBR) and support for complex materials and lighting effects. This extension allows you to create highly realistic 3D animations with ease.

## Demonstrations

With simple code like this, you can generate animations that looks super cool.

```python
from manimlib import *
from manimgl_3d import *

material_space_ship = load_material('./assets/spaceship-panels', height_scale = 0.5)

class TestPBRTexture(PBRScene):
    def construct(self):
        self.camera.light_source.light_color = np.array([5000.0, 5000.0, 5000.0])

        brick_wall = SquarePBR(material = material_space_ship, resolution = (1024, 1024)).scale(5)
        text = Text("Manim3D", color = RED, weight=BOLD).scale(5).shift(OUT * 1.0).rotate(180*DEGREES,axis=IN).apply_depth_test()
        theta = ValueTracker(0.)

        def light_updater(mob: Mobject):
            mob.move_to(np.array([
                10 * np.cos(theta.get_value()),
                10 * np.sin(theta.get_value()),
                5
            ]))
        self.camera.light_source.add_updater(light_updater)
        self.add(brick_wall, theta, self.camera.light_source)

        self.play(self.camera.frame.set_phi, 50*DEGREES, run_time = 1)
        self.play(self.camera.frame.set_theta, 180*DEGREES, run_time = 3)
        self.play(theta.increment_value, 360*DEGREES, run_time = 6, rate_func = linear)
        self.play(Write(text), self.camera.frame.animate.set_phi(0), run_time = 2)
        self.wait()
```

![](assets/videos/TestPBRTexture.mp4)
![](assets/videos/TestPBRTexture2.mp4)
![](assets/videos/TestPBRTexture3.mp4)

## Installation

Make sure you have correctly installed ManimGL 1.6.1, which is the only compatible version.

Clone the repository and install the package:

```sh
git clone https://github.com/liangkeshulizi/manimgl_3d_project_scr.git
pip install -e /path/to/manimgl_3d_project_scr
```

## Usage

Check out the `examples` directory for usage examples.

## Contributing

All kinds of contributions are welcome.

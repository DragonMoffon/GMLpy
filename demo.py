import random
import math
import arcade
import GML

point_mass_system = GML.System.create(4000.0, 8000.0, GML.Lens(1.0, 0.0, 0.0))
microlensing_system = GML.System.create(
    4000.0,
    8000.0,
    (
        GML.Lens(0.05, 0.0, 0.0),
        *(
            GML.Lens(
                0.05,
                math.cos(i / 15.0 * math.pi) * random.random() * point_mass_system.lens_radius,
                math.sin(i / 15.0 * math.pi) * random.random() * point_mass_system.lens_radius,
            )
            for i in range(30)
        ),
    ),
)

system = point_mass_system
lens_scaling = 180.0 / point_mass_system.lens_radius


class Window(arcade.Window):
    def __init__(self):
        super().__init__(720, 720)
        self.deflection = GML.IRSDeflectionMap(system, (1080, 1080))
        self.deflection.generate()

        self.geometry = GML.util.get_position_symmetric_geometry(self.ctx, 3.0, 3.0)
        self.program = self.ctx.load_program(
            vertex_shader=GML.util.get_glsl("UTIL_unprojected_uv_vs"),
            fragment_shader=GML.util.get_glsl("IRS_image_fs"),
        )
        self.program["source"] = 0.0, 0.0, 0.05, 0.0

    def on_update(self, delta_time: float) -> bool | None:
        x = 450.0 * math.cos((self.time / 3.0) % (2 * math.pi))

        # self.program["source"] = x / 180.0, 0.0, 0.05, 0.0

    def on_draw(self):
        self.clear()
        self.deflection.use()
        self.geometry.render(self.program)
        # arcade.draw_point(
        #    system.lenses[0].x * lens_scaling + self.center_x,
        #    system.lenses[0].y * lens_scaling + self.center_y,
        #    (255, 255, 110),
        #    12,
        # )
        for lens in system.lenses[1:]:
            pass
            # arcade.draw_point(
            #    lens.x * lens_scaling + self.center_x,
            #    lens.y * lens_scaling + self.center_y,
            #    (255, 255, 110),
            #    4,
            # )
        arcade.draw_circle_outline(self.center_x, self.center_y, 180.0, (255, 0, 0), 2.0)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        return
        self.program["source"] = (
            (x - self.center_x) / 180.0,
            (y - self.center_y) / 180.0,
            0.3,
            0.0,
        )


win = Window()
win.run()

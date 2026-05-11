from struct import pack
from random import random
from time import sleep, time
from collections.abc import Buffer

from PIL import Image
import numpy as np
from arcade import get_window, ArcadeContext
import arcade.gl as gl

from GMLID.util import get_fullscreen_geometry, get_glsl, get_symmetric_geometry
from GMLID.physics.util import Sr_to_au
from GMLID.logging import get_logger

from .system import System

logger = get_logger("physics.numerical")


class IRSDeflectionMap:
    """
    The IRSDeflectionMap (Inverse Ray Shooting Deflection Map) maps positions in
    the lens plane with their corresponding location in the source plane. This
    is used by the IRSHistogram to save on calculating the ray deflection.

    getting the deflection map texture using the `deflection_map` property won't
    automatically generate it. After updating the system or other attributes you
    must explicitly call `IRSDeflectionMap.generate()`.
    """

    def __init__(
        self,
        system: System,
        size: tuple[int, int],
        *,
        viewport: tuple[float, float] = (3.0, 3.0),
        lazy: bool = False,
        data: Buffer | None = None,
    ) -> None:
        self._system: System = system
        self._size: tuple[int, int] = size
        self._viewport: tuple[float, float] = viewport

        self._ctx: ArcadeContext

        self._lens_block: gl.Buffer
        self._lens_image: gl.Texture2D

        self._render_geometry: gl.Geometry
        self._render_program: gl.Program
        self._render_frame: gl.Framebuffer

        self._initialised: bool = False
        if not lazy or data is not None:
            self.initialise(data=data)

    def initialise(self, /, force: bool = False, data: Buffer | None = None):
        if self._initialised and not force:
            return

        self._ctx = ctx = get_window().ctx

        # 2 32-bit ints + 4 32-bit floats per lens
        size = 8 + len(self._system.lenses) * 16
        self._lens_block = ctx.buffer(reserve=size)
        self._update_lens_block()

        # Only two lens components are needed, and each component in 32-bit so this
        # saves 64-bits per pixel. Even if it does add complexity to reading the texture
        self._lens_image = ctx.texture(
            self._size,
            components=2,
            dtype="f4",
            data=data,
            wrap_x=gl.CLAMP_TO_EDGE,
            wrap_y=gl.CLAMP_TO_EDGE,
            filter=(gl.LINEAR, gl.LINEAR),
        )

        v_x, v_y = self._viewport
        self._render_geometry = get_symmetric_geometry(ctx, v_x * 2, v_y * 2)
        self._render_program = ctx.load_program(
            vertex_shader=get_glsl("UTIL_unprojected_uv_vs"),
            fragment_shader=get_glsl("IRS_deflection_map_fs"),
        )
        self._render_frame = ctx.framebuffer(color_attachments=[self._lens_image])

        self._initialised = True

    @property
    def deflection_map(self) -> gl.Texture2D:
        self.initialise()
        return self._lens_image

    @property
    def width(self) -> int:
        return self._size[0]

    @property
    def height(self) -> int:
        return self._size[1]

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @property
    def viewport_x(self) -> float:
        return self._viewport[0]

    @property
    def viewport_y(self) -> float:
        return self._viewport[1]

    @property
    def viewport(self) -> tuple[float, float]:
        return self._viewport

    @property
    def system(self) -> System:
        return self._system

    def _update_lens_block(self):
        count = len(self._system.lenses)
        self._lens_block.write(pack(f"2i {count * 4}f", count, 0, *self._system.pack_lenses()))

    def update_system(self, system: System):
        self.initialise()
        old = self._system
        self._system = system

        old_count = len(old.lenses)
        count = len(system.lenses)

        if old_count != count:
            # 2 32-bit ints + 4 32-bit floats per lens
            size = 8 + len(system.lenses) * 16
            self._lens_block.orphan(size)

        self._update_lens_block()

    def generate(self):
        self.initialise()

        self._ctx.disable(gl.BLEND)
        with self._render_frame.activate() as fbo:
            fbo.clear()
            self._lens_block.bind_to_storage_buffer()
            self._render_geometry.render(self._render_program)

    def use(self, unit: int = 0):
        self.initialise()
        self._lens_image.use(unit)

    def read(self) -> np.ndarray:
        data = self._lens_image.read()
        w, h = self._size
        return np.frombuffer(data, dtype=np.float32, count=w * h * 2).reshape((w, h, 2))[::-1, :]

    def capture(
        self, distance_range: float = 2.0, clipped: bool = True, blue_value: float = 127
    ) -> Image.Image:
        # maps -distance_range/2 - distance_range/2 to 0.0 - 1.0
        data = (self.read() / distance_range + 0.5) * 255
        if clipped:
            data = np.clip(data, 0.0, 255.0)
        pixels = np.zeros((self._size[0], self._size[1], 3), dtype=np.float32)
        pixels[::-1, ::, :2] = data  # set Red and Green values
        pixels[:, :, 2] = blue_value  # set Blue values
        img = Image.fromarray(pixels.astype(np.uint8), "RGB")
        return img


class IRSHistogram:
    """
    The IRSHistogram (Inverse Ray Shooting Histogram) produces caustic maps
    for the given LensSystem. This is an iterative process where a relatively
    small (~1 million) number of rays are shot towards the source plane. For each
    location (in eistein angles) the number of rays that land is stored. when
    the texture is then copied to the CPU from the GPU the pixels are transformed
    to be as a fraction of the maximum number of counted rays.

    To generate the image a number of iterations can be specified, or a single
    iteration can be called to generate the histogram over time.

    When properties of the LensSystem change the histogram has to be flushed.
    This is an expensive operation so avoid doing it more than necessary.

    There are two methods for calculating where in the source plane the image lands.
    Firstly a "deflection map" can be generated which computes the deflection at set
    angles. This is then interpolated for interim positions. The second is to compute
    the deflection for each ray directly. This is more costly, but more accurate.
    """

    def __init__(
        self,
        count: int,
        size: tuple[int, int],
        deflection_map: IRSDeflectionMap,
        *,
        viewport: tuple[float, float] = (2.0, 2.0),
        delay: float | None = None,
        lazy: bool = False,
        iterations: int = 0,
        data: Buffer | None = None,
    ) -> None:
        self._size: tuple[int, int] = size
        self._viewport: tuple[float, float] = viewport
        self._ray_count: int = count
        self._delay: float | None = delay

        self._iterations: int = iterations

        self._ctx: ArcadeContext

        self._deflection_map: IRSDeflectionMap = deflection_map
        self._histogram: gl.Texture2D

        self._ray_geometry: gl.Geometry
        self._ray_program: gl.Program
        self._ray_frame: gl.Framebuffer

        self._initialised: bool = False
        if not lazy or data is not None:
            self.initialise(data=data)

    def initialise(self, /, force: bool = True, data: Buffer | None = None):
        if self._initialised and not force:
            return

        self._ctx = ctx = get_window().ctx
        self._histogram = ctx.texture(self._size, components=1, dtype="f4", data=data)

        # Evenly space x rays between 0.0 and 1.0 (exclusive)
        # This places the ray's at the center of pixels if the ray count matches the size
        # On th GPU these use the deflection to find the final location
        # in the output histogram.
        count = self._ray_count
        x = np.linspace(0.5 / count, 1.0 - 0.5 / count, self._ray_count, dtype=np.float32)
        xy, yx = np.meshgrid(x, x)
        rays = np.asarray((xy, yx)).transpose((1, 2, 0))  # create 2d array of x,y positions
        self._ray_geometry = ctx.geometry(
            [gl.BufferDescription(ctx.buffer(data=rays.tobytes()), "2f", ["origin"])],
            mode=gl.POINTS,
        )

        self._ray_program = ctx.load_program(
            vertex_shader=get_glsl("IRS_histogram_vs"), fragment_shader=get_glsl("IRS_histogram_fs")
        )
        self._ray_program["shift"] = (1.0 / count, 1.0 / count)
        self._ray_program["scale"] = 1.0 / self._viewport[0], 1.0 / self._viewport[1]
        self._ray_frame = ctx.framebuffer(color_attachments=(self._histogram))

    @property
    def histogram(self) -> gl.Texture2D:
        return self._histogram

    @property
    def ray_count(self) -> int:
        return self._ray_count

    @property
    def width(self) -> int:
        return self._size[0]

    @property
    def height(self) -> int:
        return self._size[1]

    @property
    def size(self) -> tuple[int, int]:
        return self._size

    @property
    def viewport_x(self) -> float:
        return self._viewport[0]

    @property
    def viewport_y(self) -> float:
        return self._viewport[1]

    @property
    def viewport(self) -> tuple[float, float]:
        return self._viewport

    @property
    def iterations(self) -> int:
        return self._iterations

    @property
    def delay(self) -> float | None:
        return self._delay

    @property
    def deflection_map(self) -> IRSDeflectionMap:
        return self._deflection_map

    @property
    def system(self) -> System:
        return self._deflection_map.system

    def clear(self):
        self._iterations = 0
        self._ray_frame.clear()

    def step(self):
        # Set the blend mode to additive so it counts the number of rays that
        # hit each pixel
        self._ctx.blend_func = gl.BLEND_ADDITIVE
        self._ctx.enable(gl.BLEND)

        # Set the ray size to 1 pixel square
        self._ctx.point_size = 1

        with self._ray_frame.activate():
            # Bind the deflection map to be used by the program, and set the random
            # seed used to adjust the ray positions
            self._deflection_map.use()
            self._ray_program["seed"] = random()
            self._ray_geometry.render(self._ray_program)

        self._ctx.disable(gl.BLEND)
        self._iterations += 1
        logger.debug("IRSHistogram finished single step. [Total Iterations = %i]", self._iterations)

    def generate(self, iterations: int = 1000, flush: bool = False):
        self.initialise()
        if flush:
            self._ray_frame.clear()

        # Set the blend mode to additive so it counts the number of rays that
        # hit each pixel
        self._ctx.blend_func = gl.BLEND_ADDITIVE
        self._ctx.enable(gl.BLEND)

        # Set the ray size to 1 pixel square
        self._ctx.point_size = 1

        with self._ray_frame.activate():
            # Bind the deflection map to be used by the program
            self._deflection_map.deflection_map.use()
            for i in range(iterations):
                # set the random seed used to adjust the ray positions
                self._ray_program["seed"] = random()
                self._ray_geometry.render(self._ray_program)

                # Wait until the gpu is finished or a set amount of time
                # as to not overload the GPU. Can have major performance hits
                if self._delay is None:
                    self._ctx.finish()
                elif self._delay:
                    sleep(self._delay)
                self._iterations += 1
                logger.debug(
                    f"IRSHistogram generation step {i + 1} ({100 * (i + 1) / iterations:.1f}%) [Total Iterations = {self._iterations}]"
                )

        self._ctx.disable(gl.BLEND)
        logger.debug(f"IRSHistogram finished generation. [Total Iterations = {self._iterations}]")

    def flush(self):
        self._ray_frame.clear()

    def read(self, normalised: bool = False, flip_y: bool = False) -> np.ndarray:
        data = self._histogram.read()
        w, h = self._size
        array = np.frombuffer(data, dtype=np.float32, count=w * h).reshape((h, w))
        if flip_y:
            array = array[::-1, :]
        cap = 1.0 if not normalised else np.max(array)
        return array / cap

    def capture(self) -> Image.Image:
        return Image.fromarray((self.read(True) * 255.0).astype(np.uint8), "L").convert("RGB")

    def __str__(self) -> str:
        return f"Inverse Ray Shooting Histogram<Rays:{self.ray_count**2}, Iterations:{self._iterations}, Size=({self.width},{self.height})>"


class IRSCriticalMap:
    """
    The IRSCritical (Inverse Ray Shooting Critical [Curve] Map) produces a critical
    curve map from the IRSHistogram for a specific system. It first generates a histogram
    for the caustic curve, and then resamples that to create the critical curve map.
    """

    def __init__(self, histogram: IRSHistogram, lazy: bool = False) -> None:
        self._histogram: IRSHistogram = histogram

        self._critical_map: gl.Texture2D
        self._render_frame: gl.Framebuffer
        self._render_geometry: gl.Geometry
        self._render_program: gl.Program

        self._initialised: bool = False
        if not lazy:
            self._initialise()

    def _initialise(self, force: bool = False):
        if self._initialised and not force:
            return

        ctx = get_window().ctx

        self._critical_map = ctx.texture(
            (self._histogram.width, self._histogram.height), components=1, dtype="f4"
        )

        self._render_frame = ctx.framebuffer(color_attachments=self._critical_map)
        self._render_geometry = get_fullscreen_geometry(ctx)
        self._render_program = ctx.load_program(
            vertex_shader=get_glsl("UTIL_unprojected_uv_vs"),
            fragment_shader=get_glsl("IRS_critical_fs"),
        )
        self._render_program["deflectionMap"] = 0
        self._render_program["causticMap"] = 1

        self._initialised = True

    @property
    def critical_map(self) -> gl.Texture2D:
        return self._critical_map

    def generate(self):
        self._initialise()
        with self._render_frame.activate() as fbo:
            fbo.clear()
            # TODO: handle non-deflection map mode
            self._histogram._deflection_map.deflection_map.use(0)
            self._histogram.histogram.use(1)
            self._render_geometry.render(self._render_program)

    def read(self) -> np.ndarray:
        data = self._critical_map.read()
        w, h = self._critical_map.size
        array = np.frombuffer(data, dtype=np.float32, count=w * h).reshape((w, h))[::-1]
        cap = np.max(array)
        return array / cap

    def capture(self) -> Image.Image:
        return Image.fromarray((self.read() * 255.0).astype(np.uint8), "L").convert("RGB")


def create_caustic_map(histogram: IRSHistogram, source_radius: float) -> np.ndarray:
    x_overlap = histogram.ray_count * histogram.viewport_x / histogram.deflection_map.viewport_x
    y_overlap = histogram.ray_count * histogram.viewport_y / histogram.deflection_map.viewport_y
    ray_overlap = x_overlap * y_overlap

    w, h = histogram.width, histogram.height
    ray_density = ray_overlap / (w * h)

    caustic = np.zeros((h, w))

    system = histogram.system
    source_radius = source_radius * Sr_to_au
    logger.debug("Source Radius in Astronomical Units: %s", source_radius)
    rays_per_pixel = histogram.iterations * ray_density
    # pixel resolution is in units per pixel
    pixel_resolution = (
        2 * histogram.viewport_x * system.source_radius / w,
        2 * histogram.viewport_y * system.source_radius / h,
    )
    logger.debug("pixel resolution: %s", pixel_resolution)
    source_width = source_radius / pixel_resolution[0]
    source_height = source_radius / pixel_resolution[1]
    logger.debug("source size: (%s , %s)", source_width, source_height)

    # make convolution grid odd if histogram is odd (only true for FT based convolution)
    convolution_width = np.ceil(source_width) + 0.5  # (0.5 if w % 2 else 0.0)
    convolution_height = np.ceil(source_height) + 0.5  # (0.5 if h % 2 else 0.0)

    kernel_x = np.asarray(range(int(2 * convolution_height)))
    kernel_y = np.asarray(range(int(2 * convolution_height)))

    kernel_yy, kernel_xx = np.meshgrid(kernel_y, kernel_x)
    dx = (kernel_xx - convolution_width + 0.5) * pixel_resolution[0]
    dy = (kernel_yy - convolution_height + 0.5) * pixel_resolution[1]

    kernel = (dx**2 + dy**2 <= source_radius**2) / rays_per_pixel

    logger.debug("computed kernel")

    idx_x = np.asarray(range(w))
    idx_y = np.asarray(range(h))

    # Get Area Bounds for each (x, y) and constrain them to within the histogram
    s_x = np.clip(idx_x + int(np.ceil(-convolution_width)), 0, w)
    e_x = np.clip(idx_x + int(np.ceil(convolution_width)), 0, w)

    ks_x = np.clip(int(np.ceil(convolution_width)) - idx_x - 1, 0, kernel.shape[1])
    ke_x = np.clip(w + int(np.ceil(convolution_width)) - idx_x - 1, 0, kernel.shape[1])

    s_y = np.clip(idx_y + int(np.ceil(-convolution_height)), 0, h)
    e_y = np.clip(idx_y + int(np.ceil(convolution_height)), 0, h)

    ks_y = np.clip(int(np.ceil(convolution_height)) - idx_y - 1, 0, kernel.shape[0])
    ke_y = np.clip(h + int(np.ceil(convolution_height)) - idx_y - 1, 0, kernel.shape[0])

    logger.debug("computed kernel masks")

    conv_start = time()
    histogram_data = histogram.read()

    logger.debug("starting convolution")
    for x in idx_x:
        for y in idx_y:
            area = histogram_data[s_y[y] : e_y[y], s_x[x] : e_x[x]]
            kern = kernel[ks_y[y] : ke_y[y], ks_x[x] : ke_x[x]]
            caustic[y, x] = np.sum(area * kern)

    logger.info("finished convolution in %s seconds", time() - conv_start)

    return caustic


class IRSCausticMap:
    """
    The IRSCausticMap (Inverse Ray Shooting Caustic Map) uses an IRSHistogram to
    compute the magnification at each pixel. This is done by taking the ratio between
    the deflected ray count and the undeflected ray count for each pixel. The number of
    rays per pixel is equal to the ray density times the number of iterations done.
    """

    def __init__(self, histogram: IRSHistogram, source_radius: float) -> None:
        self._histogram: IRSHistogram = histogram
        self._source_radius: float = source_radius  # radius of source star in Solar Radii
        # How many rays would land in the histogram if there is no deflection
        x_overlap = histogram.ray_count * histogram.viewport_x / histogram.deflection_map.viewport_x
        y_overlap = histogram.ray_count * histogram.viewport_y / histogram.deflection_map.viewport_y
        ray_overlap = x_overlap * y_overlap
        # How many rays per pixel are there for one iteration.
        self._ray_density = ray_overlap / (self._histogram.width * self._histogram.height)

        self._caustic: np.ndarray = np.zeros((histogram.height, histogram.width))

    @property
    def caustic(self) -> np.ndarray:
        return self._caustic

    def generate(self):
        system = self._histogram.system
        source_radius = self._source_radius * Sr_to_au
        logger.debug("Source Radius in Astronomical Units: %s", source_radius)
        logger.debug("Source Radius in Einstein Radii: %s", source_radius / system.source_radius)
        rays_per_pixel = self._histogram.iterations * self._ray_density
        w, h = self._histogram.width, self._histogram.height
        # pixel resolution is in units per pixel
        pixel_resolution = (
            2 * self._histogram.viewport_x * system.source_radius / w,
            2 * self._histogram.viewport_y * system.source_radius / h,
        )
        logger.debug("pixel resolution: %s", pixel_resolution)
        source_width = source_radius / pixel_resolution[0]
        source_height = source_radius / pixel_resolution[1]
        logger.debug("source size: (%s , %s)", source_width, source_height)

        # make convolution grid odd if histogram is odd (only true for FT based convolution)
        convolution_width = np.ceil(source_width) + 0.5  # (0.5 if w % 2 else 0.0)
        convolution_height = np.ceil(source_height) + 0.5  # (0.5 if h % 2 else 0.0)

        kernel_x = np.asarray(range(int(2 * convolution_height)))
        kernel_y = np.asarray(range(int(2 * convolution_height)))

        kernel_yy, kernel_xx = np.meshgrid(kernel_y, kernel_x)
        dx = (kernel_xx - convolution_width + 0.5) * pixel_resolution[0]
        dy = (kernel_yy - convolution_height + 0.5) * pixel_resolution[1]

        kernel = (dx**2 + dy**2 <= source_radius**2) / rays_per_pixel

        logger.debug("computed kernel")

        idx_x = np.asarray(range(w))
        idx_y = np.asarray(range(h))

        # Get Area Bounds for each (x, y) and constrain them to within the histogram
        s_x = np.clip(idx_x + int(np.ceil(-convolution_width)), 0, w)
        e_x = np.clip(idx_x + int(np.ceil(convolution_width)), 0, w)

        ks_x = np.clip(int(np.ceil(convolution_width)) - idx_x - 1, 0, kernel.shape[1])
        ke_x = np.clip(w + int(np.ceil(convolution_width)) - idx_x - 1, 0, kernel.shape[1])

        s_y = np.clip(idx_y + int(np.ceil(-convolution_height)), 0, h)
        e_y = np.clip(idx_y + int(np.ceil(convolution_height)), 0, h)

        ks_y = np.clip(int(np.ceil(convolution_height)) - idx_y - 1, 0, kernel.shape[0])
        ke_y = np.clip(h + int(np.ceil(convolution_height)) - idx_y - 1, 0, kernel.shape[0])

        logger.debug("computed kernel masks")

        conv_start = time()
        histogram = self._histogram.read()

        logger.debug("starting convolution")
        for x in idx_x:
            for y in idx_y:
                area = histogram[s_y[y] : e_y[y], s_x[x] : e_x[x]]
                kern = kernel[ks_y[y] : ke_y[y], ks_x[x] : ke_x[x]]
                self._caustic[y, x] = np.sum(area * kern)

        logger.info("finished convolution in %s seconds", time() - conv_start)

        return self._caustic

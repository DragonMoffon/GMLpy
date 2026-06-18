from struct import pack
from random import random
from time import sleep
from collections.abc import Buffer

from PIL import Image
import numpy as np
from arcade import get_window, ArcadeContext
import arcade.gl as gl

from GML.util import get_fullscreen_geometry, get_glsl, get_symmetric_geometry
from GML.physics import Sr_to_au
from GML.logging import get_logger

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
    # Compute how many rays would land at each pixel if there was no lens system
    x_overlap = histogram.ray_count * histogram.viewport_x / histogram.deflection_map.viewport_x
    y_overlap = histogram.ray_count * histogram.viewport_y / histogram.deflection_map.viewport_y
    ray_overlap = x_overlap * y_overlap

    w, h = histogram.width, histogram.height
    rays_per_pixel = histogram.iterations * ray_overlap / (w * h)

    # Find radius of the source object in Au
    system = histogram.system
    source_radius = source_radius * Sr_to_au
    logger.debug(f"Source Radius in Astronomical Units: {source_radius}")

    # Get Au half width and height of the source plane
    source_halfwidth = histogram.viewport_x * system.source_radius
    source_halfheight = histogram.viewport_y * system.source_radius

    # Create grid of x, y Au positions in the source plane
    grid_x = np.linspace(-source_halfwidth, source_halfwidth, w)
    grid_y = np.linspace(-source_halfheight, source_halfheight, h)
    grid_yy, grid_xx = np.meshgrid(grid_y, grid_x)

    # Compare the (x, y) positions with the radius of the source at (0, 0)
    # For each pixel inside the star store the inverse fraction of the rays per pixel
    # Then take the fourier transform of the kernel
    kernel = (grid_xx**2 + grid_yy**2 <= source_radius**2) / rays_per_pixel
    kernel_fourier = np.fft.fftshift(np.fft.fft2(kernel))

    # Fetch the histogram results and apply the fourier transform
    result = histogram.read()
    ray_mean = np.mean(result)
    logger.debug(f"IRSHistogram mean ray count: {ray_mean}")
    result_fourier = np.fft.fftshift(np.fft.fft2(result - ray_mean))

    # Multiply the fourier transforms of the kernel and results together
    # This is equivalent to the convolution of the original kernel and results
    caustic_foutier = kernel_fourier * result_fourier
    caustic = np.fft.ifft2(np.fft.ifftshift(caustic_foutier))

    # The input histogram and final caustic are purely real.
    # The complex part are tiny e-13 -> e-15, and `abs` ensures
    # dtype is float not complex
    return abs(np.fft.fftshift(caustic) + ray_mean)

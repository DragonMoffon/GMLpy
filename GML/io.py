from pathlib import Path

from tomli_w import dump as dump_toml
from tomllib import load as load_toml

from GML.logging import get_logger
from .numerical import IRSDeflectionMap, IRSHistogram
from .system import Lens, System

logger = get_logger("io")
try:
    from astropy.io import fits

    _USE_FITS = True
except ImportError:
    logger.warning("Failed to import astropy.io.fits falling back on raw format")

    fits = None
    _USE_FITS = False
finally:
    import struct


def convert_to_fits(location: Path, name: str):
    if _USE_FITS is False:
        logger.exception("Cannot convert the raw to fits as astropy failed to import")
        return None


def _dump_histogram_fits(path: Path, histogram: IRSHistogram):
    pass


_SYSTEM_INFO_SIZE = struct.calcsize("q2d")
_LENS_SIZE = struct.calcsize("3d")

_DEFLECTION_SIZE = struct.calcsize("2q")
_HISTOGRAM_SIZE = struct.calcsize("4q3d")  # ray count, iterations, size, viewport [x, y], delay


def _dump_histogram_raw(path: Path, histogram: IRSHistogram):
    header = b"type histogram"

    deflection_map = histogram._deflection_map
    system = deflection_map._system
    count = len(system.lenses)

    system_size = _SYSTEM_INFO_SIZE + count * _LENS_SIZE
    system_info = b"system          " + struct.pack(
        f">qq2d{3 * count}d",
        system_size,
        count,
        system.lens_distance,
        system.source_distance,
        *(val for lens in system.lenses for val in lens),
    )

    deflection_size = _DEFLECTION_SIZE + 8 * deflection_map.width * deflection_map.height
    deflection_info = (
        b"deflection      "
        + struct.pack(">3q", deflection_size, deflection_map.width, deflection_map.height)
        + deflection_map.deflection_map.read()
    )

    histogram_size = _HISTOGRAM_SIZE + 4 * histogram.width * histogram.height
    histogram_info = (
        b"histogram       "
        + struct.pack(
            ">5q3d",
            histogram_size,
            histogram.ray_count,
            histogram.iterations,
            histogram.width,
            histogram.height,
            histogram.viewport_x,
            histogram.viewport_y,
            float("nan") if histogram.delay is None else histogram.delay,
        )
        + histogram.histogram.read()
    )

    with open(path, "wb") as fp:
        fp.write(header + system_info + deflection_info + histogram_info)


def dump_histogram(location: Path, name: str, histogram: IRSHistogram):
    if _USE_FITS:
        return _dump_histogram_fits(location / f"{name}.fits", histogram)
    return _dump_histogram_raw(location / f"{name}.histogram", histogram)


def _load_histogram_fits(path: Path) -> IRSHistogram | None: ...


def _load_histogram_raw(path: Path) -> IRSHistogram | None:
    with open(path, "rb") as fp:
        data = fp.read()

    if data[:14] != b"type histogram":
        logger.critical(f"{path} is not a valid histogram file")
        return None

    def _load_raw_block(start: int) -> tuple[str, bytes, int]:
        block_type = str(data[start : start + 16]).strip()
        block_size = int.from_bytes(data[start + 16 : start + 24])
        block_data = data[start + 24 : start + 24 + block_size]
        return block_type, block_data, start + 24 + block_size

    _, system_data, pointer = _load_raw_block(14)
    count, lens_dist, source_dist = struct.unpack(">qddd", system_data[:24])
    l_data = struct.unpack(f">{3 * count}d", system_data[24:])
    lenses = (Lens(l_data[3 * i], l_data[3 * i + 1], l_data[3 * i + 2]) for i in range(count))

    system = System.create(lens_dist, source_dist, lenses)

    _, deflection_data, pointer = _load_raw_block(pointer)

    d_width = int.from_bytes(deflection_data[0:8])
    d_height = int.from_bytes(deflection_data[8:16])
    deflection = IRSDeflectionMap(system, (d_width, d_height), data=deflection_data[16:])

    _, histogram_data, pointer = _load_raw_block(pointer)
    h_count, h_iter, h_width, h_height, h_v_x, h_v_y, h_delay = struct.unpack(
        ">4q3d", histogram_data[0:56]
    )
    h_delay = None if h_delay == float("nan") else h_delay
    histogram = IRSHistogram(
        h_count,
        (h_width, h_height),
        deflection,
        viewport=(h_v_x, h_v_y),
        delay=h_delay,
        iterations=h_iter,
        data=histogram_data[56:],
    )

    return histogram


def load_histogram(location: Path, name: str) -> IRSHistogram | None:
    if _USE_FITS:
        return _load_histogram_fits(location / f"{name}.fits")
    return _load_histogram_raw(location / f"{name}.histogram")


def dump_system(location: Path | str, system: System):
    data = {
        "lens_distance": system.lens_distance,
        "source_distance": system.source_distance,
        "lenses": [{"mass": lens.m, "x": lens.x, "y": lens.y} for lens in system.lenses],
        "calculated": {
            "mass": system.mass,
            "com": (system.com_x, system.com_y),
            "einstein_angle": system.einstein_angle,
            "lens_radius": system.lens_radius,
            "source_radius": system.source_radius,
        },
    }

    with open(location, "wb") as fp:
        dump_toml(data, fp)


def load_system(location: Path | str) -> System | None:
    with open(location, "rb") as fp:
        data = load_toml(fp)

    if "lens_distance" not in data or "source_distance" not in data:
        logger.exception("Missing required Lens and Source Distance to create System")
        return None

    lenses = (Lens(lens["mass"], lens["x"], lens["y"]) for lens in data.get("lenses", ()))

    return System.create(data["lens_distance"], data["source_distance"], lenses)

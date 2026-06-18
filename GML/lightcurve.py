import numpy as np
import numpy.typing as npt


def get_light_curve_points(
    steps: int,
    start: tuple[float, float],
    end: tuple[float, float],
):
    t = np.linspace(0.0, 1.0, steps)
    x = (1 - t) * start[0] + t * end[0]
    y = (1 - t) * start[1] + t * end[1]

    return x, y


def get_light_curve_indices(
    x: npt.NDArray[np.float64],
    y: npt.NDArray[np.float64],
    width: int,
    height: int,
    domain: tuple[float, float, float, float],
):
    # normalise to 0.0 - 1.0
    x = (x - domain[0]) / (domain[1] - domain[0])
    y = (y - domain[2]) / (domain[3] - domain[2])

    # expand to be indexable, the 0.5 and -1 are to account for indexing going from 0 to s-1
    return (0.5 + (width - 1) * x).astype(np.int64), (0.5 + (height - 1) * y).astype(np.int64)


def get_light_curve(
    source: npt.NDArray,
    steps: int,
    start: tuple[float, float],
    end: tuple[float, float],
    domain: tuple[float, float, float, float] = (-2.0, 2.0, -2.0, 2.0),
) -> npt.NDArray[np.float64]:
    x, y = get_light_curve_points(steps, start, end)
    ix, iy = get_light_curve_indices(x, y, source.shape[0], source.shape[1], domain)
    return source[iy, ix]

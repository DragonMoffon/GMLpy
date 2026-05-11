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


def get_light_curve(
    source: npt.NDArray,
    steps: int,
    start: tuple[float, float],
    end: tuple[float, float],
    domain: tuple[float, float, float, float] = (-2.0, 2.0, -2.0, 2.0),
) -> npt.NDArray[np.float64]:
    # TODO: allow for more than 2 points

    x, y = get_light_curve_points(steps, start, end)
    width, height = source.shape

    # normalise to 0.0 - 1.0
    x = (x - domain[0]) / (domain[1] - domain[0])
    y = (y - domain[2]) / (domain[3] - domain[2])

    # expand to be indexable, the 0.5 and -1 are to account for indexing going from 0 to s-1
    x = (0.5 + (width - 1) * x).astype(np.int64)
    y = (0.5 + (height - 1) * y).astype(np.int64)

    return source[x, y]


_solve_polynomial((1, 1), (2, 4), (3, 7), (4, 12), (5, 6), (7, 9))

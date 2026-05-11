from struct import pack
from importlib.resources import path
from pathlib import Path

from arcade import ArcadeContext
import arcade.gl as gl
import numpy as np

import GMLID.glsl as glsl_module


def get_glsl(name: str) -> Path:
    with path(glsl_module, f"{name}.glsl") as pth:
        return pth


def get_symmetric_byte_data(width: float, height: float):
    return pack(
        "16f",
        -1.0,
        -1.0,
        -width / 2,
        -height / 2,
        -1.0,
        1.0,
        -width / 2,
        height / 2,
        1.0,
        -1.0,
        width / 2,
        -height / 2,
        1.0,
        1.0,
        width / 2,
        height / 2,
    )


def get_position_symmetric_byte_data(width: float = 2.0, height: float = 2.0):
    return pack(
        "16f",
        -width / 2,
        -height / 2,
        0.0,
        0.0,
        -width / 2,
        height / 2,
        0.0,
        1.0,
        width / 2,
        -height / 2,
        1.0,
        0.0,
        width / 2,
        height / 2,
        1.0,
        1.0,
    )


def get_symmetric_geometry(ctx: ArcadeContext, width: float, height: float):
    return ctx.geometry(
        [
            gl.BufferDescription(
                ctx.buffer(data=get_symmetric_byte_data(width, height)), "4f", ["in_coordinate"]
            )
        ],
        mode=gl.TRIANGLE_STRIP,
    )


def get_position_symmetric_geometry(ctx: ArcadeContext, width: float, height: float):
    return ctx.geometry(
        [
            gl.BufferDescription(
                ctx.buffer(data=get_position_symmetric_byte_data(width, height)),
                "4f",
                ["in_coordinate"],
            )
        ],
        mode=gl.TRIANGLE_STRIP,
    )


def get_uv_byte_data():
    return pack(
        "16f", -1.0, -1.0, 0.0, 0.0, -1.0, 1.0, 0.0, 1.0, 1.0, -1.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0
    )


def get_fullscreen_geometry(ctx: ArcadeContext):
    return ctx.geometry(
        [gl.BufferDescription(ctx.buffer(data=get_uv_byte_data()), "4f", ["in_coordinate"])],
        mode=gl.TRIANGLE_STRIP,
    )


def get_intersection_points(
    origin: tuple[float, float],
    angle: float,
    left: float,
    right: float,
    bottom: float,
    top: float,
) -> tuple[tuple[float, float], tuple[float, float]]:
    c, s = np.cos(angle), np.sin(angle)

    # Protect against div by 0.0
    if s == 0.0:
        point_1, point_2 = (left, origin[1]), (right, origin[1])
        return (point_1, point_2) if 0.0 <= c else (point_2, point_1)
    elif c == 0.0:
        point_1, point_2 = (origin[0], bottom), (origin[0], top)
        return (point_1, point_2) if 0.0 <= s else (point_2, point_1)

    slope, inv_s = s / c, c / s  # slope of line and its inverse

    y1 = origin[1] - slope * (origin[0] - left)  # first intersection point (x = 0)
    x2 = origin[0] - inv_s * (origin[1] - bottom)  # second intersection point (y = 0)
    y3 = origin[1] + slope * (right - origin[0])  # third intersection point (x = width)
    x4 = origin[0] + inv_s * (top - origin[1])  # final intersection point (y = height)

    if slope > 0.0:
        point_1 = (left, y1) if bottom <= y1 <= top else (x2, bottom)
        point_2 = (right, y3) if bottom <= y3 <= top else (x4, top)
    else:
        point_1 = (left, y1) if bottom <= y1 <= top else (x4, top)
        point_2 = (right, y3) if bottom <= y3 <= top else (x2, bottom)

    # when cos(angle) is less than 0.0 that represents an angle > 180 which means the line
    # goes from right to left rather than left to right
    return (point_1, point_2) if 0.0 < c else (point_2, point_1)


def _solve_polynomial(*points: tuple[float, float]):
    matrix = np.asarray(
        [[point[0] ** i for i in range(len(points))] for point in points], np.float64
    )
    inverse = np.linalg.inv(matrix)
    return inverse @ tuple(point[1] for point in points)

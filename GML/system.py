"""
The lens system that causes the light to bend.

It is stored as a representation of the actual system, that is masses are
stored in solar masses, and distances are in Au and Parsecs.

The Packed data sent to the GPU is instead fractional based on the
mass fraction and Einstein angle.
"""

from typing import Generator, Iterator, Iterable, Self
from dataclasses import dataclass
from math import tan

from GML.physics import calculate_einstein_angle, pc_to_au
from GML.logging import get_logger

logger = get_logger("physics.system")


@dataclass(frozen=True)
class Lens:
    m: float  # In Solar Masses (M*)
    x: float  # In Astronomical Units (Au)
    y: float  # In Astronomical Units (Au)

    def __iter__(self) -> Iterator[float]:
        return iter((self.m, self.x, self.y))


@dataclass(frozen=True)
class System:
    # Input Values
    lens_distance: float  # In parsecs (pc)
    source_distance: float  # In parsces (pc)
    lenses: tuple[Lens, ...]

    # Mass
    mass: float  # In solar masses (M*)
    com_x: float  # In Astronomical units (Au)
    com_y: float  # In Astronomical units (Au)

    # Radii
    einstein_angle: float  # In radians (rad)
    lens_radius: float  # In Astronomical units (Au)
    source_radius: float  # In Astronomical units (Au)

    @classmethod
    def create(
        cls,
        lens_distance: float,
        source_distance: float,
        lenses: Iterable[Lens] | Lens,
    ) -> Self:
        """
        Create a lens system, and precalculate values required in calculations.
        """
        if source_distance <= lens_distance:
            logger.critical(
                "The distance to the source must be strictly greater than the distance to the lens"
            )
            raise ValueError(
                "The distance to the source must be strictly greater than the distance to the lens"
            )

        lenses = (lenses,) if isinstance(lenses, Lens) else tuple(lenses)
        if len(lenses) == 0:
            return cls(lens_distance, source_distance, (), 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

        # Collect the total mass and center of mass
        mass = com_x = com_y = 0.0
        for lens in lenses:
            mass += lens.m
            com_x += lens.x * lens.m
            com_y += lens.y * lens.m
        if mass <= 0.0:
            logger.critical(
                f"total system mass ({mass}) is invalid. Ensure all lenses have mass, and none are negative."
            )
            raise ValueError(
                f"total system mass ({mass}) is invalid. Ensure all lenses have mass, and none are negative."
            )

        com_x /= mass
        com_y /= mass

        # * Calculation of the Einstein angle is differed to GML.util as it optimises
        # * for floating point imprecision.
        einstein_angle = calculate_einstein_angle(mass, lens_distance, source_distance)
        lens_radius = pc_to_au * (lens_distance * tan(einstein_angle))
        source_radius = pc_to_au * (source_distance * tan(einstein_angle))

        return cls(
            lens_distance,
            source_distance,
            lenses,
            mass,
            com_x,
            com_y,
            einstein_angle,
            lens_radius,
            source_radius,
        )

    def pack_lenses(self) -> Generator[float, None, None]:
        c_x = self.com_x
        c_y = self.com_y

        M = self.mass

        Rl = self.lens_radius

        for lens in self.lenses:
            yield lens.m  # The mass is unneccisary, but due to byte alignment it is still reserved
            yield (lens.m / M)
            yield (lens.x - c_x) / Rl
            yield (lens.y - c_y) / Rl

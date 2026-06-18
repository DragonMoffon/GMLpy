from GMLID.logging import get_logger

logger = get_logger("physics.util")

LIGHT_SPEED_m = 299_792_458
LIGHT_SPEED_km = 299_792.458
LIGHT_SPEED_au = 0.0020039888041
LIGHT_SPEED_pc = 9.71561e-9

pc_to_au = 206264.80624538
au_to_pc = 1.0 / pc_to_au
au_to_m = 1.496e11
Sr_to_au = 4.65047e-3
au_to_Sr = 1.0 / Sr_to_au
m_to_au = 1.0 / au_to_m
pc_to_m = 3.08567758128e16

GRAVITATIONAL_CONSTANT = 6.6743e-11
SOLAR_MASS = 1.988475e30
# collect constant terms of einstein radius equation
# Precalculated to try avoid precision issues as much as possible. (in Solar Masses / pc)
# EINSTEIN_FACTOR = (4 * GRAVITATIONAL_CONSTANT / LIGHT_SPEED_m**2) * (SOLAR_MASS / pc_to_m)
EINSTEIN_FACTOR = 1.9142290343 * 10 ** (-13)


def calculate_einstein_angle(mass: float, lens: float, source: float) -> float:
    if lens <= 0 or source <= lens:
        logger.critical(
            "lens or source plane distance is invalid and the einstein angle cannot be calculated"
        )
        raise ValueError(
            "lens or source plane distance is invalid and the einstein angle cannot be calculated"
        )
    return (EINSTEIN_FACTOR * mass * (source - lens) / (source * lens)) ** 0.5

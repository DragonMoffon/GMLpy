import numpy as np

from GMLID.logging import get_logger

from .system import System

logger = get_logger("physics.analytical")


def get_amplification_at_position(system: System, locations: np.ndarray) -> np.ndarray:
    """
    Get the analytical amplification at a location for a one or two lens system.

    Args:
        system: The lens system which holds the data used to calculate the amplification
        location: The sampled location in Angular Einstein Radii
    """
    count = len(system.lenses)
    if count == 1:
        return one_lens_amplificiation(system, locations)
    elif count == 2:
        return two_lens_amplification(system, locations)
    logger.error(
        f"No analytical amplification for a {count} lens system. Use GMLID.physics.numerical instead"
    )
    raise ValueError(
        f"No analytical amplification for a {count} lens system. Use GMLID.physics.numerical instead"
    )


def one_lens_amplificiation(system: System, locations: np.ndarray) -> np.ndarray:
    if len(system.lenses) != 1:
        logger.error("This amplification solution only works for one lens")
        raise ValueError("This amplification solution only works for one lens")

    # Given there is only one lens, we can assume it will be centered at (0, 0)
    separation = (locations[:, 0] ** 2.0 + locations[:, 1] ** 2.0) ** 0.5

    # The impact parameter (mu)
    # classically the deflection is divided by the Einstein angle,
    # however the location angle is already scaled by the Einstein angle so it can
    # be skipped.
    mu = separation - system.einstein_angle**2 / separation

    return (mu**2 + 2) / (mu * (mu**2 + 4) ** 0.5)


def two_lens_amplification(system: System, locations: np.ndarray) -> np.ndarray:
    if len(system.lenses) != 2:
        logger.error("This amplification solution only works for one lens")
        raise ValueError("This amplification solution only works for two lenses")

    logger.warning("two_lens_amplification is currently unimplemented.")
    return np.asarray([0.0])


def get_critical_curves(system: System, count: int) -> np.ndarray:
    """
    get count samples of the analytical critical curves for a one or two lens system.
    The returned array is in fractions of einstein angle.
    """
    lens_count = len(system.lenses)
    if lens_count == 1:
        return one_lens_critical_curves(system, count)
    elif lens_count == 2:
        return two_lens_critical_curves(system, count)
    logger.error(
        f"No analytical solutions for a {lens_count} lens system. Use GMLID.physics.numerical instead"
    )
    raise ValueError(
        f"No analytical solutions for a {lens_count} lens system. Use GMLID.physics.numerical instead"
    )


def one_lens_critical_curves(system: System, count: int) -> np.ndarray:
    if len(system.lenses) != 1:
        logger.error("This critical curve solution only works for one lens")
        raise ValueError("This critical curve solution only works for one lens")
    angles = np.linspace(0.0, 2.0 * np.pi, count, endpoint=False)
    return np.asarray((np.cos(angles), np.sin(angles))).transpose(1, 0)


def two_lens_critical_curves(system: System, count: int) -> np.ndarray:
    if len(system.lenses) != 2:
        logger.error("This critical curve solution only works for two lenses")
        raise ValueError("This critical curve solution only works for two lenses")

    l1, l2 = system.lenses

    # normalise masses
    m1 = l1.m / system.mass
    m2 = l2.m / system.mass

    # convert to complex numbers
    p1 = l1.x + l1.y * 1j
    p2 = l2.x + l2.y * 1j

    # calculate normalised separation
    sep = (p2 - p1) / system.lens_radius

    # normalise positions
    z1 = -sep * m1
    z2 = sep * m2

    # calculate center of mass
    cx = np.real(sep) * (1 - 2 * m1)
    cy = np.imag(sep) * (1 - 2 * m1)

    # generate angles for calculations
    phi = np.linspace(0.0j, 2j * np.pi, count)

    # calculate coefficients of quartic
    c1 = np.exp(phi)
    c2 = -c1 * (2 * z2 + 2 * z1)
    c3 = c1 * (z2 * z2 + 4 * z1 * z2 + z1 * z1) - 1
    c4 = -c1 * (2 * z1 * z2 * z2 + 2 * z2 * z1 * z1)
    c5 = c1 * z1 * z1 * z2 * z2 + z1 * z2

    # stack coefficients for iteration
    coefficients = np.stack((c1, c2, c3, c4, c5), axis=-1)

    # pre-create roots array
    roots = np.zeros((count, 4), np.complex128)

    # compute roots
    for idx in range(count):
        roots[idx] = np.roots(coefficients[idx])

    # collect all non-zero roots
    roots = roots.flatten()
    roots = roots[roots != 0.0j]

    # convert back into 2D positions and adjust by center of mass
    critical_points = np.asarray((np.real(roots) - cx, np.imag(roots) - cy)).transpose(1, 0)
    return critical_points


def apply_lens_equation(system: System, locations: np.ndarray) -> np.ndarray:
    c_x = system.com_x
    c_y = system.com_y

    M = system.mass

    Rl = system.lens_radius

    results = np.copy(locations)
    for lens in system.lenses:
        # Get lens positions relative to com and normalised
        pos = (lens.x - c_x) / Rl, (lens.y - c_y) / Rl
        # Get the mass fraction of the lens
        fraction = lens.m / M

        # find the difference and compute lens diflection
        diff = locations - pos
        sep = np.vecdot(diff, diff).reshape((locations.shape[0], -1))

        results = results - fraction * diff / sep

    return results

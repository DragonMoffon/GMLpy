from os import system
from struct import pack
import sys
from timeit import timeit

import matplotlib.pyplot as plt
from matplotlib import colormaps
import numpy as np

import GML

magma = colormaps["magma"]

win = GML.setup_GMLpy()


def generate_method_histogram_and_mag():
    system = GML.System.create(4000.0, 8000.0, (GML.Lens(0.8, 0.0, 0.0), GML.Lens(0.6, 5, 0.0)))
    packed = tuple(system.pack_lenses())
    deflection = GML.IRSDeflectionMap(system, (6144, 6144))
    deflection.generate()
    histogram = GML.IRSHistogram(3072, (2048, 2048), deflection)
    histogram.generate(250)

    results = histogram.read(normalised=True)
    magnification = GML.create_magnification_map(histogram, 3)

    critical = GML.analytical.get_critical_curves(system, 50)
    angles = np.atan2(critical[:, 1], critical[:, 0])
    critical = critical[np.argsort(angles)]

    # Histogram
    fig = plt.figure(figsize=(8, 8))
    ax = fig.subplots(1, 1)
    ax.imshow(
        results,
        extent=(-2.0, 2.0, -2.0, 2.0),
        aspect="equal",
        origin="lower",
    )
    ax.plot(critical[:, 0], critical[:, 1], "--", c="gray")
    ax.scatter((packed[2], packed[6]), (packed[3], packed[7]), marker="x", c="gray")
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_xlabel(r"x-axis [$\theta_E$]")
    ax.set_ylabel(r"y-axis [$\theta_E$]")
    fig.tight_layout()
    fig.savefig("Methods_Histogram.png", transparent=True)

    # Magnication
    fig = plt.figure(figsize=(8, 8))
    ax = fig.subplots(1, 1)
    ax.imshow(
        magnification,
        extent=(-2.0, 2.0, -2.0, 2.0),
        aspect="equal",
        origin="lower",
    )
    ax.plot(critical[:, 0], critical[:, 1], "--", c="gray")
    ax.scatter((packed[2], packed[6]), (packed[3], packed[7]), marker="x", c="gray")
    ax.set_xlim(-1.5, 1.5)
    ax.set_ylim(-1.5, 1.5)
    ax.set_xlabel(r"x-axis [$\theta_E$]")
    ax.set_ylabel(r"y-axis [$\theta_E$]")
    fig.tight_layout()
    fig.savefig("Methods_Magnification_Map.png", transparent=True)


# generate_method_histogram_and_mag()


def generate_method_light_curves():
    system = GML.System.create(
        4000.0,
        8000.0,
        (
            GML.Lens(1.0, -0.5 * 4.232855307559067, 0.0),
            GML.Lens(0.1, 0.6 * 4.232855307559067, -0.6 * 4.232855307559067),
        ),
    )
    packed = tuple(system.pack_lenses())

    deflection = GML.IRSDeflectionMap(system, (2 * 6144, 2 * 6144))
    deflection.generate()
    histogram = GML.IRSHistogram(3072, (2 * 2048, 2 * 2048), deflection)
    histogram.generate(1000)
    # results = histogram.read(normalised=True)
    results = GML.create_magnification_map(histogram, 3)

    critical = GML.analytical.get_critical_curves(system, 50)
    caustic = GML.analytical.apply_lens_equation(system, critical)

    lightcurve_1 = GML.get_light_curve(results, 100, (-1.5, 0.6), (1.5, 0.6))
    lightcurve_2 = GML.get_light_curve(results, 100, (-1.5, 0.0), (1.5, 0.0))
    lightcurve_3 = GML.get_light_curve(results, 100, (-1.5, -0.2), (1.5, -0.2))
    lightcurve_4 = GML.get_light_curve(results, 100, (-1.5, -0.6), (1.5, -0.6))

    fig = plt.figure(figsize=(8, 8))
    ax1 = fig.add_subplot(2, 2, 1)
    ax2 = fig.add_subplot(2, 2, 3)
    ax3 = fig.add_subplot(4, 2, 2)
    ax4 = fig.add_subplot(4, 2, 4)
    ax5 = fig.add_subplot(4, 2, 6)
    ax6 = fig.add_subplot(4, 2, 8)

    ax3.set_xticks([])
    ax4.set_xticks([])
    ax5.set_xticks([])
    ax6.set_xticks([])

    ax1.scatter(critical[:, 0], critical[:, 1], s=1, c="gray")
    ax1.scatter(caustic[:, 0], caustic[:, 1], s=1, c="gray")
    ax1.scatter((packed[2], packed[6]), (packed[3], packed[7]), marker="x", c="gray")
    ax1.hlines((0.6, 0.0, -0.2, -0.6), -2.0, 2.0, colors=("C0", "C1", "C2", "C3"))
    ax1.set_xlim(-1.5, 1.5)
    ax1.set_ylim(-1.5, 1.5)
    ax1.set_xlabel(r"x-axis [$\theta_E$]")
    ax1.set_ylabel(r"y-axis [$\theta_E$]")

    ax2.scatter(caustic[:, 0], caustic[:, 1], s=1, c="gray")
    ax2.scatter((packed[2], packed[6]), (packed[3], packed[7]), marker="x", c="gray")
    ax2.hlines((0.6, 0.0, -0.2, -0.6), -2.0, 2.0, colors=("C0", "C1", "C2", "C3"))
    ax2.set_xlim(-0.3, 0.7)
    ax2.set_ylim(-0.6, 0.4)
    ax2.set_xlabel(r"x-axis [$\theta_E$]")
    ax2.set_ylabel(r"y-axis [$\theta_E$]")

    t = np.linspace(0, 1.0, 100)

    ax3.plot(t, lightcurve_1, "C0")
    ax4.plot(t, lightcurve_2, "C1")
    ax5.plot(t, lightcurve_3, "C2")
    ax6.plot(t, lightcurve_4, "C3")

    fig.tight_layout()
    fig.savefig("Methods_Lightcurves.png", transparent=True)


# generate_method_light_curves()


def generate_results_deflection_maps():
    system_1 = GML.System.create(4000.0, 8000.0, (GML.Lens(1, 0.0, 0.0)))
    system_2 = GML.System.create(
        4000.0,
        8000.0,
        (
            GML.Lens(0.33, 0.0, 4.2),
            GML.Lens(0.33, -np.sqrt(0.75) * 4.2, -2.1),
            GML.Lens(0.33, np.sqrt(0.75) * 4.2, -2.1),
        ),
    )

    v = 2.0

    deflection_1 = GML.IRSDeflectionMap(system_1, (2048, 2048), viewport=(v, v))
    deflection_1.generate()
    deflection_2 = GML.IRSDeflectionMap(system_2, (2048, 2048), viewport=(v, v))
    deflection_2.generate()

    fig = plt.figure(figsize=(8, 8))
    (ax1, ax2), (ax3, ax4) = fig.subplots(2, 2, sharex=True, sharey=True)

    ax1.imshow(
        deflection_1.capture(blue_value=0),
        extent=(-v, v, -v, v),
        aspect="equal",
        origin="lower",
    )
    ax1.set_ylabel(r"y-axis [$\theta_E$]")
    ax2.imshow(
        deflection_1.capture(clipped=False, blue_value=0),
        extent=(-v, v, -v, v),
        aspect="equal",
        origin="lower",
    )
    ax3.imshow(
        deflection_2.capture(blue_value=0),
        extent=(-v, v, -v, v),
        aspect="equal",
        origin="lower",
    )
    ax3.set_xlabel(r"x-axis [$\theta_E$]")
    ax3.set_ylabel(r"y-axis [$\theta_E$]")
    ax4.imshow(
        deflection_2.capture(clipped=False, blue_value=0),
        extent=(-v, v, -v, v),
        aspect="equal",
        origin="lower",
    )
    ax4.set_xlabel(r"x-axis [$\theta_E$]")

    fig.tight_layout()
    fig.savefig("Results_Deflection_Map.png")


# generate_results_deflection_maps()


def generate_results_histogram():
    system = GML.System.create(
        4000.0,
        8000.0,
        (
            GML.Lens(0.33, 0.0, 4.2),
            GML.Lens(0.33, -np.sqrt(0.75) * 4.2, -2.1),
            GML.Lens(0.33, np.sqrt(0.75) * 4.2, -2.1),
        ),
    )
    deflection = GML.IRSDeflectionMap(system, (6144, 6144))
    deflection.generate()

    histogram = GML.IRSHistogram(3072, (2048, 2048), deflection)

    histogram.generate(10)
    results_1 = histogram.read()
    histogram.generate(240)
    results_2 = histogram.read()
    histogram.generate(750)
    results_3 = histogram.read()

    fig = plt.figure(figsize=(8, 5.4))
    (ax11, ax12, ax13), (ax21, ax22, ax23) = fig.subplots(2, 3)

    extents = (-2, 2, -2, 2)
    x1, y1 = -1.0, 1.0
    x2, y2 = -0.6, -0.54
    x3, y3 = -0.36, -0.3
    ax11.imshow(results_1, extent=extents, aspect="equal", origin="lower")
    ax11.set_xlim(x1, y1)
    ax11.set_ylim(x1, y1)
    ax11.set_title("$10$ iterations")
    ax12.imshow(results_2, extent=extents, aspect="equal", origin="lower")
    ax12.set_xlim(x1, y1)
    ax12.set_ylim(x1, y1)
    ax12.set_title("$250$ iterations")
    ax13.imshow(results_3, extent=extents, aspect="equal", origin="lower")
    ax13.set_xlim(x1, y1)
    ax13.set_ylim(x1, y1)
    ax13.set_title("$1000$ iterations")
    ax21.imshow(results_1, extent=extents, aspect="equal", origin="lower")
    ax21.set_xlim(x2, y2)
    ax21.set_ylim(x3, y3)
    ax22.imshow(results_2, extent=extents, aspect="equal", origin="lower")
    ax22.set_xlim(x2, y2)
    ax22.set_ylim(x3, y3)
    ax23.imshow(results_3, extent=extents, aspect="equal", origin="lower")
    ax23.set_xlim(x2, y2)
    ax23.set_ylim(x3, y3)

    fig.tight_layout()
    fig.savefig("Results_Histogram_Various.png", transparent=True)


# generate_results_histogram()


def generate_results_magnifcation():
    system_1 = GML.System.create(
        4000.0,
        8000.0,
        (
            GML.Lens(1.0, 0.0, 4.2),
            GML.Lens(0.4, -np.sqrt(0.75) * 4.2, -2.1),
        ),
    )
    packed_1 = tuple(system_1.pack_lenses())
    system_2 = GML.System.create(
        4000.0,
        8000.0,
        (
            GML.Lens(0.33, 0.0, 4.2),
            GML.Lens(0.33, -np.sqrt(0.75) * 4.2, -2.1),
            GML.Lens(0.33, np.sqrt(0.75) * 4.2, -2.1),
        ),
    )
    packed_2 = tuple(system_2.pack_lenses())

    deflection_1 = GML.IRSDeflectionMap(system_1, (2 * 6144, 2 * 6144))
    deflection_1.generate()
    deflection_2 = GML.IRSDeflectionMap(system_2, (2 * 6144, 2 * 6144))
    deflection_2.generate()

    histogram_1 = GML.IRSHistogram(2 * 3072, (2 * 2048, 2 * 2048), deflection_1)
    histogram_2 = GML.IRSHistogram(2 * 3072, (2 * 2048, 2 * 2048), deflection_2)

    histogram_1.generate(100)
    histogram_2.generate(100)

    px_1, _ = GML.numerical.compute_pixel_resolution(system_1.lens_radius, (2.0, 2.0), (2048, 2048))
    px_2, _ = GML.numerical.compute_pixel_resolution(system_2.lens_radius, (2.0, 2.0), (2048, 2048))

    fig = plt.figure(figsize=(8, 5.4))
    (ax11, ax12, ax13), (ax21, ax22, ax23) = fig.subplots(2, 3)

    ext = (-2, 2, -2, 2)
    min_1, max_1 = -0.75, 0.75
    mag_11 = GML.create_magnification_map(histogram_1, 1)
    ax11.imshow(mag_11, extent=ext, aspect="equal", origin="lower")
    ax11.set_xlim(min_1, max_1)
    ax11.set_ylim(-1.0, 0.5)
    ax11.scatter((packed_1[2], packed_1[6]), (packed_1[3], packed_1[7]), marker="x", c="gray")
    ax11.set_title(f"${1 / px_1: .0f}$ Solar radii ($1$ pixel)")

    mag_12 = GML.create_magnification_map(histogram_1, 5)
    ax12.imshow(mag_12, extent=ext, aspect="equal", origin="lower")
    ax12.set_xlim(min_1, max_1)
    ax12.set_ylim(-1.0, 0.5)
    ax12.scatter((packed_1[2], packed_1[6]), (packed_1[3], packed_1[7]), marker="x", c="gray")
    ax12.set_title(f"${5 / px_1: .0f}$ Solar radii ($5$ pixels)")

    mag_13 = GML.create_magnification_map(histogram_1, 10)
    ax13.imshow(mag_13, extent=ext, aspect="equal", origin="lower")
    ax13.set_xlim(min_1, max_1)
    ax13.set_ylim(-1.0, 0.5)
    ax13.scatter((packed_1[2], packed_1[6]), (packed_1[3], packed_1[7]), marker="x", c="gray")
    ax13.set_title(f"${10 / px_1: .0f}$ Solar radii ($10$ pixels)")

    min_2, max_2 = -1.0, 1.0
    mag_21 = GML.create_magnification_map(histogram_2, 1)
    ax21.imshow(mag_21, extent=ext, aspect="equal", origin="lower")
    ax21.set_xlim(min_2, max_2)
    ax21.set_ylim(min_2, max_2)
    ax21.scatter(
        (packed_2[2], packed_2[6], packed_2[10]),
        (packed_2[3], packed_2[7], packed_2[11]),
        marker="x",
        c="gray",
    )
    ax21.set_title(f"${1 / px_2: .0f}$ Solar radii ($1$ pixel)")

    mag_22 = GML.create_magnification_map(histogram_2, 5)
    ax22.imshow(mag_22, extent=ext, aspect="equal", origin="lower")
    ax22.set_xlim(min_2, max_2)
    ax22.set_ylim(min_2, max_2)
    ax22.scatter(
        (packed_2[2], packed_2[6], packed_2[10]),
        (packed_2[3], packed_2[7], packed_2[11]),
        marker="x",
        c="gray",
    )
    ax22.set_title(f"${5 / px_2: .0f}$ Solar radii ($5$ pixels)")

    mag_23 = GML.create_magnification_map(histogram_2, 10)
    ax23.imshow(mag_23, extent=ext, aspect="equal", origin="lower")
    ax23.set_xlim(min_2, max_2)
    ax23.set_ylim(min_2, max_2)
    ax23.scatter(
        (packed_2[2], packed_2[6], packed_2[10]),
        (packed_2[3], packed_2[7], packed_2[11]),
        marker="x",
        c="gray",
    )
    ax23.set_title(f"${10 / px_2: .0f}$ Solar radii ($10$ pixels)")

    fig.tight_layout()
    fig.savefig("Results_Magnification_Various", transparent=True)


# generate_results_magnifcation()


def analytic_histograms():
    pass


def analytic_lightcurves():
    pass


def generate_light_curves():
    pass


def time_deflection_maps():
    import random
    import timeit

    random_m = tuple(random.uniform(0.1, 1.0) for _ in range(1000))
    random_x = tuple(random.uniform(0.0, 5.2) for _ in range(1000))
    lenses = tuple(
        GML.Lens(random.choice(random_m), random.choice(random_x), random.choice(random_x))
        for _ in range(100)
    )

    deflection: GML.IRSDeflectionMap
    count = 0
    dud = GML.System.create(4000, 5000, ())

    def gen_deflection_map():
        system = GML.System.create(4000, 8000, random.sample(lenses, count))
        deflection.update_system(system)
        deflection.generate()
        win.ctx.finish()

    sizes = np.asarray((1000, 2000, 5000, 10000, 20000))
    timings = np.zeros((10, 5))

    for i, size in enumerate(sizes):
        deflection = GML.IRSDeflectionMap(dud, (size, size))
        print(size)
        for j in range(10):
            print(j, end=", ")
            count = j + 1
            total = timeit.timeit(gen_deflection_map, number=10000)
            timings[j, i] = total / 10
        print()

    print(timings)

    # tested for number of lenses
    # plotted as time vs resolution
    pass


# time_deflection_maps()


def plot_deflection_timing():
    # fmt: off
    timings = np.asarray([
        [ 0.1057157 ,  0.26789308,  1.23596622,  4.5892779 , 16.49033128,],
        [ 0.10343106,  0.27058687,  1.22685005,  4.67067522, 16.8341443 ,],
        [ 0.10453868,  0.26647312,  1.22611464,  5.14014993, 17.05679943,],
        [ 0.10535978,  0.26848723,  1.23618225,  4.98540668, 17.50884811,],
        [ 0.10894705,  0.27989071,  1.27940546,  5.07189499, 18.35022812,],
        [ 0.11440196,  0.28869317,  1.32235419,  5.42970458, 19.97163777,],
        [ 0.11976141,  0.29695203,  1.40374143,  5.75898506, 21.64099981,],
        [ 0.12409487,  0.27549066,  1.62951798,  6.1781777 , 25.23021691,],
        [ 0.12930204,  0.29048345,  1.78136768,  6.65661615, 26.86757876,],
        [ 0.13409012,  0.30374122,  1.93861726,  7.26731112, 28.84253716,],
    ])
    # fmt: on

    sizes = np.asarray((1000, 2000, 5000, 10000, 20000))

    fig = plt.figure(figsize=(8, 8))
    ax = fig.subplots(1, 1)

    ax.semilogx(sizes, timings[0], "-o", label="1 Lens")
    ax.semilogx(sizes, timings[1], "-o", label="2 Lenses")
    ax.semilogx(sizes, timings[2], "-o", label="3 Lenses")
    ax.semilogx(sizes, timings[3], "-o", label="4 Lenses")
    ax.semilogx(sizes, timings[4], "-o", label="5 Lenses")
    ax.semilogx(sizes, timings[5], "-o", label="6 Lenses")
    ax.semilogx(sizes, timings[6], "-o", label="7 Lenses")
    ax.semilogx(sizes, timings[7], "-o", label="8 Lenses")
    ax.semilogx(sizes, timings[8], "-o", label="9 Lenses")
    ax.semilogx(sizes, timings[9], "-o", label="10 Lenses")
    ax.set_xticks(sizes, [f"${v}^2$" for v in sizes])
    ax.set_xlabel("$N_{px}$")
    ax.set_ylabel("Mean generation time [ms]")
    ax.legend()
    ax.grid(which="both")
    plt.show()


# plot_deflection_timing()


def time_histogram():
    import random
    import timeit

    # tested as number of lenses
    # plotted as time vs resolution
    # plotted as time vs iterations

    random_m = tuple(random.uniform(0.1, 1.0) for _ in range(1000))
    random_x = tuple(random.uniform(0.0, 5.2) for _ in range(1000))
    lenses = tuple(
        GML.Lens(random.choice(random_m), random.choice(random_x), random.choice(random_x))
        for _ in range(100)
    )

    histogram: GML.IRSHistogram
    count = 0

    def gen_histogram():
        histogram.generate(count, flush=True)

    rays = np.asarray((1024, 2048, 4096, 8192, 16384))
    iterations = np.asarray((1, 5, 10, 50, 100, 250, 1000))
    timings_Nrays = np.zeros((10, 5))
    timings_iterations = np.zeros((10, 5))

    displacement = GML.IRSDeflectionMap(GML.System.create(4000, 8000, ()), (3072, 3072))

    for j in range(10):
        system = GML.System.create(4000, 8000, random.sample(lenses, j + 1))
        displacement.update_system(system)
        displacement.generate()
        print(f"{j + 1} lenses:")
        for i, number in enumerate(rays):
            histogram = GML.IRSHistogram(number, (2048, 2048), displacement)
            count = 100
            total = timeit.timeit(gen_histogram, number=1)
            timings_Nrays[j, i] = total
            print(f"{number} rays: {total}s")
            win.ctx.gc()

    print(timings_Nrays)


time_histogram()


def plot_histogram_timing():
    pass

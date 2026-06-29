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
            win.ctx.gc()
        print()

    print(timings)

    # tested for number of lenses
    # plotted as time vs resolution
    pass


# time_deflection_maps()


def plot_deflection_timing():
    # fmt: off
    timings = np.asarray([
        [ 0.22154626,  0.33541086,  0.74342071,  2.14783562,  7.5608058 ,],
        [ 0.24170239,  0.31645614,  0.74757148,  2.16046476,  7.76288412,],
        [ 0.2691357 ,  0.32096908,  0.73962095,  2.19089014,  8.02013165,],
        [ 0.29444458,  0.33245998,  0.74465971,  2.22335982,  8.34519449,],
        [ 0.30553117,  0.33521318,  0.75292799,  2.52573562,  9.73996118,],
        [ 0.26142938,  0.34277448,  0.8498328 ,  2.872025  , 11.12904708,],
        [ 0.29323487,  0.34903291,  0.93255859,  3.22418126, 12.50794854,],
        [ 0.32238955,  0.38794015,  1.01984277,  3.56579642, 13.84298894,],
        [ 0.34402043,  0.39013653,  1.10928674,  3.91835312, 15.25391352,],
        [ 0.34367424,  0.38174968,  1.19632548,  4.25434748, 16.76058269,],
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

    def gen_histogram():
        displacement.update_system(GML.System.create(4000, 8000, random.sample(lenses, j + 1)))
        displacement.generate()
        histogram.generate(count, flush=True)
        win.ctx.gc()

    rays = np.asarray((1024, 2048, 4096, 8192, 16384))
    iterations = np.asarray((1, 10, 100, 1000, 10000))
    timings_Nrays = np.zeros((10, 5))
    timings_iterations = np.zeros((10, 5))

    displacement = GML.IRSDeflectionMap(GML.System.create(4000, 8000, ()), (3072, 3072))

    for j in range(10):
        print(f"{j + 1} lenses:")
        for i, number in enumerate(rays):
            histogram = GML.IRSHistogram(number, (2048, 2048), displacement)
            count = 100
            total = timeit.timeit(gen_histogram, number=1)
            timings_Nrays[j, i] = total / 1
            print(f"{number} rays: {total / 1}s")
            win.ctx.gc()
        for i, number in enumerate(iterations):
            histogram = GML.IRSHistogram(3072, (2048, 2048), displacement)
            count = number
            total = timeit.timeit(gen_histogram, number=10)
            timings_iterations[j, i] = total / 10
            print(f"{number} iterations: {total / 10}s")
            win.ctx.gc()

    print(timings_Nrays)
    print(timings_iterations)


# time_histogram()


def plot_histogram_ray_timing():
    # fmt: off
    timings = np.asarray([
        [ 0.0510823,  0.1157651,  0.4300664,  2.0665787, 11.5791281,],
        [ 0.0505941,  0.1035355,  0.4046127,  2.1430818, 11.5955211,],
        [ 0.0518712,  0.1049203,  0.4224587,  2.212228 , 11.7609271,],
        [ 0.0515354,  0.1036838,  0.4364136,  2.1294758, 11.6511372,],
        [ 0.0513942,  0.1051723,  0.4017552,  2.1492217, 11.6320105,],
        [ 0.0521984,  0.1048021,  0.4172436,  2.2008529, 11.7148818,],
        [ 0.0499126,  0.1053392,  0.3988691,  2.1467198, 11.6166718,],
        [ 0.0505822,  0.1044242,  0.4081021,  2.095103 , 11.520308 ,],
        [ 0.0510597,  0.106276 ,  0.3986673,  2.0668819, 11.6789533,],
        [ 0.0503439,  0.1051382,  0.4083375,  2.0996602, 11.5391242,],
    ])
    # fmt: on

    rays = np.asarray((1024, 2048, 4096, 8192, 16384))

    fig = plt.figure(figsize=(8, 8))
    ax = fig.subplots(1, 1)

    ax.semilogx(rays, timings[0], "-o", label="1 Lens")
    ax.semilogx(rays, timings[1], "-o", label="2 Lenses")
    ax.semilogx(rays, timings[2], "-o", label="3 Lenses")
    ax.semilogx(rays, timings[3], "-o", label="4 Lenses")
    ax.semilogx(rays, timings[4], "-o", label="5 Lenses")
    ax.semilogx(rays, timings[5], "-o", label="6 Lenses")
    ax.semilogx(rays, timings[6], "-o", label="7 Lenses")
    ax.semilogx(rays, timings[7], "-o", label="8 Lenses")
    ax.semilogx(rays, timings[8], "-o", label="9 Lenses")
    ax.semilogx(rays, timings[9], "-o", label="10 Lenses")
    ax.set_xticks(rays, [f"${v}^2$" for v in rays])
    ax.set_xlabel("$N_{r a y}$")
    ax.set_ylabel("Mean generation time [s]")
    ax.legend()
    ax.grid(which="major")
    plt.show()


# plot_histogram_ray_timing()


def plot_histogram_iteration_timing():
    # fmt: off
    timings = np.asarray([
        [ 0.17240036,  0.14700132,  0.22551473,  1.20752167, 11.68576287],
        [ 0.16685915,  0.14829668,  0.23528723,  1.22772719, 11.86841543],
        [ 0.15213019,  0.14586274,  0.22183526,  1.22571161, 11.92431288],
        [ 0.16425776,  0.14200485,  0.22612787,  1.22378062, 11.77702804],
        [ 0.15548948,  0.13742674,  0.23233261,  1.2171477 , 11.88562628],
        [ 0.15006121,  0.14404832,  0.22848388,  1.2235205 , 11.86930255],
        [ 0.16896699,  0.1438737 ,  0.22872864,  1.22162926, 11.96050487],
        [ 0.14707677,  0.14299863,  0.23447177,  1.23019808, 11.89953626],
        [ 0.14573805,  0.13475722,  0.23070232,  1.23128885, 11.88511967],
        [ 0.14659151,  0.14141505,  0.2349313 ,  1.2270214 , 11.82234501],
    ])
    # fmt: on

    iterations = np.asarray((1, 10, 100, 1000, 10000))

    fig = plt.figure(figsize=(8, 8))
    ax = fig.subplots(1, 1)

    ax.semilogx(iterations, timings[0], "-o", label="1 Lens")
    ax.semilogx(iterations, timings[1], "-o", label="2 Lenses")
    ax.semilogx(iterations, timings[2], "-o", label="3 Lenses")
    ax.semilogx(iterations, timings[3], "-o", label="4 Lenses")
    ax.semilogx(iterations, timings[4], "-o", label="5 Lenses")
    ax.semilogx(iterations, timings[5], "-o", label="6 Lenses")
    ax.semilogx(iterations, timings[6], "-o", label="7 Lenses")
    ax.semilogx(iterations, timings[7], "-o", label="8 Lenses")
    ax.semilogx(iterations, timings[8], "-o", label="9 Lenses")
    ax.semilogx(iterations, timings[9], "-o", label="10 Lenses")
    ax.set_xticks(iterations)
    ax.set_xlabel(r"$N_{iterations}$")
    ax.set_ylabel("Mean generation time [s]")
    ax.legend()
    ax.grid(which="major")
    plt.show()


# plot_histogram_iteration_timing()

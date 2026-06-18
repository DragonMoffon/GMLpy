from pathlib import Path
from time import time

from arcade import Window
import numpy as np

from GML import System, Lens, IRSDeflectionMap, IRSHistogram
from GML.io import _dump_histogram_raw
from GML.logging import get_logger

logger = get_logger("generation")
try:
    test_systems = (
        System.create(4000.0, 8000.0, (Lens(0.8, 0.0, 0.0), Lens(0.2, 3.0, 0.0))),
        System.create(4000.0, 8000.0, (Lens(0.8, 0.0, 0.0), Lens(0.2, 3.5, 0.0))),
        System.create(4000.0, 8000.0, (Lens(0.8, 0.0, 0.0), Lens(0.2, 4.0, 0.0))),
        System.create(4000.0, 8000.0, (Lens(0.8, 0.0, 0.0), Lens(0.2, 4.5, 0.0))),
        System.create(4000.0, 8000.0, (Lens(0.8, 0.0, 0.0), Lens(0.2, 5.0, 0.0))),
        *(
            System.create(
                4000.0,
                8000.0,
                (
                    Lens(0.8, 0.0, 0.0),
                    Lens(0.2, 4.0, 0.0),
                    Lens(0.2, -4.0 * np.cos(x), 4.0 * np.sin(x)),
                ),
            )
            for x in np.linspace(0.0, np.pi / 2, 5)
        ),
    )
    logger.info("Created Systems")

    win = Window()
    logger.info("Created Window")

    deflection = IRSDeflectionMap(test_systems[0], (16382, 16382))
    deflection.generate()
    win.ctx.finish()
    logger.info("Created and Generated Deflection Map")

    histogram = IRSHistogram(8192, (8192, 8192), deflection)
    logger.info("Created Histogram")

    s_time = time()
    histogram.generate(2000)
    e_time = time()
    logger.info(f"Generated Histogram in {e_time - s_time} seconds")

    _dump_histogram_raw(Path("System1.histogram"), histogram)
    logger.info("Dumped Histogram")

    for idx, system in enumerate(test_systems[1:], 2):
        deflection.update_system(system)
        deflection.generate()
        logger.info("Regenerated Deflection Map")

        histogram.clear()
        win.ctx.finish()
        logger.info("Cleared Histogram")

        s_time = time()
        histogram.generate(2000)
        e_time = time()
        logger.info(f"Generated Histogram in {e_time - s_time} seconds")

        _dump_histogram_raw(Path(f"System{idx}.histogram"), histogram)
        logger.info("Dumped Histogram")
except KeyboardInterrupt:
    logger.warning("Interrupted Code Execution", exc_info=True)
except Exception as e:
    logger.exception(e)

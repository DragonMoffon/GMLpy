from pathlib import Path

from arcade import Window
import matplotlib.pyplot as plt

from GML.io import _load_histogram_raw


win = Window()
win.minimize()
histogram = _load_histogram_raw(Path("System6.histogram"))

if histogram is None:
    exit()

data = histogram.read()

plt.imshow(data, extent=(-2.0, 2.0, -2.0, 2.0))
plt.show()

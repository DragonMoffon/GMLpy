# Gravitational Micro-Lensing Magnification Interactive Demo (GMLID)
GMLID provides tools for working with microlensings of low lens count systems without
shear or uniform mass distributions.

## Usage

### GMLID.physics
The physics sub-library in GMLID is self-contained, and provides classes and methods
to handle gravitational lensing systems.

`GMLID.physics.System` is an immutable description of the lens system. It stores the
distance to the source and lens planes. It also holds a tuple of the point mass lenses
in the system. To create a system use the class method `GMLID.physics.System.create()`.

Each `GMLID.physics.Lens` used by the system is stored with mass in solar masses, and
positions in Astronomical Units. The coordinate system is arbitrary and has the most massive
lens at (0.0, 0.0) by convention. The lenses are repositioned relative to the center of mass
within the system object.

Once you have created a `System` to get to a caustic map the first step is to choose the
simulation method;
* The first method is to use a `GMLID.physics.IRSDeflectionMap` to create a cached deflection
texture which is a 2D texture where each pixel represents the displacement vector from the lens
plane to the source plane.

* (NOT YET IMPLEMENTED) The second method is to use the `GMLID.physics.IRSHistogram` directly.
This means each ray will compute its deflection. This is more expensive, but avoids
artefacts caused by the linear interpolation of the deflection vectors.


### GMLID.interactive
(NOT YET IMPLEMENTED) If your use of GMLID is to see gravitational lensing in action, and not
to generate deflection maps or caustic maps, then you can launch the interactive window by
running `python -m GMLID` in the python environment where `GMLID` has been installed. Alternatively
you can go to [link] to use GMLID on the web.

### Using a terminal
(NOT YET IMPLEMENTED) If you would like to generate many caustic maps it is possible to run a simple
`GMLID.physics` pipeline directly from the terminal. You can either describe the system in the terminal
or reference a json file with multiple systems, and multiple output locations.

### Export options
(NOT YET IMPLEMENTED) GMLID can export to any image format supported by PIL, and additionally outputs
directly to tiff files for scientific work.
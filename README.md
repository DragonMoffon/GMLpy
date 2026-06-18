# Gravitational MicroLensing _in_ python (GMLpy)
GMLpy provides tools for working with microlensings of low lens count systems without
shear or uniform mass distributions.

## Usage

`GML.System` is an immutable description of the lens system. It stores the
distance to the source and lens planes. It also holds a tuple of the point mass lenses
in the system. To create a system use the class method `GML.System.create()`.

Each `GML.Lens` used by the system is stored with mass in solar masses, and
positions in Astronomical Units. The coordinate system is arbitrary and has the most massive
lens at (0.0, 0.0) by convention. The lenses are repositioned relative to the center of mass
within the system object.

Once you have created a `System` to get to a caustic map the first step is to choose the
simulation method;

* The first method is to use a `GML.IRSDeflectionMap` to create a cached deflection
texture which is a 2D texture where each pixel represents the displacement vector from the lens
plane to the source plane.

* (NOT YET IMPLEMENTED) The second method is to use the `GML.IRSHistogram` directly.
This means each ray will compute its deflection. This is more expensive, but avoids
artefacts caused by the linear interpolation of the deflection vectors.

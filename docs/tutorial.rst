Tutorial
========

Getting started
---------------

Before you can use PyCuda, you have to import and initialize it::

  import pycuda.driver as cuda
  import pycuda.autoinit
  from pycuda.compiler import SourceModule

Note that you do not *have* to use :mod:`pycuda.autoinit`--
initialization, context creation, and cleanup can also be performed
manually, if desired.

Transferring Data
-----------------

The next step in most programs is to transfer data onto the device.
In PyCuda, you will mostly transfer data from :mod:`numpy` arrays
on the host. (But indeed, everything that satisfies the Python buffer
interface will work, even :class:`bytes`.) Let's make a 4x4 array
of random numbers::

  import numpy
  a = numpy.random.randn(4,4)

But wait--*a* consists of double precision numbers, but most nVidia
devices only support single precision::

  a = a.astype(numpy.float32)

Finally, we need somewhere to transfer data to, so we need to
allocate memory on the device::

  a_gpu = cuda.mem_alloc(a.nbytes)

As a last step, we need to transfer the data to the GPU::

  cuda.memcpy_htod(a_gpu, a)

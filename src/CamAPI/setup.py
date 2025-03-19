
from distutils.core import setup
from Cython.Build import cythonize

setup(
  name = "cam",
  ext_modules = cythonize('*.pyx'),
)
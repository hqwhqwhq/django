"""
 This module houses the GEOSCoordSeq object, which is used internally
 by GEOSGeometry to house the actual coordinates of the Point,
 LineString, and LinearRing geometries.
"""
from ctypes import c_double, c_uint, byref
from types import ListType, TupleType
from django.contrib.gis.geos.error import GEOSException, GEOSGeometryIndexError
from django.contrib.gis.geos.libgeos import CS_PTR, HAS_NUMPY
from django.contrib.gis.geos.prototypes import cs_clone, cs_getdims, cs_getordinate, cs_getsize, cs_setordinate
if HAS_NUMPY: from numpy import ndarray

class GEOSCoordSeq(object):
    "The internal representation of a list of coordinates inside a Geometry."

    #### Python 'magic' routines ####
    def __init__(self, ptr, z=False):
        "Initializes from a GEOS pointer."
        if not isinstance(ptr, CS_PTR):
            raise TypeError('Coordinate sequence should initialize with a CS_PTR.')
        self._ptr = ptr
        self._z = z

    def __iter__(self):
        "Iterates over each point in the coordinate sequence."
        for i in xrange(self.size):
            yield self[i]

    def __len__(self):
        "Returns the number of points in the coordinate sequence."
        return int(self.size)

    def __str__(self):
        "Returns the string representation of the coordinate sequence."
        return str(self.tuple)

    def __getitem__(self, index):
        "Returns the coordinate sequence value at the given index."
        coords = [self.getX(index), self.getY(index)]
        if self.dims == 3 and self._z:
            coords.append(self.getZ(index))
        return tuple(coords)

    def __setitem__(self, index, value):
        "Sets the coordinate sequence value at the given index."
        # Checking the input value
        if isinstance(value, (ListType, TupleType)):
            pass
        elif HAS_NUMPY and isinstance(value, ndarray):
            pass
        else:
            raise TypeError('Must set coordinate with a sequence (list, tuple, or numpy array).')
        # Checking the dims of the input
        if self.dims == 3 and self._z:
            n_args = 3
            set_3d = True
        else:
            n_args = 2
            set_3d = False
        if len(value) != n_args:
            raise TypeError('Dimension of value does not match.')
        # Setting the X, Y, Z
        self.setX(index, value[0])
        self.setY(index, value[1])
        if set_3d: self.setZ(index, value[2])

    #### Internal Routines ####
    def _checkindex(self, index):
        "Checks the given index."
        sz = self.size
        if (sz < 1) or (index < 0) or (index >= sz):
            raise GEOSGeometryIndexError('invalid GEOS Geometry index: %s' % str(index))

    def _checkdim(self, dim):
        "Checks the given dimension."
        if dim < 0 or dim > 2:
            raise GEOSException('invalid ordinate dimension "%d"' % dim)

    #### Ordinate getting and setting routines ####
    def getOrdinate(self, dimension, index):
        "Returns the value for the given dimension and index."
        self._checkindex(index)
        self._checkdim(dimension)
        return cs_getordinate(self._ptr, index, dimension, byref(c_double()))

    def setOrdinate(self, dimension, index, value):
        "Sets the value for the given dimension and index."
        self._checkindex(index)
        self._checkdim(dimension)
        cs_setordinate(self._ptr, index, dimension, value)

    def getX(self, index):
        "Get the X value at the index."
        return self.getOrdinate(0, index)

    def setX(self, index, value):
        "Set X with the value at the given index."
        self.setOrdinate(0, index, value)

    def getY(self, index):
        "Get the Y value at the given index."
        return self.getOrdinate(1, index)

    def setY(self, index, value):
        "Set Y with the value at the given index."
        self.setOrdinate(1, index, value)

    def getZ(self, index):
        "Get Z with the value at the given index."
        return self.getOrdinate(2, index)

    def setZ(self, index, value):
        "Set Z with the value at the given index."
        self.setOrdinate(2, index, value)

    ### Dimensions ###
    @property
    def size(self):
        "Returns the size of this coordinate sequence."
        return cs_getsize(self._ptr, byref(c_uint()))

    @property
    def dims(self):
        "Returns the dimensions of this coordinate sequence."
        return cs_getdims(self._ptr, byref(c_uint()))

    @property
    def hasz(self):
        """
        Returns whether this coordinate sequence is 3D.  This property value is
        inherited from the parent Geometry.
        """
        return self._z

    ### Other Methods ###
    def clone(self):
        "Clones this coordinate sequence."
        return GEOSCoordSeq(cs_clone(self._ptr), self.hasz)

    @property
    def kml(self):
        "Returns the KML representation for the coordinates."
        # Getting the substitution string depending on whether the coordinates have
        #  a Z dimension.
        if self.hasz: substr = '%s,%s,%s '
        else: substr = '%s,%s,0 '
        kml = '<coordinates>'
        for i in xrange(len(self)):
            kml += substr % self[i]
        return kml.strip() + '</coordinates>'

    @property
    def tuple(self):
        "Returns a tuple version of this coordinate sequence."
        n = self.size
        if n == 1: return self[0]
        else: return tuple(self[i] for i in xrange(n))

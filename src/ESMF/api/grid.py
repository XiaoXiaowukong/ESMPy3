# $Id$

"""
The Grid API
"""

#### IMPORT LIBRARIES #########################################################

import warnings
from copy import copy

from ESMF.api.esmpymanager import *
from ESMF.util.esmpyarray import ndarray_from_esmf
import ESMF.api.constants as constants
from ESMF.util.slicing import get_formatted_slice, get_none_or_slice, get_none_or_bound, get_none_or_ssslice


#### Grid class #########################################################

class Grid(object):
    """
    The Grid class is a Python wrapper object for the ESMF Grid.  The individual 
    values of all coordinate and mask arrays are referenced to those of the
    underlying Fortran ESMF object.

    The :class:`~ESMF.api.grid.Grid` class is used to describe the geometry and
    discretization of logically rectangular physical grids.  It also contains
    the description of the underlying topology and decomposition of the physical
    grid across the available computational resources. The most frequent use of
    the :class:`~ESMF.api.grid.Grid` class is to describe physical grids in user
    code so that sufficient information is available to perform regridding
    operations.

    For more information about the ESMF Grid class, please see the 
    `ESMF Grid documentation
    <http://www.earthsystemmodeling.org/esmf_releases/public/last/ESMF_refdoc/node5.html#SECTION05080000000000000000>`_.
 
    A :class:`~ESMF.api.grid.Grid` can be created in two different ways, as a
    Grid in memory, or from SCRIP formatted or CF compliant GRIDSPEC file. The
    arguments for each type of :class:`~ESMF.api.grid.Grid` creation are
    outlined below.

    **Created in-memory:**

    *REQUIRED:*

    :param list max_index: An integer list of length 2 or 3, with the
        number of grid cells in each dimension.

    *OPTIONAL:*

    :param int num_peri_dims: The number of periodic dimensions, either ``0``
        or ``1``. If ``None``, defaults to ``0``.
    :param int periodic_dim: The periodic dimension: ``1``, ``2`` or ``3``.
        If ``None``, defaults to ``1``.
    :param int pole_dim: The pole dimension ``1`` or ``2``.
        If ``None``, defaults to ``2``.
    :param CoordSys coord_sys: Coordinate system for the
        :class:`~ESMF.api.grid.Grid`.
        If ``None``, defaults to :attr:`~ESMF.api.constants.CoordSys.SPH_DEG`.
    :param TypeKind coord_typekind: Type of the :class:`~ESMF.api.grid.Grid`
        coordinates.
        If ``None``, defaults to :attr:`~ESMF.api.constants.TypeKind.R8`.

    **Created either from file or in-memory:**

    :param StaggerLoc staggerloc: The stagger location of the coordinate values.
        If ``None``, defaults to :attr:`~ESMF.api.constants.StaggerLoc.CENTER`
        in 2D and :attr:`~ESMF.api.constants.StaggerLoc.CENTER_VCENTER` in 3D.

    **Created from file:**

    *REQUIRED:*

    :param str filename: The name of the NetCDF grid file.
    :param FileFormat filetype: The grid :attr:`~ESMF.api.constants.FileFormat`.

    *OPTIONAL:*

    :param bool is_sphere: Set to ``True`` for a spherical grid, or ``False``
        for regional. Defaults to ``True``.
    :param bool add_corner_stagger: Set to ``True`` to use the information in
        the grid file to add the corner stagger to the grid. The coordinates for
        the corner stagger are required for conservative regridding. If
        not specified, defaults to ``False``.
    :param bool add_user_area: Set to ``True`` to read in the cell area from the
        grid file; otherwise, ESMF will calculate it. Defaults to ``False``.
    :param bool add_mask: Set to ``True`` to generate the mask using the
        ``missing_value`` attribute defined in ``varname``.  This argument is
        only supported with filetype
        :attr:`~ESMF.api.constants.FileFormat.GRIDSPEC`.
        Defaults to ``False``.
    :param str varname: If add_mask is ``True``, provide a variable name stored
        in the grid file and the mask will be generated using the missing value
        of the data value of this variable.  The first two dimensions of the
        variable has to be the longitude and the latitude dimension and the
        mask is derived from the first 2D values of this variable even if this
        data is a 3D, or 4D array. This argument is only supported with
        filetype :attr:`~ESMF.api.constants.FileFormat.GRIDSPEC`.
        Defaults to ``None``.
    :param list coord_names:  A two-element array containing the longitude and
        latitude variable names in a GRIDSPEC file if there are multiple
        coordinates defined in the file. This argument is only supported with
        filetype :attr:`~ESMF.api.constants.FileFormat.GRIDSPEC`.
        Defaults to ``None``.
    """

    @initialize
    def __init__(self, max_index=None,
                 num_peri_dims=0,
                 periodic_dim=None,
                 pole_dim=None,
                 coord_sys=None,
                 coord_typekind=None,
                 staggerloc=None,
                 filename=None,
                 filetype=None,
                 reg_decomp=None,
                 decompflag=None,
                 is_sphere=None,
                 add_corner_stagger=None,
                 add_user_area=None,
                 add_mask=None,
                 varname=None,
                 coord_names=None):
 
        # initialize the from_file flag to False
        from_file = False
        
        # in-memory grid
        if max_index is not None:
            # cast max_index if not already done
            if max_index.dtype is not np.int32:
                self._max_index = np.array(max_index, dtype=np.int32)
            else:
                self._max_index = max_index
            # raise warnings on all from file args
            if filename is not None:
                warnings.warn("filename is only used for grids created from file, this argument will be ignored.")
            if filetype is not None:
                warnings.warn("filetype is only used for grids created from file, this argument will be ignored.")
            if reg_decomp is not None:
                warnings.warn("reg_decomp is only used for grids created from file, this argument will be ignored.")
            if decompflag is not None:
                warnings.warn("decompflag is only used for grids created from file, this argument will be ignored.")
            if is_sphere is not None:
                warnings.warn("is_sphere is only used for grids created from file, this argument will be ignored.")
            if add_corner_stagger is not None:
                warnings.warn("add_corner_stagger is only used for grids created from file, this argument will be ignored.")
            if add_user_area is not None:
                warnings.warn("add_user_area is only used for grids created from file, this argument will be ignored.")
            if add_mask is not None:
                warnings.warn("add_mask is only used for grids created from file, this argument will be ignored.")
            if varname is not None:
                warnings.warn("varname is only used for grids created from file, this argument will be ignored.")
            if coord_names:
                warnings.warn("coord_names is only used for grids created from file, this argument will be ignored.")
        # filename and filetype are required for from-file grids
        elif (filename is None) or (filetype is None):
            # raise error, need max_index to create in memory or filename to create from file
            raise GridArgumentError("must supply either max_index for an in-memory grid or filename and filetype for a from-file grid")
        # from file
        else:
            if (filetype != FileFormat.SCRIP) and (filetype != FileFormat.GRIDSPEC):
                raise GridArgumentError("filetype must be SCRIP or GRIDSPEC for Grid objects")
            # set the from_file flag to True
            from_file = True
            #raise errors for all in-memory grid options
            if max_index is not None:
                warnings.warn("max_index is only used for grids created in memory, this argument will be ignored.")
            if num_peri_dims is not 0:
                warnings.warn("num_peri_dims is only used for grids created in memory, this argument will be ignored.")
            if periodic_dim is not None:
                warnings.warn("periodic_dim is only used for grids created in memory, this argument will be ignored.")
            if pole_dim is not None:
                warnings.warn("pole_dim is only used for grids created in memory, this argument will be ignored.")
            if coord_sys is not None:
                warnings.warn("coord_sys is only used for grids created in memory, this argument will be ignored.")
            if coord_typekind is not None:
                warnings.warn("coord_typekind is only used for grids created in memory, this argument will be ignored.")
            if staggerloc is not None:
                warnings.warn("staggerloc is only used for grids created in memory, this argument will be ignored.")

        # ctypes stuff
        self._struct = None

        # for ocgis compatibility
        self._ocgis = {}

        # type, kind, rank, etc.
        self._type = TypeKind.R8
        self._areatype = TypeKind.R8
        self._rank = None
        self._periodic_dim = periodic_dim
        self._pole_dim = pole_dim
        self._coord_sys = coord_sys
        self._ndims = None # Applies to Gridspec only
        self._has_corners = False

        if num_peri_dims is None:
            self._num_peri_dims = 0
        else:
            self._num_peri_dims = num_peri_dims

        # size, type and rank of the grid for bookeeping of coordinates 
        self._size = [None]

        # public facing

        # placeholder for staggerlocs, True if present, False if not
        self._staggerloc = [None]

        # placeholder for the list of numpy arrays which holds the grid bounds
        self._lower_bounds = [None]
        self._upper_bounds = [None]

        # placeholder for the list of numpy arrays which hold the grid coords
        self._coords = [None]

        # mask and area
        self._mask = np.zeros(None)
        self._area = np.zeros(None)

        # create the correct grid
        self._struct = None

        if from_file:
            # create default reg_decomp if it is not passed as an argument
            if reg_decomp is None:
                reg_decomp = [pet_count(), 1]
            # create the grid from file
            self._struct = ESMP_GridCreateFromFile(filename, filetype,
                                                  reg_decomp,
                                                  decompflag=decompflag,
                                                  isSphere=is_sphere,
                                                  addCornerStagger=add_corner_stagger,
                                                  addUserArea=add_user_area,
                                                  addMask=add_mask, 
                                                  varname=varname,
                                                  coordNames=coord_names)
            # grid rank and dims
            if filetype == FileFormat.SCRIP:
                self._rank, self._max_index = ESMP_ScripInq(filename)
                self._ndims = self.rank
            else: # must be GRIDSPEC
                self._rank, self._ndims, self._max_index = ESMP_GridspecInq(filename)
            # stagger is not required for from-file grids, but we need to
            # correctly allocate the space
            staggerloc = [StaggerLoc.CENTER]

            # add corner, this assumes 2D grids right?
            if add_corner_stagger:
                if StaggerLoc.CORNER not in staggerloc:
                    staggerloc.append(StaggerLoc.CORNER)
                _has_corners = True
            
            # set the num_peri_dims so sizes are calculated correctly
            # is_sphere defaults to True
            if is_sphere == False:
                self._num_peri_dims = 0
            else:
                self._num_peri_dims = 1
                self._periodic_dim = 0
                # TODO: we assume that all periodic grids create from file will be periodic across the first
                #       dimension.. is that true?
            
        else:
            # ctypes stuff
            self._struct = ESMP_GridStruct()
            if self.num_peri_dims == 0:
                self._struct = ESMP_GridCreateNoPeriDim(self.max_index,
                                                       coordSys=coord_sys,
                                                       coordTypeKind=coord_typekind)
            elif (self.num_peri_dims == 1):
                self._struct = ESMP_GridCreate1PeriDim(self.max_index,
                                                      periodicDim=periodic_dim,
                                                      poleDim=pole_dim,
                                                      coordSys=coord_sys,
                                                      coordTypeKind=coord_typekind)
                if periodic_dim == None:
                    self._periodic_dim = 0
                    self._pole_dim = 1
            else:
                raise TypeError("Number of periodic dimensions should be 0 or 1")

            # grid rank
            self._rank = self.max_index.size
            self._ndims = self._rank

        # grid type
        if coord_typekind is None:
            self._type = TypeKind.R8
        else:
            self._type = coord_typekind

        # staggerloc
        self._staggerloc = [False for a in range(2**self.rank)]

        # bounds
        self._lower_bounds = [None for a in range(2**self.rank)]
        self._upper_bounds = [None for a in range(2**self.rank)]

        # distributed sizes
        self._size = [None for a in range(2**self.rank)]

        # initialize the coordinates structures
        # index order is [staggerLoc][coord_dim]
        self._coords = [[None for a in range(self.rank)] \
                        for b in range(2**self.rank)]

        # initialize the item structures
        # index order is [staggerLoc][itemDim]
        self._mask = [None for a in range(2**self.rank)]
        self._area = [None for a in range(2**self.rank)]

        # Add coordinates if a staggerloc is specified
        if staggerloc is not None:
            self.add_coords(staggerloc=staggerloc, from_file=from_file)

        # Add items if they are specified, this is done after the
        # mask and area are initialized
        if add_user_area:
            self.add_item(GridItem.AREA, staggerloc=StaggerLoc.CENTER, 
                          from_file=from_file)
        if add_mask:
            self.add_item(GridItem.MASK, staggerloc=StaggerLoc.CENTER, 
                          from_file=from_file)

        # for arbitrary metadata
        self._meta = {}

        # regist with atexit
        import atexit; atexit.register(self.__del__)
        self._finalized = False

    def __del__(self):
        self.destroy()

    def __getitem__(self, slc):
        # no slicing in parallel
        if pet_count() > 1:
            raise SerialMethod

        # format and copy
        slc = get_formatted_slice(slc, self.rank)
        ret = self.copy()

        # coords, mask and area
        ret._coords = [[get_none_or_ssslice(get_none_or_slice(get_none_or_slice(self.coords, stagger), coorddim), slc,
                                            stagger, self.rank)
                        for coorddim in range(self.rank)] for stagger in range(2 ** self.rank)]
        ret._mask = [get_none_or_slice(get_none_or_slice(self.mask, stagger), slc) for stagger in range(2 ** self.rank)]
        ret._area = [get_none_or_slice(get_none_or_slice(self.area, stagger), slc) for stagger in range(2 ** self.rank)]

        # upper bounds are "sliced" by taking the shape of the coords
        ret._upper_bounds = [get_none_or_bound(get_none_or_slice(ret.coords, stagger), 0) for stagger in
                             range(2 ** self.rank)]
        # lower bounds do not need to be sliced yet because slicing is not yet enabled in parallel

        return ret

    def __repr__(self):
        string = ("Grid:\n"
                  "    type = %r"
                  "    areatype = %r"
                  "    rank = %r"
                  "    num_peri_dims = %r"
                  "    periodic_dim = %r"
                  "    pole_dim = %r"
                  "    coord_sys = %r"
                  "    staggerloc = %r"
                  "    lower bounds = %r"
                  "    upper bounds = %r"
                  "    coords = %r"
                  "    mask = %r"
                  "    area = %r"
                  %
                  (self.type,
                   self.areatype,
                   self.rank,
                   self.num_peri_dims,
                   self.periodic_dim,
                   self.pole_dim,
                   self.coord_sys,
                   self.staggerloc,
                   self.lower_bounds,
                   self.upper_bounds,
                   self.coords,
                   self.mask,
                   self.area))

        return string

    @property
    def area(self):
        """
        :rtype: A list of numpy arrays with an entry for every stagger location
            of the :class:`~ESMF.api.grid.Grid`.
        :return: The :class:`~ESMF.api.grid.Grid` cell areas represented as
            numpy arrays of floats of size given by
            ``upper_bounds - lower_bounds``.
        """

        return self._area

    @property
    def areatype(self):
        """
        :rtype: :attr:`~ESMF.api.constants.TypeKind`
        :return: The ESMF typekind of the :class:`~ESMF.api.grid.Grid` cell
            areas.
        """

        return self._areatype

    @property
    def coords(self):
        """
        :rtype: 2D list of numpy arrays of size given by
            ``upper_bounds - lower_bounds``, where the first index represents
            the stagger locations of the :class:`~ESMF.api.grid.Grid` and the
            second index represent the coordinate dimensions of the
            :class:`~ESMF.api.grid.Grid`.
        :return: The coordinates of the :class:`~ESMF.api.grid.Grid`.
        """

        return self._coords

    @property
    def coord_sys(self):
        """
        :rtype: :attr:`~ESMF.api.constants.CoordSys`
        :return: The coordinate system of the :class:`~ESMF.api.grid.Grid`.
        """

        return self._coord_sys

    @property
    def finalized(self):
        """
        :rtype: bool
        :return: Indicate if the underlying ESMF memory for this object has
            been deallocated.
        """

        return self._finalized

    @property
    def has_corners(self):
        """
        :rtype: bool
        :return: A boolean value to tell if the :class:`~ESMF.api.grid.Grid`
            has corners allocated.
        """

        return self._has_corners

    @property
    def lower_bounds(self):
        """
        :rtype: A list of numpy arrays with an entry for every stagger location
            of the :class:`~ESMF.api.grid.Grid`.
        :return: The lower bounds of the :class:`~ESMF.api.grid.Grid`
            represented as numpy arrays of ints of size given by
            ``upper_bounds - lower_bounds``.
        """

        return self._lower_bounds

    @property
    def mask(self):
        """
        :rtype: A list of numpy arrays with an entry for every stagger location
            of the :class:`~ESMF.api.grid.Grid`.
        :return: The mask of the :class:`~ESMF.api.grid.Grid` represented as
            numpy arrays of ints of size given by `
            `upper_bounds - lower_bounds``.
        """

        return self._mask

    @property
    def max_index(self):
        """
        :rtype: A numpy array with as many values as the
            :class:`~ESMF.api.grid.Grid` rank.
        :return: The number of :class:`~ESMF.api.grid.Grid` cells in each
            dimension of the grid.
        """

        return self._max_index

    @property
    def meta(self):
        """
        :rtype: tdk
        :return: tdk
        """

        return self._meta

    @property
    def ndims(self):
        """
        :rtype: int
        :return: The rank of the coordinate arrays of the
            :class:`~ESMF.api.grid.Grid`.
        """

        return self._ndims

    @property
    def num_peri_dims(self):
        """
        :rtype: int
        :return: The total number of periodic dimensions in the
            :class:`~ESMF.api.grid.Grid`.
        """

        return self._num_peri_dims

    @property
    def periodic_dim(self):
        """
        :rtype: int
        :return: The periodic dimension of the :class:`~ESMF.api.grid.Grid`
            (e.g. ``0`` for ``x`` or ``longitude``, ``1`` for ``y`` or
            ``latitude``, etc.).
        """

        return self._periodic_dim

    @property
    def pole_dim(self):
        """
        :rtype: int
        :return: The pole dimension of the :class:`~ESMF.api.grid.Grid`
            (e.g. ``0`` for ``x`` or ``longitude``, ``1`` for ``y`` or
            ``latitude``, etc.).
        """

        return self._pole_dim

    @property
    def rank(self):
        """
        :rtype: int
        :return: The rank of the :class:`~ESMF.api.grid.Grid`.
        """

        return self._rank

    @property
    def size(self):
        """
        :rtype: A list of numpy arrays with an entry for every stagger location
            of the :class:`~ESMF.api.grid.Grid`.
        :return: The size of the :class:`~ESMF.api.grid.Grid` represented as
            numpy arrays of ints of size given by
            ``upper_bounds - lower_bounds``.
        """

        return self._size

    @property
    def staggerloc(self):
        """
        :rtype: list of bools
        :return: The stagger locations that have been allocated for the
            :class:`~ESMF.api.grid.Grid`.
        """

        return self._staggerloc

    @property
    def struct(self):
        """
        :rtype: pointer
        :return: A pointer to the underlying ESMF allocation for the
            :class:`~ESMF.api.grid.Grid`.
        """

        return self._struct

    @property
    def type(self):
        """
        :rtype: :attr:`~ESMF.api.constants.TypeKind`
        :return: The ESMF typekind of the :class:`~ESMF.api.grid.Grid`
            coordinates.
        """
        return self._type

    @property
    def upper_bounds(self):
        """
        :rtype: A list of numpy arrays with an entry for every stagger location
            of the :class:`~ESMF.api.grid.Grid`.
        :return: The upper bounds of the :class:`~ESMF.api.grid.Grid`
            represented as numpy arrays of ints of size given by
            ``upper_bounds - lower_bounds``.
        """
        return self._upper_bounds

    def add_coords(self, staggerloc=None, coord_dim=None, from_file=False):
        """
        Add coordinates to the :class:`~ESMF.api.grid.Grid` at the specified
        stagger location.

        :param StaggerLoc staggerloc: The stagger location of the coordinate
            values. If ``None``, defaults to
            :attr:`~ESMF.api.constants.StaggerLoc.CENTER`
            in 2D and :attr:`~ESMF.api.constants.StaggerLoc.CENTER_VCENTER` in
            3D.
        :param int coord_dim: The dimension number of the coordinates to return
            e.g. ``[x, y, z] = (0, 1, 2)``, or ``[lat, lon] = (0, 1)``
            (coordinates will not be returned if coord_dim is not specified and
            staggerlocs is a list with more than one element).
        :param bool from_file: Boolean for internal use to determine whether the
            :class:`~ESMF.api.grid.Grid` has already been created from file.

        :return: A numpy array of coordinate values if staggerloc and
            coord_dim are specified, otherwise return None.
        """
        if staggerloc is None:
            staggerloc = [StaggerLoc.CENTER]
        else:
            try:
                staggerloc = list(staggerloc)
            except TypeError:
                staggerloc = [staggerloc]

        for stagger in staggerloc:
            if self.coords[stagger][0] is not None:
                warnings.warn("This coordinate has already been added.")
            else:
                # request that ESMF allocate space for the coordinates
                if not from_file:
                    ESMP_GridAddCoord(self, staggerloc=stagger)

                # and now for Python
                self._allocate_coords_(stagger, from_file=from_file)

                # set the staggerlocs to be done
                self.staggerloc[stagger] = True

        if len(staggerloc) == 1 and coord_dim is not None:
            return self.coords[staggerloc[0]][coord_dim]

    def add_item(self, item, staggerloc=None, from_file=False):
        """
        Allocate space for a :class:`~ESMF.api.grid.Grid` item (mask or areas)
        at a specified stagger location.

        *REQUIRED:*

        :param GridItem item: The :attr:`~ESMF.api.constants.GridItem` to
            allocate.

        *OPTIONAL:*

        :param StaggerLoc staggerloc: The stagger location of the item
            values. If ``None``, defaults to
            :attr:`~ESMF.api.constants.StaggerLoc.CENTER`
            in 2D and :attr:`~ESMF.api.constants.StaggerLoc.CENTER_VCENTER` in
            3D.
        :param bool from_file: Boolean for internal use to determine whether the
            :class:`~ESMF.api.grid.Grid` has already been created from file.

        :return: A numpy array of the mask or area values if a single
            staggerloc is given, otherwise return None.
        """
        if staggerloc is None:
            staggerloc = [StaggerLoc.CENTER]
        else:
            try:
                staggerloc = list(staggerloc)
            except TypeError:
                staggerloc = [staggerloc]

        done = True
        for stagger in staggerloc:
            # check to see if they are done
            if item == GridItem.MASK:
                if self.mask[stagger] is not None:
                    raise GridItemAlreadyLinked
                done = False
            elif item == GridItem.AREA:
                if self.area[stagger] is not None:
                    raise GridItemAlreadyLinked
                done = False
            else:
                raise GridItemNotSupported

            if not done:
                # request that ESMF allocate space for the coordinates
                if not from_file:
                    ESMP_GridAddItem(self, item, staggerloc=stagger)

                # and now for Python..
                self._allocate_items_(item, stagger, from_file=from_file)

        if len(staggerloc) is 1:
            if item == GridItem.MASK:
                return self.mask[staggerloc[0]]
            elif item == GridItem.AREA:
                return self.area[staggerloc[0]]
            else:
                raise GridItemNotSupported

    def copy(self):
        """
        Copy a :class:`~ESMF.api.grid.Grid` in an ESMF-safe manner.

        :return: A :class:`~ESMF.api.grid.Grid` shallow copy.
        """
        # shallow copy
        ret = copy(self)
        # don't call ESMF destructor twice on the same shallow Python object
        ret._finalized = True

        return ret

    def destroy(self):
        """
        Release the memory associated with a :class:`~ESMF.api.grid.Grid`.
        """
        if hasattr(self, '_finalized'):
            if not self._finalized:
                ESMP_GridDestroy(self)
                self._finalized = True

    def get_coords(self, coord_dim, staggerloc=None):
        """
        Return a numpy array of coordinates at a specified stagger 
        location. The returned array is NOT a copy, it is
        directly aliased to the underlying memory allocated by ESMF.

        *REQUIRED:*

        :param int coord_dim: The dimension number of the coordinates to return
            e.g. ``[x, y, z] = (0, 1, 2)``, or ``[lat, lon] = (0, 1)``
            (coordinates will not be returned if ``coord_dim`` is not specified
            and ``staggerlocs`` is a list with more than one element).

        *OPTIONAL:*

        :param StaggerLoc staggerloc: The stagger location of the coordinate
            values. If ``None``, defaults to
            :attr:`~ESMF.api.constants.StaggerLoc.CENTER`
            in 2D and :attr:`~ESMF.api.constants.StaggerLoc.CENTER_VCENTER` in
            3D.

        :return: A numpy array of coordinate values at the specified staggerloc.
        """

        ret = None
        # handle the default case
        if staggerloc is None:
            staggerloc = StaggerLoc.CENTER
        elif type(staggerloc) is list:
            raise GridSingleStaggerloc
        elif type(staggerloc) is tuple:
            raise GridSingleStaggerloc

        assert (self.coords[staggerloc][coord_dim] is not None)
        ret = self.coords[staggerloc][coord_dim]

        return ret

    def get_item(self, item, staggerloc=None):
        """
        Return a numpy array of item values at a specified stagger
        location.  The returned array is NOT a copy, it is
        directly aliased to the underlying memory allocated by ESMF.

        *REQUIRED:*

        :param GridItem item: The :attr:`~ESMF.api.constants.GridItem` to
            return.

        *OPTIONAL:*

        :param StaggerLoc staggerloc: The stagger location of the item
            values. If ``None``, defaults to
            :attr:`~ESMF.api.constants.StaggerLoc.CENTER` in 2D and
            :attr:`~ESMF.api.constants.StaggerLoc.CENTER_VCENTER` in 3D.

        :return: A numpy array of mask or area values at the specified staggerloc.
        """

        ret = None
        # handle the default case
        if staggerloc is None:
            staggerloc = StaggerLoc.CENTER
        elif type(staggerloc) is list:
            raise GridSingleStaggerloc
        elif type(staggerloc) is tuple:
            raise GridSingleStaggerloc

        # selec the grid item
        if item == GridItem.MASK:
            assert (self.mask[staggerloc] is not None)
            ret = self.mask[staggerloc]
        elif item == GridItem.AREA:
            assert (self.area[staggerloc] is not None)
            ret = self.area[staggerloc]
        else:
            raise GridItemNotSupported

        return ret

    def set_coords(self, staggerloc, item_data):
        raise MethodNotImplemented
        # check sizes
        # assert (self.coords[staggerloc][:,:,coord_dim].shape == 
        #         coord_data.shape)
        # use user coordinates to initialize underlying ESMF data
        # self.coords[staggerloc][:,:,coord_dim] = coord_data.copy()

    def set_item(self, item, staggerloc, item_data):
        raise MethodNotImplemented
        # check sizes
        # set item_out = item_data.copy()
        # set the item as a grid property and return this pointer
        # self.item[staggerloc_local] = item_out

    ################ Helper functions ##########################################

    def _verify_grid_bounds_(self, stagger):
        if self.lower_bounds[stagger] is None:
            try:
                lb, ub = ESMP_GridGetCoordBounds(self, staggerloc=stagger)
            except:
                raise GridBoundsNotCreated

            self._lower_bounds[stagger] = np.copy(lb)
            self._upper_bounds[stagger] = np.copy(ub)

            # find the local size of this stagger
            self._size[stagger] = np.array(self.upper_bounds[stagger] -
                                       self.lower_bounds[stagger])
        else:
            lb, ub = ESMP_GridGetCoordBounds(self, staggerloc=stagger)
            assert(self.lower_bounds[stagger].all() == lb.all())
            assert(self.upper_bounds[stagger].all() == ub.all())
            assert(self.size[stagger].all() == np.array(ub-lb).all())

    def _allocate_coords_(self, stagger, from_file=False):
        # this could be one of several entry points to the grid,
        # verify that bounds and other necessary data are available
        self._verify_grid_bounds_(stagger)

        # allocate space for the coordinates on the Python side
        self._coords[stagger][0] = np.zeros(shape = (self.size[stagger]),
                                            dtype = constants._ESMF2PythonType[self.type])
        self._coords[stagger][1] = np.zeros(shape = (self.size[stagger]),
                                            dtype = constants._ESMF2PythonType[self.type])
        if self.rank == 3:
            self._coords[stagger][2] = np.zeros(shape = (self.size[stagger]),
                                                dtype = constants._ESMF2PythonType[self.type])

        # link the ESMF allocations to the Python grid properties
        # first if number of coordinate dimensions is equivalent to the grid rank
        if (self.ndims == self.rank) or (self.ndims == 0):
            for xyz in range(self.rank):
                self._link_coord_buffer_(xyz, stagger)
        # and this way if we have 1d coordinates
        elif self.ndims < self.rank:
            if not (self.ndims == 1):
                raise ValueError("Grid does not know how to handle coordinate arrays that are either 1 dimensional"
                                 "  or have dimensionality equivalent to the number coordinate dimensions of the Grid")
            self._link_coord_buffer_1Dcoords(stagger)

        # initialize to zeros, because ESMF doesn't handle that
        if not from_file:
            self._coords[stagger][0][...] = 0
            self._coords[stagger][1][...] = 0
            if self.rank == 3:
               self._coords[stagger][2][...] = 0

    def _allocate_items_(self, item, stagger, from_file=False):
        # this could be one of several entry points to the grid,
        # verify that bounds and other necessary data are available
        self._verify_grid_bounds_(stagger)

        # if the item is a mask it is of type I4
        if item == GridItem.MASK:
            self._mask[stagger] = np.zeros(
                shape=(self.size[stagger]),
                dtype=constants._ESMF2PythonType[TypeKind.I4])
        # if the item is area then it is of type R8
        elif item == GridItem.AREA:
            self._area[stagger] = np.zeros(
                shape=(self.size[stagger]),
                dtype=constants._ESMF2PythonType[TypeKind.R8])
        else:
            raise GridItemNotSupported

        # link the ESMF allocations to the grid properties
        self._link_item_buffer_(item, stagger)

        # initialize to zeros, because ESMF doesn't handle that
        if not from_file:
            if item == GridItem.MASK:
                self._mask[stagger][...] = 1
            elif item == GridItem.AREA:
                self._area[stagger][...] = 0
            else:
                raise GridItemNotSupported

    def _link_coord_buffer_(self, coord_dim, stagger):
        # get the data pointer and bounds of the ESMF allocation
        data = ESMP_GridGetCoordPtr(self, coord_dim, staggerloc=stagger)
        lb, ub = ESMP_GridGetCoordBounds(self, staggerloc=stagger)

        gridCoordP = ndarray_from_esmf(data, self.type, ub-lb)

        # alias the coordinates to a grid property
        self._coords[stagger][coord_dim] = gridCoordP

        if stagger in (StaggerLoc.CORNER, StaggerLoc.CORNER_VFACE):
            self._has_corners = True

    def _link_coord_buffer_1Dcoords(self, stagger):
        # get the data pointer and bounds of the ESMF allocation
        lb, ub = ESMP_GridGetCoordBounds(self, staggerloc=stagger)

        gc0 = ndarray_from_esmf(ESMP_GridGetCoordPtr(self, 0, staggerloc=stagger), self.type, ((ub - lb)[0],))
        gc1 = ndarray_from_esmf(ESMP_GridGetCoordPtr(self, 1, staggerloc=stagger), self.type, ((ub - lb)[1],))
        if self.rank == 3:
            gc2 = ndarray_from_esmf(ESMP_GridGetCoordPtr(self, 2, staggerloc=stagger), self.type, ((ub - lb)[2],))
            gc00, gc11, gc22 = np.meshgrid(gc0, gc1, gc2, indexing="ij")
        elif self.rank == 2:
            gc00, gc11 = np.meshgrid(gc0, gc1, indexing="ij")
        else:
            raise ValueError("Grid rank must be 2 or 3")

        # alias the coordinates to a grid property
        self._coords[stagger][0] = gc00
        self._coords[stagger][1] = gc11
        if self.rank == 3:
            self._coords[stagger][2] = gc22

        if stagger in (StaggerLoc.CORNER, StaggerLoc.CORNER_VFACE):
            self._has_corners = True

    def _link_item_buffer_(self, item, stagger):

        # # check to see if they are done
        # if item == GridItem.MASK:
        #     if self.mask[stagger] is not None:
        #         raise GridItemAlreadyLinked
        # elif item == GridItem.AREA:
        #     if self.area[stagger] is not None:
        #         raise GridItemAlreadyLinked
        # else:
        #     raise GridItemNotSupported

        # get the data pointer and bounds of the ESMF allocation
        data = ESMP_GridGetItem(self, item, staggerloc=stagger)
        lb, ub = ESMP_GridGetCoordBounds(self, staggerloc=stagger)

        # create Array of the appropriate type the appropriate type
        if item == GridItem.MASK:
            self._mask[stagger] = ndarray_from_esmf(data, TypeKind.I4, ub-lb)
        elif item == GridItem.AREA:
            self._area[stagger] = ndarray_from_esmf(data, TypeKind.R8, ub-lb)
        else:
            raise GridItemNotSupported

    def _write_(self, filename, staggerloc=None):
        """
        Write a Grid to vtk formatted file at a specified stagger 
        location.

        *REQUIRED:*

        :param str filename: The name of the file, .vtk will be appended.

        *OPTIONAL:*

        :param StaggerLoc staggerloc: The stagger location of the item
            values. If ``None``, defaults to
            :attr:`~ESMF.api.constants.StaggerLoc.CENTER` in 2D and
            :attr:`~ESMF.api.constants.StaggerLoc.CENTER_VCENTER` in 3D.
        """

        # handle the default case
        if staggerloc is None:
            staggerloc = StaggerLoc.CENTER
        elif type(staggerloc) is list:
            raise GridSingleStaggerloc
        elif type(staggerloc) is tuple:
            raise GridSingleStaggerloc

        ESMP_GridWrite(self, filename, staggerloc=staggerloc)

from auto_lens.profiles import geometry_profiles

import numpy as np


class RayTrace(object):
    """The ray-tracing calculations, defined by a set of grids of coordinates and planes containing every galaxy in \
    the lensing system. These are computed in order of ascending galaxy redshift.

    The ray-tracing calculations between every plane is determined using the angular diameter distances between each \
    set of galaxies.

    This is used to perform all ray-tracing calculations and for converting dimensionless measurements (e.g. \
    arc-seconds, mass) to physical units.

    Parameters
    ----------
    galaxies : [Galaxy]
        The list of galaxies that form the lensing planes.
    cosmological_model : astropy.cosmology.FLRW
        The assumed cosmology for this ray-tracing calculation.
    """
    pass


class TraceImageAndSource(object):

    def __init__(self, lens_galaxies, source_galaxies, image_plane_grids):
        """The ray-tracing calculations, defined by a lensing system with just one image-plane and source-plane.

        This has no associated cosmology, thus all calculations are performed in arc seconds and galaxies do not need \
        known redshift measurements. For computational efficiency, it is recommend this ray-tracing class is used for \
        lens modeling, provided cosmological information is not necessary.

        Parameters
        ----------
        lens_galaxies : [Galaxy]
            The list of lens galaxies in the image-plane.
        source_galaxies : [Galaxy]
            The list of source galaxies in the source-plane.
        image_plane_grids : RayTracingGrids
            The image-plane grids of coordinates where ray-tracing calculation are performed, (this includes the image.grid, \
            sub_grid, blurring.grid etc.).
        """
        self.image_plane = ImagePlane(lens_galaxies, image_plane_grids)

        source_plane_grids = self.image_plane.trace_to_next_plane()

        self.source_plane = SourcePlane(source_galaxies, source_plane_grids)


class Plane(object):
    """Represents a plane of galaxies and grids.

    Parameters
    ----------
    galaxies : [Galaxy]
        The galaxies in the plane.
    grids : grids.RayTracingGrids
        The grids of (x,y) coordinates in the plane, including the image grid, sub-grid, blurring grid, etc.
    """
    def __init__(self, galaxies, grids):

        self.galaxies = galaxies
        self.grids = grids


class LensPlane(Plane):

    def __init__(self, galaxies, grids):
        """Represents a lens-plane, a set of galaxies and grids at an intermediate redshift in the ray-tracing \
        calculation.

        A lens-plane is not the final ray-tracing plane and its grids will be traced too another higher \
        redshift plane. Thus, the deflection angles due to the plane's galaxies are calculated.

        Parameters
        ----------
        galaxies : [Galaxy]
            The galaxies in the image_grid-plane.
        grids : grids.RayTracingGrids
            The grids of (x,y) coordinates in the plane, including the image grid, sub-grid, blurring grid, etc.
        """

        super(LensPlane, self).__init__(galaxies, grids)

        self.deflection_angles = self.deflection_angles_on_grids()

    def deflection_angles_on_grids(self):
        """Compute the deflection angles on the grids"""
        return self.grids.deflection_grids_from_galaxies(self.galaxies)

    def trace_to_next_plane(self):
        """Trace the grids to the next plane.

        NOTE : This does not work for multiplane lensing, which requires one to use the previous plane's deflection \
        angles to perform the tracing. I guess we'll ultimately call this class 'LensPlanes' and have it as a list.
        """
        return self.grids.new_grids_from_deflections(self.deflection_angles)


class ImagePlane(LensPlane):

    def __init__(self, galaxies, grids):
        """Represents an image-plane, a set of galaxies and grids at the lowest redshift in the lens ray-tracing \
        calculation.

        The image-plane is, by definition, a lens-plane, thus the deflection angles for each grid are computed.

        The image-plane coodinates are defined on the observed image's uniform regular grid. Calculating its model \
        images from its light profiles exploits this uniformity to perform more efficient and precise calculations via \
        an iterative sub-gridding approach.

        The light profiles of galaxies at higher redshifts (and therefore in different lens-planes) can be assigned to \
        the ImagePlane. This occurs when:

        1) The efficiency and precision offered by computing the light profile on a uniform grid is preferred and \
        won't lead noticeable inaccuracy. For example, computing the light profile of the main lens galaxy, ignoring \
        minor lensing effects due to a low mass foreground substructure.

        2) When evaluating the light profile in its lens-plane is inaccurate. For example, when modeling the \
        point-source images of a lensed quasar, effects like micro-lensing means lens-plane modeling will be inaccurate.

        Parameters
        ----------
        galaxies : [Galaxy]
            The galaxies in the image_grid-plane.
        grids : grids.RayTracingGrids
            The grids of (x,y) coordinates in the plane, including the image grid, sub-grid, blurring grid, etc.
        """

        super(ImagePlane, self).__init__(galaxies, grids)

    # TODO : Add iterative sub-grid to this routine / class. Can we use the iterative sub-grid you made in
    # TODO : geometry profiles?

    def generate_light_profile_image(self, iterative_sub_grid=True, iterative_sub_grid_accuracy=1e-4):
        """Generate the image-plane image of this ray-tracing instance.

        This uses the image-plane grid coordinates and galaxy light profiles. By default, an iterative sub-grid is \
        used, which computes all intensity values to a specified degree of accuracy by computing them on finer and \
        finer sub-grids until a threshold relative accuracy is reached.
        """

        if iterative_sub_grid is False:

            return sum(map(lambda galaxy : galaxy.intensity_grid(self.grids.image.grid), self.galaxies))


class SourcePlane(Plane):

    def __init__(self, galaxies, grids):
        """Represents a source-plane, a set of galaxies and grids at the highest redshift in the ray-tracing \
        calculation.

        A source-plane is the final ray-tracing plane, thus the deflection angles due to the plane's galaxies are \
        not calculated.

        Parameters
        ----------
        galaxies : [Galaxy]
            The galaxies in the source-plane.
        grids : grids.RayTracingGrids
            The grids of (x,y) coordinates in the plane, including the image grid, sub-grid, blurring grid, etc.
        """
        super(SourcePlane, self).__init__(galaxies, grids)
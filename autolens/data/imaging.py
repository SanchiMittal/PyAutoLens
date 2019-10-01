import logging

from scipy.stats import norm

import scipy.signal
from astropy import units
from skimage.transform import resize, rescale

import numpy as np

from autolens import exc
from autoarray import grids
from autoarray import mask as msk
from autolens.data import abstract_data
from autoarray import scaled_array
from autoarray.util import array_util
from autoarray.mapping_util import grid_mapping_util
from autolens.model.profiles.light_profiles import EllipticalGaussian

logger = logging.getLogger(__name__)


class ImagingData(abstract_data.AbstractData):
    def __init__(
        self,
        image,
        pixel_scale,
        psf,
        noise_map=None,
        background_noise_map=None,
        poisson_noise_map=None,
        exposure_time_map=None,
        background_sky_map=None,
        name=None,
        **kwargs
    ):
        """A collection of 2D Imaging data (an image, noise-map, psf, etc.)

        Parameters
        ----------
        image : scaled_array.ScaledSquarePixels
            The array of the image data_type, in units of electrons per second.
        pixel_scale : float
            The size of each pixel in arc seconds.
        psf : PSF
            An array describing the PSF kernel of the image.
        noise_map : NoiseMap | float | ndarray
            An array describing the RMS standard deviation error in each pixel, preferably in units of electrons per
            second.
        background_noise_map : NoiseMap
            An array describing the RMS standard deviation error in each pixel due to the background sky noise_map,
            preferably in units of electrons per second.
        poisson_noise_map : NoiseMap
            An array describing the RMS standard deviation error in each pixel due to the Poisson counts of the source,
            preferably in units of electrons per second.
        exposure_time_map : scaled_array.Scaled
            An array describing the effective exposure time in each imaging pixel.
        background_sky_map : scaled_array.Scaled
            An array describing the background sky.
        """

        super(ImagingData, self).__init__(
            data=image,
            pixel_scale=pixel_scale,
            noise_map=noise_map,
            exposure_time_map=exposure_time_map,
        )

        self.psf = psf
        self.name = name
        self.background_noise_map = background_noise_map
        self.poisson_noise_map = poisson_noise_map
        self.background_sky_map = background_sky_map

    @property
    def image(self):
        return self._data

    @property
    def shape(self):
        return self.image.shape

    def new_imaging_data_with_binned_up_arrays(self, bin_up_factor):

        image = self.bin_up_scaled_array(
            scaled_array=self.image, bin_up_factor=bin_up_factor, method="mean"
        )
        psf = self.psf.new_psf_with_rescaled_odd_dimensioned_array(
            rescale_factor=1.0 / bin_up_factor, renormalize=True
        )
        noise_map = self.bin_up_scaled_array(
            scaled_array=self.noise_map,
            bin_up_factor=bin_up_factor,
            method="quadrature",
        )
        background_noise_map = self.bin_up_scaled_array(
            scaled_array=self.background_noise_map,
            bin_up_factor=bin_up_factor,
            method="quadrature",
        )
        poisson_noise_map = self.bin_up_scaled_array(
            scaled_array=self.poisson_noise_map,
            bin_up_factor=bin_up_factor,
            method="quadrature",
        )
        exposure_time_map = self.bin_up_scaled_array(
            scaled_array=self.exposure_time_map,
            bin_up_factor=bin_up_factor,
            method="sum",
        )
        background_sky_map = self.bin_up_scaled_array(
            scaled_array=self.background_sky_map,
            bin_up_factor=bin_up_factor,
            method="mean",
        )

        return ImagingData(
            image=image,
            pixel_scale=self.pixel_scale * bin_up_factor,
            psf=psf,
            noise_map=noise_map,
            background_noise_map=background_noise_map,
            poisson_noise_map=poisson_noise_map,
            exposure_time_map=exposure_time_map,
            background_sky_map=background_sky_map,
            name=self.name,
        )

    def new_imaging_data_with_resized_arrays(
        self, new_shape, new_centre_pixels=None, new_centre_arcsec=None
    ):

        image = self.resize_scaled_array(
            scaled_array=self.image,
            new_shape=new_shape,
            new_centre_pixels=new_centre_pixels,
            new_centre_arcsec=new_centre_arcsec,
        )

        noise_map = self.resize_scaled_array(
            scaled_array=self.noise_map,
            new_shape=new_shape,
            new_centre_pixels=new_centre_pixels,
            new_centre_arcsec=new_centre_arcsec,
        )

        background_noise_map = self.resize_scaled_array(
            scaled_array=self.background_noise_map,
            new_shape=new_shape,
            new_centre_pixels=new_centre_pixels,
            new_centre_arcsec=new_centre_arcsec,
        )

        poisson_noise_map = self.resize_scaled_array(
            scaled_array=self.poisson_noise_map,
            new_shape=new_shape,
            new_centre_pixels=new_centre_pixels,
            new_centre_arcsec=new_centre_arcsec,
        )

        exposure_time_map = self.resize_scaled_array(
            scaled_array=self.exposure_time_map,
            new_shape=new_shape,
            new_centre_pixels=new_centre_pixels,
            new_centre_arcsec=new_centre_arcsec,
        )

        background_sky_map = self.resize_scaled_array(
            scaled_array=self.background_sky_map,
            new_shape=new_shape,
            new_centre_pixels=new_centre_pixels,
            new_centre_arcsec=new_centre_arcsec,
        )

        return ImagingData(
            image=image,
            pixel_scale=self.pixel_scale,
            psf=self.psf,
            noise_map=noise_map,
            background_noise_map=background_noise_map,
            poisson_noise_map=poisson_noise_map,
            exposure_time_map=exposure_time_map,
            background_sky_map=background_sky_map,
            name=self.name,
        )

    def new_imaging_data_with_resized_psf(self, new_shape):
        psf = self.resize_scaled_array(scaled_array=self.psf, new_shape=new_shape)
        return ImagingData(
            image=self.image,
            pixel_scale=self.pixel_scale,
            psf=psf,
            noise_map=self.noise_map,
            background_noise_map=self.background_noise_map,
            poisson_noise_map=self.poisson_noise_map,
            exposure_time_map=self.exposure_time_map,
            background_sky_map=self.background_sky_map,
            name=self.name,
        )

    def new_imaging_data_with_modified_image(self, modified_image):

        return ImagingData(
            image=modified_image,
            pixel_scale=self.pixel_scale,
            psf=self.psf,
            noise_map=self.noise_map,
            background_noise_map=self.background_noise_map,
            poisson_noise_map=self.poisson_noise_map,
            exposure_time_map=self.exposure_time_map,
            background_sky_map=self.background_sky_map,
            name=self.name,
        )

    def new_imaging_data_with_poisson_noise_added(self, seed=-1):

        image_with_sky = self.image + self.background_sky_map

        image_with_sky_and_noise = image_with_sky + generate_poisson_noise(
            image=image_with_sky, exposure_time_map=self.exposure_time_map, seed=seed
        )

        image_with_noise = image_with_sky_and_noise - self.background_sky_map

        return ImagingData(
            image=image_with_noise,
            pixel_scale=self.pixel_scale,
            psf=self.psf,
            noise_map=self.noise_map,
            background_noise_map=self.background_noise_map,
            poisson_noise_map=self.poisson_noise_map,
            name=self.name,
        )

    def new_imaging_data_converted_from_electrons(self):

        image = self.array_from_counts_to_electrons_per_second(array=self.image)
        noise_map = self.array_from_counts_to_electrons_per_second(array=self.noise_map)
        background_noise_map = self.array_from_counts_to_electrons_per_second(
            array=self.background_noise_map
        )
        poisson_noise_map = self.array_from_counts_to_electrons_per_second(
            array=self.poisson_noise_map
        )
        background_sky_map = self.array_from_counts_to_electrons_per_second(
            array=self.background_sky_map
        )

        return ImagingData(
            image=image,
            pixel_scale=self.pixel_scale,
            psf=self.psf,
            noise_map=noise_map,
            background_noise_map=background_noise_map,
            poisson_noise_map=poisson_noise_map,
            exposure_time_map=self.exposure_time_map,
            background_sky_map=background_sky_map,
            name=self.name,
        )

    def new_imaging_data_converted_from_adus(self, gain):

        image = self.array_from_adus_to_electrons_per_second(
            array=self.image, gain=gain
        )
        noise_map = self.array_from_adus_to_electrons_per_second(
            array=self.noise_map, gain=gain
        )
        background_noise_map = self.array_from_adus_to_electrons_per_second(
            array=self.background_noise_map, gain=gain
        )
        poisson_noise_map = self.array_from_adus_to_electrons_per_second(
            array=self.poisson_noise_map, gain=gain
        )
        background_sky_map = self.array_from_adus_to_electrons_per_second(
            array=self.background_sky_map, gain=gain
        )

        return ImagingData(
            image=image,
            pixel_scale=self.pixel_scale,
            psf=self.psf,
            noise_map=noise_map,
            background_noise_map=background_noise_map,
            poisson_noise_map=poisson_noise_map,
            exposure_time_map=self.exposure_time_map,
            background_sky_map=background_sky_map,
            name=self.name,
        )

    def new_imaging_data_with_signal_to_noise_limit(self, signal_to_noise_limit):

        noise_map_limit = np.where(
            self.signal_to_noise_map > signal_to_noise_limit,
            np.abs(self.image) / signal_to_noise_limit,
            self.noise_map,
        )

        return ImagingData(
            image=self.image,
            pixel_scale=self.pixel_scale,
            psf=self.psf,
            noise_map=noise_map_limit,
            background_noise_map=self.background_noise_map,
            poisson_noise_map=self.poisson_noise_map,
            exposure_time_map=self.exposure_time_map,
            background_sky_map=self.background_sky_map,
            name=self.name,
        )

    @property
    def background_noise_map_counts(self):
        """ The background noise_maps mappers in units of counts."""
        return self.array_from_electrons_per_second_to_counts(self.background_noise_map)

    @property
    def estimated_noise_map_counts(self):
        """ The estimated noise_maps mappers of the image (using its background noise_maps mappers and image values
        in counts) in counts.
        """
        return np.sqrt(
            (np.abs(self.image_counts) + np.square(self.background_noise_map_counts))
        )

    @property
    def estimated_noise_map(self):
        """ The estimated noise_maps mappers of the image (using its background noise_maps mappers and image values
        in counts) in electrons per second.
        """
        estimated_noise_map_1d = self.array_from_counts_to_electrons_per_second(
            self.estimated_noise_map_counts
        )
        return self._data.mask.scaled_array_from_array_1d(array_1d=estimated_noise_map_1d)

    def background_noise_from_edges(self, no_edges):
        """Estimate the background signal_to_noise_ratio by binning data_to_image located at the edge(s) of an image
        into a histogram and fitting a Gaussian profiles to this histogram. The standard deviation (sigma) of this
        Gaussian gives a signal_to_noise_ratio estimate.

        Parameters
        ----------
        no_edges : int
            Number of edges used to estimate the background signal_to_noise_ratio.

        """

        edges = []

        for edge_no in range(no_edges):
            top_edge = self.image[edge_no, edge_no : self.image.shape[1] - edge_no]
            bottom_edge = self.image[
                self.image.shape[0] - 1 - edge_no,
                edge_no : self.image.shape[1] - edge_no,
            ]
            left_edge = self.image[
                edge_no + 1 : self.image.shape[0] - 1 - edge_no, edge_no
            ]
            right_edge = self.image[
                edge_no + 1 : self.image.shape[0] - 1 - edge_no,
                self.image.shape[1] - 1 - edge_no,
            ]

            edges = np.concatenate(
                (edges, top_edge, bottom_edge, right_edge, left_edge)
            )

        return norm.fit(edges)[1]

    def __array_finalize__(self, obj):
        if isinstance(obj, ImagingData):
            try:
                self.image = obj.image
                self.pixel_scale = obj.pixel_scale
                self.psf = obj.psf
                self.noise_map = obj.noise_map
                self.background_noise_map = obj.background_noise_map
                self.poisson_noise_map = obj.poisson_noise_map
                self.exposure_time_map = obj.exposure_time_map
                self.background_sky_map = obj.background_sky_map
                self.origin = obj.origin
            except AttributeError:
                logger.debug(
                    "Original object in Imaging.__array_finalize__ missing one or more attributes"
                )


class NoiseMap(abstract_data.AbstractNoiseMap):
    @classmethod
    def from_image_and_background_noise_map(
        cls,
        pixel_scale,
        image,
        background_noise_map,
        exposure_time_map,
        gain=None,
        convert_from_electrons=False,
        convert_from_adus=False,
    ):

        if not convert_from_electrons and not convert_from_adus:
            return NoiseMap.from_2d(
                array_2d=np.sqrt(
                    np.abs(
                        ((background_noise_map.in_2d) * exposure_time_map.in_2d) ** 2.0
                        + (image.in_2d) * exposure_time_map.in_2d
                    )
                )
                / (exposure_time_map.in_2d),
                pixel_scale=pixel_scale,
            )
        elif convert_from_electrons:
            return NoiseMap.from_2d(
                array_2d=np.sqrt(np.abs(background_noise_map.in_2d ** 2.0 + image.in_2d)),
                pixel_scale=pixel_scale,
            )
        elif convert_from_adus:
            return NoiseMap.from_2d(
                array_2d=np.sqrt(
                    np.abs((gain * background_noise_map.in_2d) ** 2.0 + gain * image.in_2d)
                )
                / gain,
                pixel_scale=pixel_scale,
            )


class PSF(scaled_array.Scaled):

    # noinspection PyUnusedLocal
    def __new__(cls, sub_array_1d, mask, renormalize=False, *args, **kwargs):
        """ A hyper array with square-pixels.

        Parameters
        ----------
        sub_array_1d: ndarray
            An array representing image (e.g. an image, noise-map, etc.)
        pixel_scales: (float, float)
            The arc-second to pixel conversion factor of each pixel.
        origin : (float, float)
            The arc-second origin of the hyper array's coordinate system.
        """

#        obj = scaled_array.Scaled(sub_array_1d=sub_array_1d, mask=mask)

        obj = super(PSF, cls).__new__(cls=cls, sub_array_1d=sub_array_1d, mask=mask)

        if renormalize:
            obj[:] = np.divide(obj, np.sum(obj))

        return obj

    @classmethod
    def from_2d(cls, array_2d, pixel_scale, origin=(0.0, 0.0), renormalize=False):

        mask = msk.Mask.unmasked_from_shape_pixel_scales_and_sub_size(
            shape=array_2d.shape,
            pixel_scales=(pixel_scale, pixel_scale),
            sub_size=1,
            origin=origin,
        )

        scaled_array = mask.scaled_array_from_array_2d(array_2d=array_2d)
        return PSF(sub_array_1d=scaled_array, mask=mask, renormalize=renormalize)

    @classmethod
    def from_array_2d_and_pixel_scales(cls, array_2d, pixel_scales, origin=(0.0, 0.0), renormalize=False):

        mask = msk.Mask.unmasked_from_shape_pixel_scales_and_sub_size(
            shape=array_2d.shape,
            pixel_scales=pixel_scales,
            sub_size=1,
            origin=origin,
        )

        scaled_array = mask.scaled_array_from_array_2d(array_2d=array_2d)
        return PSF(sub_array_1d=scaled_array, mask=mask, renormalize=renormalize)

    @classmethod
    def from_no_blurring_kernel(cls, pixel_scale):

        array = np.array([[0.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 0.0]])

        return PSF.from_2d(array_2d=array, pixel_scale=pixel_scale, renormalize=False)

    @classmethod
    def from_gaussian(
        cls, shape, pixel_scale, sigma, centre=(0.0, 0.0), axis_ratio=1.0, phi=0.0
    ):
        """Simulate the PSF as an elliptical Gaussian profile."""
        from autolens.model.profiles.light_profiles import EllipticalGaussian

        gaussian = EllipticalGaussian(
            centre=centre, axis_ratio=axis_ratio, phi=phi, intensity=1.0, sigma=sigma
        )

        grid = grids.Grid.from_shape_pixel_scale_and_sub_size(
            shape=shape, pixel_scale=pixel_scale, sub_size=1
        )

        gaussian = gaussian.profile_image_from_grid(grid=grid)

        return PSF.from_2d(array_2d=gaussian.in_2d_binned, pixel_scale=pixel_scale, renormalize=True)

    @classmethod
    def from_as_gaussian_via_alma_fits_header_parameters(
        cls, shape, pixel_scale, y_stddev, x_stddev, theta, centre=(0.0, 0.0)
    ):

        x_stddev = (
            x_stddev * (units.deg).to(units.arcsec) / (2.0 * np.sqrt(2.0 * np.log(2.0)))
        )
        y_stddev = (
            y_stddev * (units.deg).to(units.arcsec) / (2.0 * np.sqrt(2.0 * np.log(2.0)))
        )

        axis_ratio = x_stddev / y_stddev

        gaussian = EllipticalGaussian(
            centre=centre,
            axis_ratio=axis_ratio,
            phi=90.0 - theta,
            intensity=1.0,
            sigma=y_stddev,
        )

        from autoarray import grids

        grid = grids.Grid.from_shape_pixel_scale_and_sub_size(
            shape=shape, pixel_scale=pixel_scale, sub_size=1
        )

        gaussian = gaussian.profile_image_from_grid(grid=grid)

        return PSF.from_2d(array_2d=gaussian.in_2d_binned, pixel_scale=pixel_scale, renormalize=True)

    @classmethod
    def from_fits_renormalized(cls, file_path, hdu, pixel_scale):
        """Loads a PSF from fits and renormalizes it

        Parameters
        ----------
        pixel_scale
        file_path: String
            The path to the file containing the PSF
        hdu : int
            The HDU the PSF is stored in the .fits file.

        Returns
        -------
        psf: PSF
            A renormalized PSF instance
        """
        psf = PSF.from_fits_with_scale(file_path=file_path, hdu=hdu, pixel_scale=pixel_scale)
        psf[:] = np.divide(psf, np.sum(psf))
        return psf

    @classmethod
    def from_fits_with_scale(cls, file_path, hdu, pixel_scale):
        """
        Loads the PSF from a .fits file.

        Parameters
        ----------
        pixel_scale
        file_path: String
            The path to the file containing the PSF
        hdu : int
            The HDU the PSF is stored in the .fits file.
        """
        return PSF.from_2d(
            array_2d=array_util.numpy_array_2d_from_fits(file_path=file_path, hdu=hdu),
            pixel_scale=pixel_scale,
        )

    def new_psf_with_rescaled_odd_dimensioned_array(
        self, rescale_factor, renormalize=True
    ):

        psf_rescaled = rescale(
            self.in_2d,
            rescale_factor,
            anti_aliasing=False,
            mode="constant",
            multichannel=False,
        )

        if psf_rescaled.shape[0] % 2 == 0 and psf_rescaled.shape[1] % 2 == 0:
            psf_rescaled = resize(
                psf_rescaled,
                output_shape=(psf_rescaled.shape[0] + 1, psf_rescaled.shape[1] + 1),
                anti_aliasing=False,
                mode="constant",
            )
        elif psf_rescaled.shape[0] % 2 == 0 and psf_rescaled.shape[1] % 2 != 0:
            psf_rescaled = resize(
                psf_rescaled,
                output_shape=(psf_rescaled.shape[0] + 1, psf_rescaled.shape[1]),
                anti_aliasing=False,
                mode="constant",
            )
        elif psf_rescaled.shape[0] % 2 != 0 and psf_rescaled.shape[1] % 2 == 0:
            psf_rescaled = resize(
                psf_rescaled,
                output_shape=(psf_rescaled.shape[0], psf_rescaled.shape[1] + 1),
                anti_aliasing=False,
                mode="constant",
            )

        pixel_scale_factors = (
            self.mask.shape[0] / psf_rescaled.shape[0],
            self.mask.shape[1] / psf_rescaled.shape[1],
        )
        pixel_scales = (
            self.mask.pixel_scales[0] * pixel_scale_factors[0],
            self.mask.pixel_scales[1] * pixel_scale_factors[1],
        )


        return PSF.from_array_2d_and_pixel_scales(
            array_2d=psf_rescaled,
            pixel_scales=pixel_scales,
            renormalize=renormalize,
        )

    def new_psf_with_renormalized_array(self):
        """Renormalize the PSF such that its data_vector values sum to unity."""
        return PSF(sub_array_1d=self, mask=self.mask, renormalize=True)

    def convolved_array_2d_from_array_2d(self, array_2d):
        """
        Convolve an array with this PSF

        Parameters
        ----------
        image : ndarray
            An array representing the image the PSF is convolved with.

        Returns
        -------
        convolved_image : ndarray
            An array representing the image after convolution.

        Raises
        ------
        KernelException if either PSF psf dimension is odd
        """
        if self.mask.shape[0] % 2 == 0 or self.mask.shape[1] % 2 == 0:
            raise exc.ConvolutionException("PSF Kernel must be odd")

        return scipy.signal.convolve2d(array_2d, self.in_2d, mode="same")

    def convolved_scaled_array_from_array_2d_and_mask(self, array_2d, mask):
        """
        Convolve an array with this PSF

        Parameters
        ----------
        image : ndarray
            An array representing the image the PSF is convolved with.

        Returns
        -------
        convolved_image : ndarray
            An array representing the image after convolution.

        Raises
        ------
        KernelException if either PSF psf dimension is odd
        """
        return mask.scaled_array_from_array_2d(array_2d=self.convolved_array_2d_from_array_2d(array_2d=array_2d))


class PoissonNoiseMap(NoiseMap):
    @classmethod
    def from_image_and_exposure_time_map(
        cls,
        pixel_scale,
        image,
        exposure_time_map,
        gain=None,
        convert_from_electrons=False,
        convert_from_adus=False,
    ):
        if not convert_from_electrons and not convert_from_adus:
            return PoissonNoiseMap.from_2d(
                array_2d=np.sqrt(np.abs(image.in_2d) * exposure_time_map.in_2d) / (exposure_time_map.in_2d),
                pixel_scale=pixel_scale,
            )
        elif convert_from_electrons:
            return PoissonNoiseMap.from_2d(
                array_2d=np.sqrt(np.abs(image.in_2d)), pixel_scale=pixel_scale
            )
        elif convert_from_adus:
            return NoiseMap.from_2d(
                array_2d=np.sqrt(gain * np.abs(image.in_2d)) / gain, pixel_scale=pixel_scale
            )


class SimulatedImagingData(ImagingData):
    def __init__(
        self,
        image,
        pixel_scale,
        psf,
        noise_map=None,
        background_noise_map=None,
        poisson_noise_map=None,
        exposure_time_map=None,
        background_sky_map=None,
        noise_realization=None,
        name=None,
        **kwargs
    ):

        super(SimulatedImagingData, self).__init__(
            image=image,
            pixel_scale=pixel_scale,
            psf=psf,
            noise_map=noise_map,
            background_noise_map=background_noise_map,
            poisson_noise_map=poisson_noise_map,
            exposure_time_map=exposure_time_map,
            background_sky_map=background_sky_map,
            name=name,
            kwargs=kwargs,
        )

        self.noise_realization = noise_realization

    @classmethod
    def from_deflections_galaxies_and_exposure_arrays(
        cls,
        deflections,
        pixel_scale,
        galaxies,
        exposure_time,
        psf=None,
        exposure_time_map=None,
        background_sky_level=0.0,
        background_sky_map=None,
        add_noise=True,
        noise_if_add_noise_false=0.1,
        noise_seed=-1,
        name=None,
    ):

        shape = (deflections.mask.shape[0], deflections.mask.shape[1])

        grid = grids.Grid.from_shape_pixel_scale_and_sub_size(
            shape=shape, pixel_scale=pixel_scale, sub_size=1
        )

        deflected_grid_1d = grid.in_1d - deflections.in_1d

        image_2d = sum(
            map(
                lambda g: g.profile_image_from_grid(
                    grid=deflected_grid_1d,
                ),
                galaxies,
            )
        )

        return cls.from_image_and_exposure_arrays(
            image=image_2d,
            pixel_scale=pixel_scale,
            exposure_time=exposure_time,
            psf=psf,
            exposure_time_map=exposure_time_map,
            background_sky_level=background_sky_level,
            background_sky_map=background_sky_map,
            add_noise=add_noise,
            noise_if_add_noise_false=noise_if_add_noise_false,
            noise_seed=noise_seed,
            name=name,
        )

    @classmethod
    def from_tracer_grid_and_exposure_arrays(
        cls,
        tracer,
        grid,
        pixel_scale,
        exposure_time,
        psf=None,
        exposure_time_map=None,
        background_sky_level=0.0,
        background_sky_map=None,
        add_noise=True,
        noise_if_add_noise_false=0.1,
        noise_seed=-1,
        name=None,
    ):
        """
        Create a realistic simulated image by applying effects to a plain simulated image.

        Parameters
        ----------
        name
        image : ndarray
            The image before simulating (e.g. the lens and source galaxies before optics blurring and Imaging read-out).
        pixel_scale: float
            The scale of each pixel in arc seconds
        exposure_time_map : ndarray
            An array representing the effective exposure time of each pixel.
        psf: PSF
            An array describing the PSF the simulated image is blurred with.
        background_sky_map : ndarray
            The value of background sky in every image pixel (electrons per second).
        add_noise: Bool
            If True poisson noise_maps is simulated and added to the image, based on the total counts in each image
            pixel
        noise_seed: int
            A seed for random noise_maps generation
        """

        if psf is not None:
            image_2d = tracer.padded_profile_image_2d_from_grid_and_psf_shape(
                grid=grid, psf_shape=psf.shape
            )
        else:
            image_2d = tracer.profile_image_from_grid(grid=grid)

        return cls.from_image_and_exposure_arrays(
            image=image_2d,
            pixel_scale=pixel_scale,
            exposure_time=exposure_time,
            psf=psf,
            exposure_time_map=exposure_time_map,
            background_sky_level=background_sky_level,
            background_sky_map=background_sky_map,
            add_noise=add_noise,
            noise_if_add_noise_false=noise_if_add_noise_false,
            noise_seed=noise_seed,
            name=name,
        )

    @classmethod
    def from_image_and_exposure_arrays(
        cls,
        image,
        pixel_scale,
        exposure_time,
        psf=None,
        exposure_time_map=None,
        background_sky_level=0.0,
        background_sky_map=None,
        add_noise=True,
        noise_if_add_noise_false=0.1,
        noise_seed=-1,
        name=None,
    ):
        """
        Create a realistic simulated image by applying effects to a plain simulated image.

        Parameters
        ----------
        name
        image : ndarray
            The image before simulating (e.g. the lens and source galaxies before optics blurring and Imaging read-out).
        pixel_scale: float
            The scale of each pixel in arc seconds
        exposure_time_map : ndarray
            An array representing the effective exposure time of each pixel.
        psf: PSF
            An array describing the PSF the simulated image is blurred with.
        background_sky_map : ndarray
            The value of background sky in every image pixel (electrons per second).
        add_noise: Bool
            If True poisson noise_maps is simulated and added to the image, based on the total counts in each image
            pixel
        noise_seed: int
            A seed for random noise_maps generation
        """

        if psf is None:
            psf = PSF.from_no_blurring_kernel(pixel_scale=pixel_scale)
            image_needs_trimming = False
        else:
            image_needs_trimming = True

        if exposure_time_map is None:

            exposure_time_map = scaled_array.Scaled.from_single_value_shape_and_pixel_scale(
                value=exposure_time, shape=image.mask.shape, pixel_scale=pixel_scale
            )

        if background_sky_map is None:

            background_sky_map = scaled_array.Scaled.from_single_value_shape_and_pixel_scale(
                value=background_sky_level, shape=image.mask.shape, pixel_scale=pixel_scale
            )

        image += background_sky_map

        image = psf.convolved_scaled_array_from_array_2d_and_mask(array_2d=image.in_2d, mask=image.mask)

        if image_needs_trimming:
            image = image.new_scaled_array_trimmed_from_kernel_shape(kernel_shape=psf.mask.shape)
            exposure_time_map = exposure_time_map.new_scaled_array_trimmed_from_kernel_shape(kernel_shape=psf.mask.shape)
            background_sky_map = background_sky_map.new_scaled_array_trimmed_from_kernel_shape(kernel_shape=psf.mask.shape)

        if add_noise is True:
            noise_realization = generate_poisson_noise(
                image, exposure_time_map, noise_seed
            )
            image += noise_realization
            image_counts = np.multiply(image, exposure_time_map)
            noise_map = np.divide(np.sqrt(image_counts), exposure_time_map)
            noise_map = NoiseMap(sub_array_1d=noise_map, mask=noise_map.mask)
        else:
            noise_map = NoiseMap.from_single_value_shape_and_pixel_scale(
                value=noise_if_add_noise_false,
                shape=image.mask.shape,
                pixel_scale=pixel_scale,
            )
            noise_realization = None

        if np.isnan(noise_map).any():
            raise exc.DataException(
                "The noise-map has NaN values in it. This suggests your exposure time and / or"
                "background sky levels are too low, creating signal counts at or close to 0.0."
            )

        image -= background_sky_map

        # ESTIMATE THE BACKGROUND NOISE MAP FROM THE BACKGROUND SKY MAP

        background_noise_map_counts = np.sqrt(
            np.multiply(background_sky_map, exposure_time_map)
        )
        background_noise_map = np.divide(background_noise_map_counts, exposure_time_map)

        # ESTIMATE THE POISSON NOISE MAP FROM THE IMAGE

        image_counts = np.multiply(image, exposure_time_map)
        poisson_noise_map = np.divide(np.sqrt(np.abs(image_counts)), exposure_time_map)

        image = scaled_array.Scaled(sub_array_1d=image, mask=image.mask)
        background_noise_map = NoiseMap(
            sub_array_1d=background_noise_map, mask=background_noise_map.mask
        )
        poisson_noise_map = PoissonNoiseMap(
            sub_array_1d=poisson_noise_map, mask=poisson_noise_map.mask
        )

        return SimulatedImagingData(
            image=image,
            pixel_scale=pixel_scale,
            psf=psf,
            noise_map=noise_map,
            background_noise_map=background_noise_map,
            poisson_noise_map=poisson_noise_map,
            exposure_time_map=exposure_time_map,
            background_sky_map=background_sky_map,
            noise_realization=noise_realization,
            name=name,
        )

    def __array_finalize__(self, obj):
        if isinstance(obj, SimulatedImagingData):
            try:
                self.image = obj.image
                self.pixel_scale = obj.pixel_scale
                self.psf = obj.psf
                self.noise_map = obj.noise_map
                self.background_noise_map = obj.background_noise_map
                self.poisson_noise_map = obj.poisson_noise_map
                self.exposure_time_map = obj.exposure_time_map
                self.background_sky_map = obj.background_sky_map
                self.background_noise_realization = obj.background_noise_realization
                self.poisson_noise_realization = obj.poisson_noise_realization
                self.origin = obj.origin
            except AttributeError:
                logger.debug(
                    "Original object in Imaging.__array_finalize__ missing one or more attributes"
                )


def setup_random_seed(seed):
    """Setup the random seed. If the input seed is -1, the code will use a random seed for every run. If it is \
    positive, that seed is used for all runs, thereby giving reproducible results.

    Parameters
    ----------
    seed : int
        The seed of the random number generator.
    """
    if seed == -1:
        seed = np.random.randint(
            0, int(1e9)
        )  # Use one seed, so all regions have identical column non-uniformity.
    np.random.seed(seed)


def generate_poisson_noise(image, exposure_time_map, seed=-1):
    """
    Generate a two-dimensional poisson noise_maps-mappers from an image.

    Values are computed from a Poisson distribution using the image's input values in units of counts.

    Parameters
    ----------
    image : ndarray
        The 2D image, whose values in counts are used to draw Poisson noise_maps values.
    exposure_time_map : Union(ndarray, int)
        2D array of the exposure time in each pixel used to convert to / from counts and electrons per second.
    seed : int
        The seed of the random number generator, used for the random noise_maps maps.

    Returns
    -------
    poisson_noise_map: ndarray
        An array describing simulated poisson noise_maps
    """
    setup_random_seed(seed)
    image_counts = np.multiply(image, exposure_time_map)
    return image - np.divide(
        np.random.poisson(image_counts, image.shape), exposure_time_map
    )


def load_imaging_data_from_fits(
    image_path,
    pixel_scale,
    image_hdu=0,
    resized_imaging_shape=None,
    resized_imaging_origin_pixels=None,
    resized_imaging_origin_arcsec=None,
    psf_path=None,
    psf_hdu=0,
    resized_psf_shape=None,
    renormalize_psf=True,
    noise_map_path=None,
    noise_map_hdu=0,
    noise_map_from_image_and_background_noise_map=False,
    convert_noise_map_from_weight_map=False,
    convert_noise_map_from_inverse_noise_map=False,
    background_noise_map_path=None,
    background_noise_map_hdu=0,
    convert_background_noise_map_from_weight_map=False,
    convert_background_noise_map_from_inverse_noise_map=False,
    poisson_noise_map_path=None,
    poisson_noise_map_hdu=0,
    poisson_noise_map_from_image=False,
    convert_poisson_noise_map_from_weight_map=False,
    convert_poisson_noise_map_from_inverse_noise_map=False,
    exposure_time_map_path=None,
    exposure_time_map_hdu=0,
    exposure_time_map_from_single_value=None,
    exposure_time_map_from_inverse_noise_map=False,
    background_sky_map_path=None,
    background_sky_map_hdu=0,
    convert_from_electrons=False,
    gain=None,
    convert_from_adus=False,
    lens_name=None,
):
    """Factory for loading the imaging data_type from .fits files, as well as computing properties like the noise-map,
    exposure-time map, etc. from the imaging-data.

    This factory also includes a number of routines for converting the imaging-data from units not supported by PyAutoLens \
    (e.g. adus, electrons) to electrons per second.

    Parameters
    ----------
    lens_name
    image_path : str
        The path to the image .fits file containing the image (e.g. '/path/to/image.fits')
    pixel_scale : float
        The size of each pixel in arc seconds.
    image_hdu : int
        The hdu the image is contained in the .fits file specified by *image_path*.        
    image_hdu : int
        The hdu the image is contained in the .fits file that *image_path* points too.
    resized_imaging_shape : (int, int) | None
        If input, the imaging arrays that are image sized, e.g. the image, noise-maps) are resized to these dimensions.
    resized_imaging_origin_pixels : (int, int) | None
        If the imaging arrays are resized, this defines a new origin (in pixels) around which recentering occurs.
    resized_imaging_origin_arcsec : (float, float) | None
        If the imaging arrays are resized, this defines a new origin (in arc-seconds) around which recentering occurs.
    psf_path : str
        The path to the psf .fits file containing the psf (e.g. '/path/to/psf.fits')        
    psf_hdu : int
        The hdu the psf is contained in the .fits file specified by *psf_path*.
    resized_psf_shape : (int, int) | None
        If input, the psf is resized to these dimensions.
    renormalize_psf : bool
        If True, the PSF is renoralized such that all elements sum to 1.0.
    noise_map_path : str
        The path to the noise_map .fits file containing the noise_map (e.g. '/path/to/noise_map.fits')        
    noise_map_hdu : int
        The hdu the noise_map is contained in the .fits file specified by *noise_map_path*.
    noise_map_from_image_and_background_noise_map : bool
        If True, the noise-map is computed from the observed image and background noise-map \
        (see NoiseMap.from_image_and_background_noise_map).
    convert_noise_map_from_weight_map : bool
        If True, the noise-map loaded from the .fits file is converted from a weight-map to a noise-map (see \
        *NoiseMap.from_weight_map).
    convert_noise_map_from_inverse_noise_map : bool
        If True, the noise-map loaded from the .fits file is converted from an inverse noise-map to a noise-map (see \
        *NoiseMap.from_inverse_noise_map).
    background_noise_map_path : str
        The path to the background_noise_map .fits file containing the background noise-map \ 
        (e.g. '/path/to/background_noise_map.fits')        
    background_noise_map_hdu : int
        The hdu the background_noise_map is contained in the .fits file specified by *background_noise_map_path*.
    convert_background_noise_map_from_weight_map : bool
        If True, the bacground noise-map loaded from the .fits file is converted from a weight-map to a noise-map (see \
        *NoiseMap.from_weight_map).
    convert_background_noise_map_from_inverse_noise_map : bool
        If True, the background noise-map loaded from the .fits file is converted from an inverse noise-map to a \
        noise-map (see *NoiseMap.from_inverse_noise_map).
    poisson_noise_map_path : str
        The path to the poisson_noise_map .fits file containing the Poisson noise-map \
         (e.g. '/path/to/poisson_noise_map.fits')        
    poisson_noise_map_hdu : int
        The hdu the poisson_noise_map is contained in the .fits file specified by *poisson_noise_map_path*.
    poisson_noise_map_from_image : bool
        If True, the Poisson noise-map is estimated using the image.
    convert_poisson_noise_map_from_weight_map : bool
        If True, the Poisson noise-map loaded from the .fits file is converted from a weight-map to a noise-map (see \
        *NoiseMap.from_weight_map).
    convert_poisson_noise_map_from_inverse_noise_map : bool
        If True, the Poisson noise-map loaded from the .fits file is converted from an inverse noise-map to a \
        noise-map (see *NoiseMap.from_inverse_noise_map).
    exposure_time_map_path : str
        The path to the exposure_time_map .fits file containing the exposure time map \ 
        (e.g. '/path/to/exposure_time_map.fits')        
    exposure_time_map_hdu : int
        The hdu the exposure_time_map is contained in the .fits file specified by *exposure_time_map_path*.
    exposure_time_map_from_single_value : float
        The exposure time of the imaging, which is used to compute the exposure-time map as a single value \
        (see *ExposureTimeMap.from_single_value*).
    exposure_time_map_from_inverse_noise_map : bool
        If True, the exposure-time map is computed from the background noise_map map \
        (see *ExposureTimeMap.from_background_noise_map*)
    background_sky_map_path : str
        The path to the background_sky_map .fits file containing the background sky map \
        (e.g. '/path/to/background_sky_map.fits').
    background_sky_map_hdu : int
        The hdu the background_sky_map is contained in the .fits file specified by *background_sky_map_path*.
    convert_from_electrons : bool
        If True, the input unblurred_image_1d are in units of electrons and all converted to electrons / second using the exposure \
        time map.
    gain : float
        The image gain, used for convert from ADUs.
    convert_from_adus : bool
        If True, the input unblurred_image_1d are in units of adus and all converted to electrons / second using the exposure \
        time map and gain.
    """

    image = abstract_data.load_image(
        image_path=image_path, image_hdu=image_hdu, pixel_scale=pixel_scale
    )

    background_noise_map = load_background_noise_map(
        background_noise_map_path=background_noise_map_path,
        background_noise_map_hdu=background_noise_map_hdu,
        pixel_scale=pixel_scale,
        convert_background_noise_map_from_weight_map=convert_background_noise_map_from_weight_map,
        convert_background_noise_map_from_inverse_noise_map=convert_background_noise_map_from_inverse_noise_map,
    )

    if background_noise_map is not None:
        inverse_noise_map = 1.0 / background_noise_map
    else:
        inverse_noise_map = None

    exposure_time_map = abstract_data.load_exposure_time_map(
        exposure_time_map_path=exposure_time_map_path,
        exposure_time_map_hdu=exposure_time_map_hdu,
        pixel_scale=pixel_scale,
        shape=image.mask.shape,
        exposure_time=exposure_time_map_from_single_value,
        exposure_time_map_from_inverse_noise_map=exposure_time_map_from_inverse_noise_map,
        inverse_noise_map=inverse_noise_map,
    )

    poisson_noise_map = load_poisson_noise_map(
        poisson_noise_map_path=poisson_noise_map_path,
        poisson_noise_map_hdu=poisson_noise_map_hdu,
        pixel_scale=pixel_scale,
        convert_poisson_noise_map_from_weight_map=convert_poisson_noise_map_from_weight_map,
        convert_poisson_noise_map_from_inverse_noise_map=convert_poisson_noise_map_from_inverse_noise_map,
        image=image,
        exposure_time_map=exposure_time_map,
        poisson_noise_map_from_image=poisson_noise_map_from_image,
        convert_from_electrons=convert_from_electrons,
        gain=gain,
        convert_from_adus=convert_from_adus,
    )

    noise_map = load_noise_map(
        noise_map_path=noise_map_path,
        noise_map_hdu=noise_map_hdu,
        pixel_scale=pixel_scale,
        image=image,
        background_noise_map=background_noise_map,
        exposure_time_map=exposure_time_map,
        convert_noise_map_from_weight_map=convert_noise_map_from_weight_map,
        convert_noise_map_from_inverse_noise_map=convert_noise_map_from_inverse_noise_map,
        noise_map_from_image_and_background_noise_map=noise_map_from_image_and_background_noise_map,
        convert_from_electrons=convert_from_electrons,
        gain=gain,
        convert_from_adus=convert_from_adus,
    )

    psf = load_psf(
        psf_path=psf_path,
        psf_hdu=psf_hdu,
        pixel_scale=pixel_scale,
        renormalize=renormalize_psf,
    )

    background_sky_map = load_background_sky_map(
        background_sky_map_path=background_sky_map_path,
        background_sky_map_hdu=background_sky_map_hdu,
        pixel_scale=pixel_scale,
    )

    imaging_data = ImagingData(
        image=image,
        pixel_scale=pixel_scale,
        psf=psf,
        noise_map=noise_map,
        background_noise_map=background_noise_map,
        poisson_noise_map=poisson_noise_map,
        exposure_time_map=exposure_time_map,
        background_sky_map=background_sky_map,
        gain=gain,
        name=lens_name,
    )

    if resized_imaging_shape is not None:
        imaging_data = imaging_data.new_imaging_data_with_resized_arrays(
            new_shape=resized_imaging_shape,
            new_centre_pixels=resized_imaging_origin_pixels,
            new_centre_arcsec=resized_imaging_origin_arcsec,
        )

    if resized_psf_shape is not None:
        imaging_data = imaging_data.new_imaging_data_with_resized_psf(
            new_shape=resized_psf_shape
        )

    if convert_from_electrons:
        imaging_data = imaging_data.new_imaging_data_converted_from_electrons()
    elif convert_from_adus:
        imaging_data = imaging_data.new_imaging_data_converted_from_adus(gain=gain)

    return imaging_data


def load_noise_map(
    noise_map_path,
    noise_map_hdu,
    pixel_scale,
    image=None,
    background_noise_map=None,
    exposure_time_map=None,
    convert_noise_map_from_weight_map=False,
    convert_noise_map_from_inverse_noise_map=False,
    noise_map_from_image_and_background_noise_map=False,
    convert_from_electrons=False,
    gain=None,
    convert_from_adus=False,
):
    """Factory for loading the noise-map from a .fits file.

    This factory also includes a number of routines for converting the noise-map from from other units (e.g. \
    a weight map) or computing the noise-map from other unblurred_image_1d (e.g. the imaging image and background noise-map).

    Parameters
    ----------
    noise_map_path : str
        The path to the noise_map .fits file containing the noise_map (e.g. '/path/to/noise_map.fits')
    noise_map_hdu : int
        The hdu the noise_map is contained in the .fits file specified by *noise_map_path*.
    pixel_scale : float
        The size of each pixel in arc seconds.
    image : ndarray
        The image-image, which the noise-map can be calculated using.
    background_noise_map : ndarray
        The background noise-map, which the noise-map can be calculated using.
    exposure_time_map : ndarray
        The exposure-time map, which the noise-map can be calculated using.
    convert_noise_map_from_weight_map : bool
        If True, the noise-map loaded from the .fits file is converted from a weight-map to a noise-map (see \
        *NoiseMap.from_weight_map).
    convert_noise_map_from_inverse_noise_map : bool
        If True, the noise-map loaded from the .fits file is converted from an inverse noise-map to a noise-map (see \
        *NoiseMap.from_inverse_noise_map).
    background_noise_map_path : str
        The path and filename of the .fits image containing the background noise-map.
    background_noise_map_hdu : int
        The hdu the background noise-map is contained in the .fits file that *background_noise_map_path* points too.
    convert_background_noise_map_from_weight_map : bool
        If True, the bacground noise-map loaded from the .fits file is converted from a weight-map to a noise-map (see \
        *NoiseMap.from_weight_map).
    convert_background_noise_map_from_inverse_noise_map : bool
        If True, the background noise-map loaded from the .fits file is converted from an inverse noise-map to a \
        noise-map (see *NoiseMap.from_inverse_noise_map).
    noise_map_from_image_and_background_noise_map : bool
        If True, the noise-map is computed from the observed image and background noise-map \
        (see NoiseMap.from_image_and_background_noise_map).
    convert_from_electrons : bool
        If True, the input unblurred_image_1d are in units of electrons and all converted to electrons / second using the exposure \
        time map.
    gain : float
        The image gain, used for convert from ADUs.
    convert_from_adus : bool
        If True, the input unblurred_image_1d are in units of adus and all converted to electrons / second using the exposure \
        time map and gain.
    """
    noise_map_options = sum(
        [
            convert_noise_map_from_weight_map,
            convert_noise_map_from_inverse_noise_map,
            noise_map_from_image_and_background_noise_map,
        ]
    )

    if noise_map_options > 1:
        raise exc.DataException(
            "You have specified more than one method to load the noise_map map, e.g.:"
            "convert_noise_map_from_weight_map | "
            "convert_noise_map_from_inverse_noise_map |"
            "noise_map_from_image_and_background_noise_map"
        )

    if noise_map_options == 0 and noise_map_path is not None:
        return NoiseMap.from_fits_with_pixel_scale(
            file_path=noise_map_path, hdu=noise_map_hdu, pixel_scale=pixel_scale
        )
    elif convert_noise_map_from_weight_map and noise_map_path is not None:
        weight_map = scaled_array.Scaled.from_fits_with_pixel_scale(
            file_path=noise_map_path, hdu=noise_map_hdu, pixel_scale=pixel_scale
        )
        return NoiseMap.from_weight_map(weight_map=weight_map, pixel_scale=pixel_scale)
    elif convert_noise_map_from_inverse_noise_map and noise_map_path is not None:
        inverse_noise_map = scaled_array.Scaled.from_fits_with_pixel_scale(
            file_path=noise_map_path, hdu=noise_map_hdu, pixel_scale=pixel_scale
        )
        return NoiseMap.from_inverse_noise_map(
            inverse_noise_map=inverse_noise_map, pixel_scale=pixel_scale
        )
    elif noise_map_from_image_and_background_noise_map:

        if background_noise_map is None:
            raise exc.DataException(
                "Cannot compute the noise-map from the image and background noise_map map if a "
                "background noise_map map is not supplied."
            )

        if (
            not (convert_from_electrons or convert_from_adus)
            and exposure_time_map is None
        ):
            raise exc.DataException(
                "Cannot compute the noise-map from the image and background noise_map map if an "
                "exposure-time (or exposure time map) is not supplied to convert to adus"
            )

        if convert_from_adus and gain is None:
            raise exc.DataException(
                "Cannot compute the noise-map from the image and background noise_map map if a"
                "gain is not supplied to convert from adus"
            )

        return NoiseMap.from_image_and_background_noise_map(
            pixel_scale=pixel_scale,
            image=image,
            background_noise_map=background_noise_map,
            exposure_time_map=exposure_time_map,
            convert_from_electrons=convert_from_electrons,
            gain=gain,
            convert_from_adus=convert_from_adus,
        )
    else:
        raise exc.DataException(
            "A noise_map map was not loaded, specify a noise_map_path or option to compute a noise_map map."
        )


def load_psf(psf_path, psf_hdu, pixel_scale, renormalize=False):
    """Factory for loading the psf from a .fits file.

    Parameters
    ----------
    psf_path : str
        The path to the psf .fits file containing the psf (e.g. '/path/to/psf.fits')
    psf_hdu : int
        The hdu the psf is contained in the .fits file specified by *psf_path*.
    pixel_scale : float
        The size of each pixel in arc seconds.
    renormalize : bool
        If True, the PSF is renoralized such that all elements sum to 1.0.
    """
    if renormalize:
        return PSF.from_fits_renormalized(
            file_path=psf_path, hdu=psf_hdu, pixel_scale=pixel_scale
        )
    if not renormalize:
        return PSF.from_fits_with_scale(
            file_path=psf_path, hdu=psf_hdu, pixel_scale=pixel_scale
        )


def load_background_noise_map(
    background_noise_map_path,
    background_noise_map_hdu,
    pixel_scale,
    convert_background_noise_map_from_weight_map=False,
    convert_background_noise_map_from_inverse_noise_map=False,
):
    """Factory for loading the background noise-map from a .fits file.

    This factory also includes a number of routines for converting the background noise-map from from other units (e.g. \
    a weight map).

    Parameters
    ----------
    background_noise_map_path : str
        The path to the background_noise_map .fits file containing the background noise-map \
        (e.g. '/path/to/background_noise_map.fits')
    background_noise_map_hdu : int
        The hdu the background_noise_map is contained in the .fits file specified by *background_noise_map_path*.
    pixel_scale : float
        The size of each pixel in arc seconds.
    convert_background_noise_map_from_weight_map : bool
        If True, the bacground noise-map loaded from the .fits file is converted from a weight-map to a noise-map (see \
        *NoiseMap.from_weight_map).
    convert_background_noise_map_from_inverse_noise_map : bool
        If True, the background noise-map loaded from the .fits file is converted from an inverse noise-map to a \
        noise-map (see *NoiseMap.from_inverse_noise_map).
    """
    background_noise_map_options = sum(
        [
            convert_background_noise_map_from_weight_map,
            convert_background_noise_map_from_inverse_noise_map,
        ]
    )

    if background_noise_map_options == 0 and background_noise_map_path is not None:
        return NoiseMap.from_fits_with_pixel_scale(
            file_path=background_noise_map_path,
            hdu=background_noise_map_hdu,
            pixel_scale=pixel_scale,
        )
    elif (
        convert_background_noise_map_from_weight_map
        and background_noise_map_path is not None
    ):
        weight_map = scaled_array.Scaled.from_fits_with_pixel_scale(
            file_path=background_noise_map_path, hdu=background_noise_map_hdu, pixel_scale=pixel_scale
        )
        return NoiseMap.from_weight_map(weight_map=weight_map, pixel_scale=pixel_scale)
    elif (
        convert_background_noise_map_from_inverse_noise_map
        and background_noise_map_path is not None
    ):
        inverse_noise_map = scaled_array.Scaled.from_fits_with_pixel_scale(
            file_path=background_noise_map_path, hdu=background_noise_map_hdu, pixel_scale=pixel_scale
        )
        return NoiseMap.from_inverse_noise_map(
            inverse_noise_map=inverse_noise_map, pixel_scale=pixel_scale
        )
    else:
        return None


def load_poisson_noise_map(
    poisson_noise_map_path,
    poisson_noise_map_hdu,
    pixel_scale,
    convert_poisson_noise_map_from_weight_map=False,
    convert_poisson_noise_map_from_inverse_noise_map=False,
    poisson_noise_map_from_image=False,
    image=None,
    exposure_time_map=None,
    convert_from_electrons=False,
    gain=None,
    convert_from_adus=False,
):
    """Factory for loading the Poisson noise-map from a .fits file.

    This factory also includes a number of routines for converting the Poisson noise-map from from other units (e.g. \
    a weight map) or computing the Poisson noise_map from other unblurred_image_1d (e.g. the imaging image).

    Parameters
    ----------
    poisson_noise_map_path : str
        The path to the poisson_noise_map .fits file containing the Poisson noise-map \
         (e.g. '/path/to/poisson_noise_map.fits')
    poisson_noise_map_hdu : int
        The hdu the poisson_noise_map is contained in the .fits file specified by *poisson_noise_map_path*.
    pixel_scale : float
        The size of each pixel in arc seconds.
    convert_poisson_noise_map_from_weight_map : bool
        If True, the Poisson noise-map loaded from the .fits file is converted from a weight-map to a noise-map (see \
        *NoiseMap.from_weight_map).
    convert_poisson_noise_map_from_inverse_noise_map : bool
        If True, the Poisson noise-map loaded from the .fits file is converted from an inverse noise-map to a \
        noise-map (see *NoiseMap.from_inverse_noise_map).
    poisson_noise_map_from_image : bool
        If True, the Poisson noise-map is estimated using the image.
    image : ndarray
        The image, which the Poisson noise-map can be calculated using.
    background_noise_map : ndarray
        The background noise-map, which the Poisson noise-map can be calculated using.
    exposure_time_map : ndarray
        The exposure-time map, which the Poisson noise-map can be calculated using.
    convert_from_electrons : bool
        If True, the input unblurred_image_1d are in units of electrons and all converted to electrons / second using the exposure \
        time map.
    gain : float
        The image gain, used for convert from ADUs.
    convert_from_adus : bool
        If True, the input unblurred_image_1d are in units of adus and all converted to electrons / second using the exposure \
        time map and gain.
    """
    poisson_noise_map_options = sum(
        [
            convert_poisson_noise_map_from_weight_map,
            convert_poisson_noise_map_from_inverse_noise_map,
            poisson_noise_map_from_image,
        ]
    )

    if poisson_noise_map_options == 0 and poisson_noise_map_path is not None:
        return PoissonNoiseMap.from_fits_with_pixel_scale(
            file_path=poisson_noise_map_path,
            hdu=poisson_noise_map_hdu,
            pixel_scale=pixel_scale,
        )
    elif poisson_noise_map_from_image:

        if (
            not (convert_from_electrons or convert_from_adus)
            and exposure_time_map is None
        ):
            raise exc.DataException(
                "Cannot compute the Poisson noise-map from the image if an "
                "exposure-time (or exposure time map) is not supplied to convert to adus"
            )

        if convert_from_adus and gain is None:
            raise exc.DataException(
                "Cannot compute the Poisson noise-map from the image if a"
                "gain is not supplied to convert from adus"
            )

        return PoissonNoiseMap.from_image_and_exposure_time_map(
            pixel_scale=pixel_scale,
            image=image,
            exposure_time_map=exposure_time_map,
            convert_from_electrons=convert_from_electrons,
            gain=gain,
            convert_from_adus=convert_from_adus,
        )

    elif (
        convert_poisson_noise_map_from_weight_map and poisson_noise_map_path is not None
    ):
        weight_map = scaled_array.Scaled.from_fits_with_pixel_scale(
            file_path=poisson_noise_map_path, hdu=poisson_noise_map_hdu, pixel_scale=pixel_scale
        )
        return PoissonNoiseMap.from_weight_map(
            weight_map=weight_map, pixel_scale=pixel_scale
        )
    elif (
        convert_poisson_noise_map_from_inverse_noise_map
        and poisson_noise_map_path is not None
    ):
        inverse_noise_map = scaled_array.Scaled.from_fits_with_pixel_scale(
            file_path=poisson_noise_map_path, hdu=poisson_noise_map_hdu, pixel_scale=pixel_scale
        )
        return PoissonNoiseMap.from_inverse_noise_map(
            inverse_noise_map=inverse_noise_map, pixel_scale=pixel_scale
        )
    else:
        return None


def load_background_sky_map(
    background_sky_map_path, background_sky_map_hdu, pixel_scale
):
    """Factory for loading the background sky from a .fits file.

    Parameters
    ----------
    background_sky_map_path : str
        The path to the background_sky_map .fits file containing the background sky map \
        (e.g. '/path/to/background_sky_map.fits').
    background_sky_map_hdu : int
        The hdu the background_sky_map is contained in the .fits file specified by *background_sky_map_path*.
    pixel_scale : float
        The size of each pixel in arc seconds.
    """
    if background_sky_map_path is not None:
        return scaled_array.Scaled.from_fits_with_pixel_scale(
            file_path=background_sky_map_path,
            hdu=background_sky_map_hdu,
            pixel_scale=pixel_scale,
        )
    else:
        return None


def output_imaging_data_to_fits(
    imaging_data,
    image_path,
    psf_path,
    noise_map_path=None,
    background_noise_map_path=None,
    poisson_noise_map_path=None,
    exposure_time_map_path=None,
    background_sky_map_path=None,
    overwrite=False,
):
    array_util.numpy_array_2d_to_fits(
        array_2d=imaging_data.image.in_2d, file_path=image_path, overwrite=overwrite
    )
    array_util.numpy_array_2d_to_fits(
        array_2d=imaging_data.psf.in_2d, file_path=psf_path, overwrite=overwrite
    )

    if imaging_data.noise_map is not None and noise_map_path is not None:
        array_util.numpy_array_2d_to_fits(
            array_2d=imaging_data.noise_map.in_2d,
            file_path=noise_map_path,
            overwrite=overwrite,
        )

    if (
        imaging_data.background_noise_map is not None
        and background_noise_map_path is not None
    ):
        array_util.numpy_array_2d_to_fits(
            array_2d=imaging_data.background_noise_map.in_2d,
            file_path=background_noise_map_path,
            overwrite=overwrite,
        )

    if (
        imaging_data.poisson_noise_map is not None
        and poisson_noise_map_path is not None
    ):
        array_util.numpy_array_2d_to_fits(
            array_2d=imaging_data.poisson_noise_map.in_2d,
            file_path=poisson_noise_map_path,
            overwrite=overwrite,
        )

    if (
        imaging_data.exposure_time_map is not None
        and exposure_time_map_path is not None
    ):
        array_util.numpy_array_2d_to_fits(
            array_2d=imaging_data.exposure_time_map.in_2d,
            file_path=exposure_time_map_path,
            overwrite=overwrite,
        )

    if (
        imaging_data.background_sky_map is not None
        and background_sky_map_path is not None
    ):
        array_util.numpy_array_2d_to_fits(
            array_2d=imaging_data.background_sky_map.in_2d,
            file_path=background_sky_map_path,
            overwrite=overwrite,
        )
import autofit as af
import autolens as al


import os


def simulator_from_data_resolution(data_resolution, sub_size):
    """Determine the pixel scale from a data_type resolution type based on real observations.

    These options are representative of LSST, Euclid, HST, over-sampled HST and Adaptive Optics image.

    Parameters
    ----------
    data_resolution : str
        A string giving the resolution of the desired data_type type (LSST | Euclid | HST | HST_Up | AO).
    """
    if data_resolution == "sma":
        return al.simulator.interferometer.sma(sub_size=sub_size)
    else:
        raise ValueError(
            "An invalid data_type resolution was entered - ", data_resolution
        )


def simulate_interferometer_from_galaxies_and_output_to_fits(
    data_type, data_resolution, galaxies, sub_size=4
):

    # Simulate the imaging data, remembering that we use a special image which ensures edge-effects don't
    # degrade our modeling of the telescope optics (e.al. the PSF convolution).

    simulator = simulator_from_data_resolution(
        data_resolution=data_resolution, sub_size=sub_size
    )

    # Use the input galaxies to setup a tracer, which will generate the image for the simulated imaging data.
    tracer = al.Tracer.from_galaxies(galaxies=galaxies)

    interferometer = simulator.from_tracer(tracer=tracer)

    # Now, lets output this simulated interferometer-simulator to the test_autoarray/simulator folder.
    test_path = "{}/../../".format(os.path.dirname(os.path.realpath(__file__)))

    dataset_path = af.path_util.make_and_return_path_from_path_and_folder_names(
        path=test_path,
        folder_names=["dataset", "interferometer", data_type, data_resolution],
    )

    interferometer.output_to_fits(
        visibilities_path=dataset_path + "visibilities.fits",
        noise_map_path=dataset_path + "noise_map.fits",
        uv_wavelengths_path=dataset_path + "uv_wavelengths.fits",
        overwrite=True,
    )

    aplt.interferometer.subplot_imaging(
        interferometer=interferometer,
        output_filename="interferometer",
        output_path=dataset_path,
        format="png",
    )

    aplt.interferometer.individual(
        interferometer=interferometer,
        plot_visibilities=True,
        output_path=dataset_path,
        format="png",
    )

    aplt.tracer.subplot_tracer(
        tracer=tracer,
        grid=simulator.grid,
        output_filename="tracer",
        output_path=dataset_path,
        format="png",
    )

    aplt.tracer.individual(
        tracer=tracer,
        grid=simulator.grid,
        plot_profile_image=True,
        plot_source_plane=True,
        plot_convergence=True,
        plot_potential=True,
        plot_deflections=True,
        output_path=dataset_path,
        format="png",
    )


def make_lens_light_dev_vaucouleurs(data_resolutions, sub_size):

    data_type = "lens_light_dev_vaucouleurs"

    # This lens-only system has a Dev Vaucouleurs spheroid / bulge.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllipticalDevVaucouleurs(
            centre=(0.0, 0.0),
            axis_ratio=0.9,
            phi=45.0,
            intensity=0.1,
            effective_radius=1.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_interferometer_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            galaxies=[lens_galaxy, al.Galaxy(redshift=1.0)],
            sub_size=sub_size,
        )


def make_lens_bulge_disk(data_resolutions, sub_size):

    data_type = "lens_bulge_disk"

    # This source-only system has a Dev Vaucouleurs spheroid / bulge and surrounding Exponential envelope

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllipticalDevVaucouleurs(
            centre=(0.0, 0.0),
            axis_ratio=0.9,
            phi=45.0,
            intensity=0.1,
            effective_radius=1.0,
        ),
        envelope=al.lp.EllipticalExponential(
            centre=(0.0, 0.0),
            axis_ratio=0.7,
            phi=60.0,
            intensity=1.0,
            effective_radius=2.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_interferometer_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            galaxies=[lens_galaxy, al.Galaxy(redshift=1.0)],
            sub_size=sub_size,
        )


def make_lens_x2_light(data_resolutions, sub_size):

    data_type = "lens_x2_light"

    # This source-only system has two Sersic bulges separated by 2.0"

    lens_galaxy_0 = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllipticalSersic(
            centre=(-1.0, -1.0),
            axis_ratio=0.8,
            phi=0.0,
            intensity=1.0,
            effective_radius=1.0,
            sersic_index=3.0,
        ),
    )

    lens_galaxy_1 = al.Galaxy(
        redshift=0.5,
        bulge=al.lp.EllipticalSersic(
            centre=(1.0, 1.0),
            axis_ratio=0.8,
            phi=0.0,
            intensity=1.0,
            effective_radius=1.0,
            sersic_index=3.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_interferometer_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            galaxies=[lens_galaxy_0, lens_galaxy_1, al.Galaxy(redshift=1.0)],
            sub_size=sub_size,
        )


def make_lens_sie__source_smooth(data_resolutions, sub_size):

    data_type = "lens_sie__source_smooth"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        mass=al.mp.EllipticalIsothermal(
            centre=(0.0, 0.0), einstein_radius=1.6, axis_ratio=0.7, phi=45.0
        ),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.4,
            effective_radius=0.5,
            sersic_index=1.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_interferometer_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            galaxies=[lens_galaxy, source_galaxy],
            sub_size=sub_size,
        )


def make_lens_sie__source_cuspy(data_resolutions, sub_size):

    data_type = "lens_sie__source_cuspy"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        mass=al.mp.EllipticalIsothermal(
            centre=(0.0, 0.0), einstein_radius=1.6, axis_ratio=0.7, phi=45.0
        ),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.1,
            effective_radius=0.5,
            sersic_index=3.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_interferometer_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            galaxies=[lens_galaxy, source_galaxy],
            sub_size=sub_size,
        )


def make_lens_sis__source_smooth(data_resolutions, sub_size):

    data_type = "lens_sis__source_smooth"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        mass=al.mp.SphericalIsothermal(centre=(0.0, 0.0), einstein_radius=1.6),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.4,
            effective_radius=0.5,
            sersic_index=1.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_interferometer_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            galaxies=[lens_galaxy, source_galaxy],
            sub_size=sub_size,
        )


def make_lens_sie__source_smooth__offset_centre(data_resolutions, sub_size):

    data_type = "lens_sie__source_smooth__offset_centre"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        mass=al.mp.SphericalIsothermal(centre=(2.0, 2.0), einstein_radius=1.2),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(2.0, 2.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.4,
            effective_radius=0.5,
            sersic_index=1.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_interferometer_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            galaxies=[lens_galaxy, source_galaxy],
            sub_size=sub_size,
        )


def make_lens_light__source_smooth(data_resolutions, sub_size):

    data_type = "lens_light__source_smooth"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.9,
            phi=45.0,
            intensity=0.5,
            effective_radius=0.8,
            sersic_index=4.0,
        ),
        mass=al.mp.EllipticalIsothermal(
            centre=(0.0, 0.0), einstein_radius=1.6, axis_ratio=0.7, phi=45.0
        ),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.4,
            effective_radius=0.5,
            sersic_index=1.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_interferometer_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            galaxies=[lens_galaxy, source_galaxy],
            sub_size=sub_size,
        )


def make_lens_light__source_cuspy(data_resolutions, sub_size):

    data_type = "lens_light__source_cuspy"

    # This source-only system has a smooth source (low Sersic Index) and simple SIE mass profile.

    lens_galaxy = al.Galaxy(
        redshift=0.5,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.9,
            phi=45.0,
            intensity=0.5,
            effective_radius=0.8,
            sersic_index=4.0,
        ),
        mass=al.mp.EllipticalIsothermal(
            centre=(0.0, 0.0), einstein_radius=1.6, axis_ratio=0.7, phi=45.0
        ),
    )

    source_galaxy = al.Galaxy(
        redshift=1.0,
        light=al.lp.EllipticalSersic(
            centre=(0.0, 0.0),
            axis_ratio=0.8,
            phi=60.0,
            intensity=0.1,
            effective_radius=0.5,
            sersic_index=3.0,
        ),
    )

    for data_resolution in data_resolutions:

        simulate_interferometer_from_galaxies_and_output_to_fits(
            data_type=data_type,
            data_resolution=data_resolution,
            galaxies=[lens_galaxy, source_galaxy],
            sub_size=sub_size,
        )

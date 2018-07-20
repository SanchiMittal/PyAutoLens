from src import exc
from src.analysis import ray_tracing, galaxy
from src.profiles import mass_profiles, light_profiles
from astropy import cosmology as cosmo
from src.imaging import mask

import pytest
import numpy as np


@pytest.fixture(name="no_galaxies")
def make_no_galaxies():
    return [galaxy.Galaxy()]


@pytest.fixture(name="galaxy_light_sersic")
def make_galaxy_light_sersic():
    sersic = light_profiles.EllipticalSersic(axis_ratio=0.5, phi=0.0, intensity=1.0, effective_radius=0.6,
                                             sersic_index=4.0)
    return galaxy.Galaxy(light_profile=sersic)


@pytest.fixture(name="galaxy_mass_sis")
def make_galaxy_mass_sis():
    sis = mass_profiles.SphericalIsothermal(einstein_radius=1.0)
    return galaxy.Galaxy(mass_profile=sis)


@pytest.fixture(name="all_grids")
def make_all_grids():
    regular_grid = np.array([[1.0, 1.0]])
    sub = np.array([[1.0, 1.0], [1.0, 0.0], [1.0, 1.0], [1.0, 0.0]])
    blurring_grid = np.array([[1.0, 0.0]])

    grid = mask.CoordinateGrid(regular_grid)
    sub = mask.SubCoordinateGrid(sub, None, sub_grid_size=2)
    blurring_grid = mask.CoordinateGrid(blurring_grid)

    all_grids = mask.CoordinateCollection(grid, sub, blurring_grid)

    return all_grids


@pytest.fixture(name="sparse_mask")
def make_sparse_mask():
    return mask.SparseMask(np.array([[0, 0]]), 1)


# @pytest.fixture(name="sparse_mask")
# def make_sparse_mask():
#     return grids.GridMapping(image_shape=(3, 3), image_pixels=1, data_to_image=np.array([[1, 1]]),
#                              sub_size=2, sub_to_image=np.array([0, 0, 0, 0]))

@pytest.fixture(name="sparse_mask")
def make_sparse_mask():
    return None


@pytest.fixture(name="galaxy_light_only")
def make_galaxy_light_only():
    return galaxy.Galaxy(light_profile=light_profiles.EllipticalSersic())


@pytest.fixture(name="galaxy_light_and_mass")
def make_galaxy_light_and_mass():
    return galaxy.Galaxy(light_profile=light_profiles.EllipticalSersic(),
                         mass_profile=mass_profiles.SphericalIsothermal())


@pytest.fixture(name='lens_sis_x3')
def make_lens_sis_x3():
    mass_profile = mass_profiles.SphericalIsothermal(einstein_radius=1.0)
    return galaxy.Galaxy(mass_profile_1=mass_profile, mass_profile_2=mass_profile,
                         mass_profile_3=mass_profile)


class MockMassProfile(object):

    def __init__(self, value):
        self.value = value


class MockMapping(object):

    def __init__(self):
        pass


class MockPixelization(object):

    def __init__(self, value):
        self.value = value

    # noinspection PyUnusedLocal,PyShadowingNames
    def inversion_from_pix_grids(self, grids, sparse_mask):
        return self.value


class TestTracerGeometry(object):

    def test__2_planes__z01_and_z1(self):
        geometry = ray_tracing.TracerGeometry(redshifts=[0.1, 1.0], cosmology=cosmo.Planck15)

        assert geometry.arcsec_per_kpc(plane_i=0) == pytest.approx(0.525060, 1e-5)
        assert geometry.kpc_per_arcsec(plane_i=0) == pytest.approx(1.904544, 1e-5)

        assert geometry.ang_to_earth(plane_i=0) == pytest.approx(392840, 1e-5)
        assert geometry.ang_between_planes(plane_i=0, plane_j=0) == 0.0
        assert geometry.ang_between_planes(plane_i=0, plane_j=1) == pytest.approx(1481890.4, 1e-5)

        assert geometry.arcsec_per_kpc(plane_i=1) == pytest.approx(0.1214785, 1e-5)
        assert geometry.kpc_per_arcsec(plane_i=1) == pytest.approx(8.231907, 1e-5)

        assert geometry.ang_to_earth(plane_i=1) == pytest.approx(1697952, 1e-5)
        assert geometry.ang_between_planes(plane_i=1, plane_j=0) == pytest.approx(-2694346, 1e-5)
        assert geometry.ang_between_planes(plane_i=1, plane_j=1) == 0.0

        assert geometry.critical_density_kpc(plane_i=0, plane_j=1) == pytest.approx(4.85e9, 1e-2)
        assert geometry.critical_density_arcsec(plane_i=0, plane_j=1) == pytest.approx(17593241668, 1e-2)

    def test__3_planes__z01_z1__and_z2(self):
        geometry = ray_tracing.TracerGeometry(redshifts=[0.1, 1.0, 2.0], cosmology=cosmo.Planck15)

        assert geometry.final_plane == 2

        assert geometry.arcsec_per_kpc(plane_i=0) == pytest.approx(0.525060, 1e-5)
        assert geometry.kpc_per_arcsec(plane_i=0) == pytest.approx(1.904544, 1e-5)

        assert geometry.ang_to_earth(plane_i=0) == pytest.approx(392840, 1e-5)
        assert geometry.ang_between_planes(plane_i=0, plane_j=0) == 0.0
        assert geometry.ang_between_planes(plane_i=0, plane_j=1) == pytest.approx(1481890.4, 1e-5)
        assert geometry.ang_between_planes(plane_i=0, plane_j=2) == pytest.approx(1626471, 1e-5)

        assert geometry.arcsec_per_kpc(plane_i=1) == pytest.approx(0.1214785, 1e-5)
        assert geometry.kpc_per_arcsec(plane_i=1) == pytest.approx(8.231907, 1e-5)

        assert geometry.ang_to_earth(plane_i=1) == pytest.approx(1697952, 1e-5)
        assert geometry.ang_between_planes(plane_i=1, plane_j=0) == pytest.approx(-2694346, 1e-5)
        assert geometry.ang_between_planes(plane_i=1, plane_j=1) == 0.0
        assert geometry.ang_between_planes(plane_i=1, plane_j=2) == pytest.approx(638544, 1e-5)

        assert geometry.arcsec_per_kpc(plane_i=2) == pytest.approx(0.116500, 1e-5)
        assert geometry.kpc_per_arcsec(plane_i=2) == pytest.approx(8.58368, 1e-5)

        assert geometry.ang_to_earth(plane_i=2) == pytest.approx(1770512, 1e-5)
        assert geometry.ang_between_planes(plane_i=2, plane_j=0) == pytest.approx(-4435831, 1e-5)
        assert geometry.ang_between_planes(plane_i=2, plane_j=1) == pytest.approx(-957816)
        assert geometry.ang_between_planes(plane_i=2, plane_j=2) == 0.0

        assert geometry.critical_density_kpc(plane_i=0, plane_j=1) == pytest.approx(4.85e9, 1e-2)
        assert geometry.critical_density_arcsec(plane_i=0, plane_j=1) == pytest.approx(17593241668, 1e-2)

    def test__4_planes__z01_z1_z2_and_z3(self):
        geometry = ray_tracing.TracerGeometry(redshifts=[0.1, 1.0, 2.0, 3.0], cosmology=cosmo.Planck15)

        assert geometry.final_plane == 3

        assert geometry.arcsec_per_kpc(plane_i=0) == pytest.approx(0.525060, 1e-5)
        assert geometry.kpc_per_arcsec(plane_i=0) == pytest.approx(1.904544, 1e-5)

        assert geometry.ang_to_earth(plane_i=0) == pytest.approx(392840, 1e-5)
        assert geometry.ang_between_planes(plane_i=0, plane_j=0) == 0.0
        assert geometry.ang_between_planes(plane_i=0, plane_j=1) == pytest.approx(1481890.4, 1e-5)
        assert geometry.ang_between_planes(plane_i=0, plane_j=2) == pytest.approx(1626471, 1e-5)
        assert geometry.ang_between_planes(plane_i=0, plane_j=3) == pytest.approx(1519417, 1e-5)

        assert geometry.arcsec_per_kpc(plane_i=1) == pytest.approx(0.1214785, 1e-5)
        assert geometry.kpc_per_arcsec(plane_i=1) == pytest.approx(8.231907, 1e-5)

        assert geometry.ang_to_earth(plane_i=1) == pytest.approx(1697952, 1e-5)
        assert geometry.ang_between_planes(plane_i=1, plane_j=0) == pytest.approx(-2694346, 1e-5)
        assert geometry.ang_between_planes(plane_i=1, plane_j=1) == 0.0
        assert geometry.ang_between_planes(plane_i=1, plane_j=2) == pytest.approx(638544, 1e-5)
        assert geometry.ang_between_planes(plane_i=1, plane_j=3) == pytest.approx(778472, 1e-5)

        assert geometry.arcsec_per_kpc(plane_i=2) == pytest.approx(0.116500, 1e-5)
        assert geometry.kpc_per_arcsec(plane_i=2) == pytest.approx(8.58368, 1e-5)

        assert geometry.ang_to_earth(plane_i=2) == pytest.approx(1770512, 1e-5)
        assert geometry.ang_between_planes(plane_i=2, plane_j=0) == pytest.approx(-4435831, 1e-5)
        assert geometry.ang_between_planes(plane_i=2, plane_j=1) == pytest.approx(-957816)
        assert geometry.ang_between_planes(plane_i=2, plane_j=2) == 0.0
        assert geometry.ang_between_planes(plane_i=2, plane_j=3) == pytest.approx(299564)

        assert geometry.arcsec_per_kpc(plane_i=3) == pytest.approx(0.12674, 1e-5)
        assert geometry.kpc_per_arcsec(plane_i=3) == pytest.approx(7.89009, 1e-5)

        assert geometry.ang_to_earth(plane_i=3) == pytest.approx(1627448, 1e-5)
        assert geometry.ang_between_planes(plane_i=3, plane_j=0) == pytest.approx(-5525155, 1e-5)
        assert geometry.ang_between_planes(plane_i=3, plane_j=1) == pytest.approx(-1556945, 1e-5)
        assert geometry.ang_between_planes(plane_i=3, plane_j=2) == pytest.approx(-399419, 1e-5)
        assert geometry.ang_between_planes(plane_i=3, plane_j=3) == 0.0

        assert geometry.critical_density_kpc(plane_i=0, plane_j=1) == pytest.approx(4.85e9, 1e-2)
        assert geometry.critical_density_arcsec(plane_i=0, plane_j=1) == pytest.approx(17593241668, 1e-2)

    def test__scaling_factors__3_planes__z01_z1_and_z2(self):
        geometry = ray_tracing.TracerGeometry(redshifts=[0.1, 1.0, 2.0], cosmology=cosmo.Planck15)

        assert geometry.scaling_factor(plane_i=0, plane_j=1) == pytest.approx(0.9500, 1e-4)
        assert geometry.scaling_factor(plane_i=0, plane_j=2) == pytest.approx(1.0, 1e-4)
        assert geometry.scaling_factor(plane_i=1, plane_j=2) == pytest.approx(1.0, 1e-4)

    def test__scaling_factors__4_planes__z01_z1_z2_and_z3(self):
        geometry = ray_tracing.TracerGeometry(redshifts=[0.1, 1.0, 2.0, 3.0], cosmology=cosmo.Planck15)

        assert geometry.scaling_factor(plane_i=0, plane_j=1) == pytest.approx(0.9348, 1e-4)
        assert geometry.scaling_factor(plane_i=0, plane_j=2) == pytest.approx(0.984, 1e-4)
        assert geometry.scaling_factor(plane_i=0, plane_j=3) == pytest.approx(1.0, 1e-4)
        assert geometry.scaling_factor(plane_i=1, plane_j=2) == pytest.approx(0.754, 1e-4)
        assert geometry.scaling_factor(plane_i=1, plane_j=3) == pytest.approx(1.0, 1e-4)
        assert geometry.scaling_factor(plane_i=2, plane_j=3) == pytest.approx(1.0, 1e-4)


class TestTracer(object):
    class TestSetup:

        def test__image_grid__no_galaxy__image_and_source_planes_setup__same_coordinates(self, all_grids, no_galaxies):
            ray_trace = ray_tracing.Tracer(lens_galaxies=no_galaxies, source_galaxies=no_galaxies,
                                           image_plane_grids=all_grids)

            assert ray_trace.image_plane.coordinates_collection.image[0] == pytest.approx(np.array([1.0, 1.0]),
                                                                                          1e-3)
            assert ray_trace.image_plane.deflections.image[0] == pytest.approx(np.array([0.0, 0.0]), 1e-3)
            assert ray_trace.source_plane.coordinates_collection.image[0] == pytest.approx(np.array([1.0, 1.0]),
                                                                                           1e-3)

        def test__image_grid__sis_lens__image_coordinates_are_grid_and_source_plane_is_deflected(self, all_grids,
                                                                                                 galaxy_mass_sis):
            ray_trace = ray_tracing.Tracer(lens_galaxies=[galaxy_mass_sis], source_galaxies=galaxy_mass_sis,
                                           image_plane_grids=all_grids)

            assert ray_trace.image_plane.coordinates_collection.image == pytest.approx(np.array([[1.0, 1.0]]),
                                                                                       1e-3)
            assert ray_trace.image_plane.deflections.image[0] == pytest.approx(np.array([0.707, 0.707]),
                                                                                          1e-3)
            assert ray_trace.source_plane.coordinates_collection.image == pytest.approx(
                np.array([[1.0 - 0.707, 1.0 - 0.707]]), 1e-3)

        def test__image_grid__2_sis_lenses__same_as_above_but_deflections_double(self, all_grids, galaxy_mass_sis):
            ray_trace = ray_tracing.Tracer(lens_galaxies=[galaxy_mass_sis, galaxy_mass_sis],
                                           source_galaxies=galaxy_mass_sis,
                                           image_plane_grids=all_grids)

            assert ray_trace.image_plane.coordinates_collection.image == pytest.approx(np.array([[1.0, 1.0]]),
                                                                                       1e-3)
            assert ray_trace.image_plane.deflections.image[0] == pytest.approx(np.array([1.414, 1.414]),
                                                                                          1e-3)
            assert ray_trace.source_plane.coordinates_collection.image == pytest.approx(
                np.array([[1.0 - 1.414, 1.0 - 1.414]]), 1e-3)

        def test__all_grids__sis_lens__planes_setup_correctly(self, all_grids, galaxy_mass_sis):
            ray_trace = ray_tracing.Tracer(lens_galaxies=[galaxy_mass_sis], source_galaxies=galaxy_mass_sis,
                                           image_plane_grids=all_grids)

            assert ray_trace.image_plane.coordinates_collection.image[0] == pytest.approx(np.array([1.0, 1.0]),
                                                                                          1e-3)
            assert ray_trace.image_plane.coordinates_collection.sub[0] == pytest.approx(
                np.array([1.0, 1.0]), 1e-3)
            assert ray_trace.image_plane.coordinates_collection.sub[1] == pytest.approx(
                np.array([1.0, 0.0]), 1e-3)
            assert ray_trace.image_plane.coordinates_collection.sub[2] == pytest.approx(
                np.array([1.0, 1.0]), 1e-3)
            assert ray_trace.image_plane.coordinates_collection.sub[3] == pytest.approx(
                np.array([1.0, 0.0]), 1e-3)
            assert ray_trace.image_plane.coordinates_collection.blurring[0] == pytest.approx(
                np.array([1.0, 0.0]), 1e-3)

            assert ray_trace.image_plane.deflections.image[0] == pytest.approx(np.array([0.707, 0.707]),
                                                                                          1e-3)
            assert ray_trace.image_plane.deflections.sub[0] == pytest.approx(np.array([0.707, 0.707]), 1e-3)
            assert ray_trace.image_plane.deflections.sub[1] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
            assert ray_trace.image_plane.deflections.sub[2] == pytest.approx(np.array([0.707, 0.707]), 1e-3)
            assert ray_trace.image_plane.deflections.sub[3] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
            assert ray_trace.image_plane.deflections.blurring[0] == pytest.approx(np.array([1.0, 0.0]), 1e-3)

            assert ray_trace.source_plane.coordinates_collection.image[0] == pytest.approx(
                np.array([1.0 - 0.707, 1.0 - 0.707]),
                1e-3)
            assert ray_trace.source_plane.coordinates_collection.sub[0] == pytest.approx(
                np.array([1.0 - 0.707, 1.0 - 0.707]), 1e-3)
            assert ray_trace.source_plane.coordinates_collection.sub[1] == pytest.approx(
                np.array([0.0, 0.0]), 1e-3)
            assert ray_trace.source_plane.coordinates_collection.sub[2] == pytest.approx(
                np.array([1.0 - 0.707, 1.0 - 0.707]), 1e-3)
            assert ray_trace.source_plane.coordinates_collection.sub[3] == pytest.approx(
                np.array([0.0, 0.0]), 1e-3)
            assert ray_trace.source_plane.coordinates_collection.blurring[0] == pytest.approx(
                np.array([0.0, 0.0]), 1e-3)

    class TestImageFromGalaxies:

        def test__no_galaxies__image_is_sum_of_image_plane_and_source_plane_images(self, all_grids,
                                                                                   no_galaxies):
            image_plane = ray_tracing.Plane(galaxies=no_galaxies, coordinates_collection=all_grids,
                                            compute_deflections=True)
            source_plane = ray_tracing.Plane(galaxies=no_galaxies, coordinates_collection=all_grids,
                                             compute_deflections=False)
            plane_image = image_plane.generate_image_of_galaxy_light_profiles(
            ) + source_plane.generate_image_of_galaxy_light_profiles()

            ray_trace = ray_tracing.Tracer(lens_galaxies=no_galaxies, source_galaxies=no_galaxies,
                                           image_plane_grids=all_grids)
            ray_trace_image = ray_trace.generate_image_of_galaxy_light_profiles()

            assert (plane_image == ray_trace_image).all()

        def test__galaxy_light_sersic_no_mass__image_is_sum_of_image_plane_and_source_plane_images(self, all_grids,
                                                                                                   galaxy_light_only):
            image_plane = ray_tracing.Plane(galaxies=[galaxy_light_only], coordinates_collection=all_grids,
                                            compute_deflections=True)
            source_plane = ray_tracing.Plane(galaxies=[galaxy_light_only], coordinates_collection=all_grids,
                                             compute_deflections=False)
            plane_image = image_plane.generate_image_of_galaxy_light_profiles(
            ) + source_plane.generate_image_of_galaxy_light_profiles()

            ray_trace = ray_tracing.Tracer(lens_galaxies=[galaxy_light_only],
                                           source_galaxies=[galaxy_light_only], image_plane_grids=all_grids)
            ray_trace_image = ray_trace.generate_image_of_galaxy_light_profiles()

            assert (plane_image == ray_trace_image).all()

        def test__galaxy_light_sersic_mass_sis__source_plane_image_includes_deflections(self, all_grids,
                                                                                        galaxy_light_and_mass):
            image_plane = ray_tracing.Plane(galaxies=[galaxy_light_and_mass], coordinates_collection=all_grids,
                                            compute_deflections=True)
            deflections_grid = ray_tracing.deflections_for_coordinates_collection(all_grids,
                                                                                  galaxies=[galaxy_light_and_mass])
            source_grid = ray_tracing.traced_collection_for_deflections(all_grids, deflections_grid)
            source_plane = ray_tracing.Plane(galaxies=[galaxy_light_and_mass], coordinates_collection=source_grid,
                                             compute_deflections=False)
            plane_image = image_plane.generate_image_of_galaxy_light_profiles(
            ) + source_plane.generate_image_of_galaxy_light_profiles()

            ray_trace = ray_tracing.Tracer(lens_galaxies=[galaxy_light_and_mass],
                                           source_galaxies=[galaxy_light_and_mass],
                                           image_plane_grids=all_grids)
            ray_trace_image = ray_trace.generate_image_of_galaxy_light_profiles()

            assert (plane_image == ray_trace_image).all()

    class TestBlurringImageFromGalaxies:

        def test__no_galaxies__image_is_sum_of_image_plane_and_source_plane_images(self, all_grids, no_galaxies):
            image_plane = ray_tracing.Plane(galaxies=no_galaxies, coordinates_collection=all_grids,
                                            compute_deflections=True)
            source_plane = ray_tracing.Plane(galaxies=no_galaxies, coordinates_collection=all_grids,
                                             compute_deflections=False)
            plane_image = image_plane.generate_blurring_image_of_galaxy_light_profiles(

            ) + source_plane.generate_blurring_image_of_galaxy_light_profiles()

            ray_trace = ray_tracing.Tracer(lens_galaxies=no_galaxies, source_galaxies=no_galaxies,
                                           image_plane_grids=all_grids)
            ray_trace_image = ray_trace.generate_blurring_image_of_galaxy_light_profiles()

            assert (plane_image == ray_trace_image).all()

        def test__galaxy_light_sersic_no_mass__image_is_sum_of_image_plane_and_source_plane_images(self, all_grids,
                                                                                                   galaxy_light_only):
            image_plane = ray_tracing.Plane(galaxies=[galaxy_light_only], coordinates_collection=all_grids,
                                            compute_deflections=True)
            source_plane = ray_tracing.Plane(galaxies=[galaxy_light_only], coordinates_collection=all_grids,
                                             compute_deflections=False)
            plane_image = image_plane.generate_blurring_image_of_galaxy_light_profiles(
            ) + source_plane.generate_blurring_image_of_galaxy_light_profiles()

            ray_trace = ray_tracing.Tracer(lens_galaxies=[galaxy_light_only],
                                           source_galaxies=[galaxy_light_only],
                                           image_plane_grids=all_grids)
            ray_trace_image = ray_trace.generate_blurring_image_of_galaxy_light_profiles()

            assert (plane_image == ray_trace_image).all()

        def test__galaxy_light_sersic_mass_sis__source_plane_image_includes_deflections(self, all_grids,
                                                                                        galaxy_light_and_mass):
            image_plane = ray_tracing.Plane(galaxies=[galaxy_light_and_mass], coordinates_collection=all_grids,
                                            compute_deflections=True)
            deflections_grid = ray_tracing.deflections_for_coordinates_collection(all_grids,
                                                                                  galaxies=[galaxy_light_and_mass])
            source_grid = ray_tracing.traced_collection_for_deflections(all_grids, deflections_grid)
            source_plane = ray_tracing.Plane(galaxies=[galaxy_light_and_mass], coordinates_collection=source_grid,
                                             compute_deflections=False)
            plane_image = image_plane.generate_blurring_image_of_galaxy_light_profiles(
            ) + source_plane.generate_blurring_image_of_galaxy_light_profiles()

            ray_trace = ray_tracing.Tracer(lens_galaxies=[galaxy_light_and_mass],
                                           source_galaxies=[galaxy_light_and_mass],
                                           image_plane_grids=all_grids)
            ray_trace_image = ray_trace.generate_blurring_image_of_galaxy_light_profiles()

            assert (plane_image == ray_trace_image).all()

    class TestPixelizationFromGalaxy:

        def test__no_galaxies_in_plane__returns_none(self, all_grids, sparse_mask):
            galaxy_no_pix = galaxy.Galaxy()

            tracing = ray_tracing.Tracer(lens_galaxies=[], source_galaxies=[galaxy_no_pix], image_plane_grids=all_grids)

            pix_matrix = tracing.generate_pixelization_matrices_of_source_galaxy(sparse_mask)

            assert pix_matrix is None

        def test__image_galaxy_has_pixelization__still_returns_none(self, all_grids, sparse_mask):
            galaxy_pix = galaxy.Galaxy(pixelization=MockPixelization(value=1))
            galaxy_no_pix = galaxy.Galaxy()

            tracing = ray_tracing.Tracer(lens_galaxies=[galaxy_pix], source_galaxies=[galaxy_no_pix],
                                         image_plane_grids=all_grids)

            pix_matrix = tracing.generate_pixelization_matrices_of_source_galaxy(sparse_mask)

            assert pix_matrix is None

        def test__source_galaxy_has_pixelization__returns_pixelization_matrix(self, all_grids, sparse_mask):
            galaxy_pix = galaxy.Galaxy(pixelization=MockPixelization(value=1))
            galaxy_no_pix = galaxy.Galaxy()

            tracing = ray_tracing.Tracer(lens_galaxies=[galaxy_no_pix], source_galaxies=[galaxy_pix],
                                         image_plane_grids=all_grids)

            pix_matrix = tracing.generate_pixelization_matrices_of_source_galaxy(sparse_mask)

            assert pix_matrix == 1


class TestMultiTracer(object):
    class TestGalaxyOrder:

        def test__3_galaxies_reordered_in_ascending_redshift(self, all_grids):
            tracer = ray_tracing.MultiTracer(galaxies=[galaxy.Galaxy(redshift=2.0), galaxy.Galaxy(redshift=1.0),
                                                       galaxy.Galaxy(redshift=0.1)], image_plane_grids=all_grids,
                                             cosmology=cosmo.Planck15)

            assert tracer.galaxies_redshift_order[0].redshift == 0.1
            assert tracer.galaxies_redshift_order[1].redshift == 1.0
            assert tracer.galaxies_redshift_order[2].redshift == 2.0

        def test__3_galaxies_two_same_redshift__planes_redshift_order_is_size_2_with_those_redshifts(self, all_grids):
            tracer = ray_tracing.MultiTracer(galaxies=[galaxy.Galaxy(redshift=1.0), galaxy.Galaxy(redshift=1.0),
                                                       galaxy.Galaxy(redshift=0.1)], image_plane_grids=all_grids,
                                             cosmology=cosmo.Planck15)

            assert tracer.galaxies_redshift_order[0].redshift == 0.1
            assert tracer.galaxies_redshift_order[1].redshift == 1.0
            assert tracer.galaxies_redshift_order[2].redshift == 1.0

            assert tracer.planes_redshift_order[0] == 0.1
            assert tracer.planes_redshift_order[1] == 1.0

        def test__6_galaxies_producing_4_planes(self, all_grids):
            g0 = galaxy.Galaxy(redshift=1.0)
            g1 = galaxy.Galaxy(redshift=1.0)
            g2 = galaxy.Galaxy(redshift=0.1)
            g3 = galaxy.Galaxy(redshift=1.05)
            g4 = galaxy.Galaxy(redshift=0.95)
            g5 = galaxy.Galaxy(redshift=1.05)

            tracer = ray_tracing.MultiTracer(galaxies=[g0, g1, g2, g3, g4, g5],
                                             image_plane_grids=all_grids, cosmology=cosmo.Planck15)

            assert tracer.galaxies_redshift_order[0].redshift == 0.1
            assert tracer.galaxies_redshift_order[1].redshift == 0.95
            assert tracer.galaxies_redshift_order[2].redshift == 1.0
            assert tracer.galaxies_redshift_order[3].redshift == 1.0
            assert tracer.galaxies_redshift_order[4].redshift == 1.05
            assert tracer.galaxies_redshift_order[5].redshift == 1.05

            assert tracer.planes_redshift_order[0] == 0.1
            assert tracer.planes_redshift_order[1] == 0.95
            assert tracer.planes_redshift_order[2] == 1.0
            assert tracer.planes_redshift_order[3] == 1.05

        def test__6_galaxies__plane_galaxies_are_correct(self, all_grids):
            g0 = galaxy.Galaxy(redshift=1.0)
            g1 = galaxy.Galaxy(redshift=1.0)
            g2 = galaxy.Galaxy(redshift=0.1)
            g3 = galaxy.Galaxy(redshift=1.05)
            g4 = galaxy.Galaxy(redshift=0.95)
            g5 = galaxy.Galaxy(redshift=1.05)

            tracer = ray_tracing.MultiTracer(galaxies=[g0, g1, g2, g3, g4, g5],
                                             image_plane_grids=all_grids, cosmology=cosmo.Planck15)

            assert tracer.planes_galaxies[0] == [g2]
            assert tracer.planes_galaxies[1] == [g4]
            assert tracer.planes_galaxies[2] == [g0, g1]
            assert tracer.planes_galaxies[3] == [g3, g5]

    class TestRayTracingPlanes:

        def test__6_galaxies__tracer_planes_are_correct(self, all_grids):
            g0 = galaxy.Galaxy(redshift=2.0)
            g1 = galaxy.Galaxy(redshift=2.0)
            g2 = galaxy.Galaxy(redshift=0.1)
            g3 = galaxy.Galaxy(redshift=3.0)
            g4 = galaxy.Galaxy(redshift=1.0)
            g5 = galaxy.Galaxy(redshift=3.0)

            tracer = ray_tracing.MultiTracer(galaxies=[g0, g1, g2, g3, g4, g5],
                                             image_plane_grids=all_grids, cosmology=cosmo.Planck15)

            assert tracer.planes[0].galaxies == [g2]
            assert tracer.planes[1].galaxies == [g4]
            assert tracer.planes[2].galaxies == [g0, g1]
            assert tracer.planes[3].galaxies == [g3, g5]

        def test__multiplane_4_planes__coordinate_grids_and_deflections_are_correct__sis_mass_profile(self, all_grids):
            import math

            g0 = galaxy.Galaxy(redshift=2.0, mass_profile=mass_profiles.SphericalIsothermal(einstein_radius=1.0))
            g1 = galaxy.Galaxy(redshift=2.0, mass_profile=mass_profiles.SphericalIsothermal(einstein_radius=1.0))
            g2 = galaxy.Galaxy(redshift=0.1, mass_profile=mass_profiles.SphericalIsothermal(einstein_radius=1.0))
            g3 = galaxy.Galaxy(redshift=3.0, mass_profile=mass_profiles.SphericalIsothermal(einstein_radius=1.0))
            g4 = galaxy.Galaxy(redshift=1.0, mass_profile=mass_profiles.SphericalIsothermal(einstein_radius=1.0))
            g5 = galaxy.Galaxy(redshift=3.0, mass_profile=mass_profiles.SphericalIsothermal(einstein_radius=1.0))

            tracer = ray_tracing.MultiTracer(galaxies=[g0, g1, g2, g3, g4, g5],
                                             image_plane_grids=all_grids, cosmology=cosmo.Planck15)

            # From unit test below:
            # Beta_01 = 0.9348
            # Beta_02 = 0.9840
            # Beta_03 = 1.0
            # Beta_12 = 0.754
            # Beta_13 = 1.0
            # Beta_23 = 1.0

            val = math.sqrt(2) / 2.0

            assert tracer.planes[0].coordinates_collection.image[0] == pytest.approx(np.array([1.0, 1.0]), 1e-4)
            assert tracer.planes[0].coordinates_collection.sub[0] == pytest.approx(np.array([1.0, 1.0]),
                                                                                   1e-4)
            assert tracer.planes[0].coordinates_collection.sub[1] == pytest.approx(np.array([1.0, 0.0]),
                                                                                   1e-4)
            assert tracer.planes[0].coordinates_collection.blurring[0] == pytest.approx(np.array([1.0, 0.0]),
                                                                                        1e-4)
            assert tracer.planes[0].deflections.image[0] == pytest.approx(np.array([val, val]), 1e-4)
            assert tracer.planes[0].deflections.sub[0] == pytest.approx(np.array([val, val]), 1e-4)
            assert tracer.planes[0].deflections.sub[1] == pytest.approx(np.array([1.0, 0.0]), 1e-4)
            assert tracer.planes[0].deflections.blurring[0] == pytest.approx(np.array([1.0, 0.0]), 1e-4)

            assert tracer.planes[1].coordinates_collection.image[0] == pytest.approx(
                np.array([(1.0 - 0.9348 * val), (1.0 - 0.9348 * val)]), 1e-4)
            assert tracer.planes[1].coordinates_collection.sub[0] == pytest.approx(
                np.array([(1.0 - 0.9348 * val), (1.0 - 0.9348 * val)]), 1e-4)
            assert tracer.planes[1].coordinates_collection.sub[1] == pytest.approx(
                np.array([(1.0 - 0.9348 * 1.0), 0.0]), 1e-4)
            assert tracer.planes[1].coordinates_collection.blurring[0] == pytest.approx(
                np.array([(1.0 - 0.9348 * 1.0), 0.0]), 1e-4)

            defl11 = g0.deflections_from_coordinate_grid(grid=np.array([[(1.0 - 0.9348 * val), (1.0 - 0.9348 * val)]]))
            defl12 = g0.deflections_from_coordinate_grid(grid=np.array([[(1.0 - 0.9348 * 1.0), 0.0]]))

            assert tracer.planes[1].deflections.image[0] == pytest.approx(defl11[0], 1e-4)
            assert tracer.planes[1].deflections.sub[0] == pytest.approx(defl11[0], 1e-4)
            assert tracer.planes[1].deflections.sub[1] == pytest.approx(defl12[0], 1e-4)
            assert tracer.planes[1].deflections.blurring[0] == pytest.approx(defl12[0], 1e-4)

            assert tracer.planes[2].coordinates_collection.image[0] == pytest.approx(
                np.array([(1.0 - 0.9839601 * val - 0.7539734 * defl11[0, 0]),
                          (1.0 - 0.9839601 * val - 0.7539734 * defl11[0, 1])]), 1e-4)
            assert tracer.planes[2].coordinates_collection.sub[0] == pytest.approx(
                np.array([(1.0 - 0.9839601 * val - 0.7539734 * defl11[0, 0]),
                          (1.0 - 0.9839601 * val - 0.7539734 * defl11[0, 1])]), 1e-4)
            assert tracer.planes[2].coordinates_collection.sub[1] == pytest.approx(
                np.array([(1.0 - 0.9839601 * 1.0 - 0.7539734 * defl12[0, 0]),
                          0.0]), 1e-4)
            assert tracer.planes[2].coordinates_collection.blurring[0] == pytest.approx(
                np.array([(1.0 - 0.9839601 * 1.0 - 0.7539734 * defl12[0, 0]),
                          0.0]), 1e-4)

            # 2 Galaxies in this plane, so multiply by 2.0

            defl21 = 2.0 * g0.deflections_from_coordinate_grid(
                grid=np.array([[(1.0 - 0.9839601 * val - 0.7539734 * defl11[0, 0]),
                                (1.0 - 0.9839601 * val - 0.7539734 * defl11[0, 1])]]))
            defl22 = 2.0 * g0.deflections_from_coordinate_grid(
                grid=np.array([[(1.0 - 0.9839601 * 1.0 - 0.7539734 * defl12[0, 0]),
                                0.0]]))

            assert tracer.planes[2].deflections.image[0] == pytest.approx(defl21[0], 1e-4)
            assert tracer.planes[2].deflections.sub[0] == pytest.approx(defl21[0], 1e-4)
            assert tracer.planes[2].deflections.sub[1] == pytest.approx(defl22[0], 1e-4)
            assert tracer.planes[2].deflections.blurring[0] == pytest.approx(defl22[0], 1e-4)

            coord1 = (1.0 - tracer.planes[0].deflections.image[0, 0] -
                      tracer.planes[1].deflections.image[
                          0, 0] -
                      tracer.planes[2].deflections.image[0, 0])

            coord2 = (1.0 - tracer.planes[0].deflections.image[0, 1] -
                      tracer.planes[1].deflections.image[
                          0, 1] -
                      tracer.planes[2].deflections.image[0, 1])

            coord3 = (1.0 - tracer.planes[0].deflections.sub[1, 0] -
                      tracer.planes[1].deflections.sub[1, 0] -
                      tracer.planes[2].deflections.sub[1, 0])

            assert tracer.planes[3].coordinates_collection.image[0] == pytest.approx(np.array([coord1, coord2]),
                                                                                     1e-4)
            assert tracer.planes[3].coordinates_collection.sub[0] == pytest.approx(
                np.array([coord1, coord2]), 1e-4)
            assert tracer.planes[3].coordinates_collection.sub[1] == pytest.approx(np.array([coord3, 0.0]),
                                                                                   1e-4)
            assert tracer.planes[3].coordinates_collection.blurring[0] == pytest.approx(np.array([coord3, 0.0]),
                                                                                        1e-4)

    class TestImageFromGalaxies:

        def test__galaxy_light_sersic_no_mass__image_sum_of_all_3_planes(self, all_grids):
            sersic = light_profiles.EllipticalSersic(axis_ratio=0.5, phi=0.0, intensity=1.0, effective_radius=0.6,
                                                     sersic_index=4.0)

            g0 = galaxy.Galaxy(redshift=0.1, light_profile=sersic)
            g1 = galaxy.Galaxy(redshift=1.0, light_profile=sersic)
            g2 = galaxy.Galaxy(redshift=2.0, light_profile=sersic)

            ray_trace = ray_tracing.MultiTracer(galaxies=[g0, g1, g2], image_plane_grids=all_grids,
                                                cosmology=cosmo.Planck15)
            ray_trace_image = ray_trace.generate_image_of_galaxy_light_profiles()

            plane_0 = ray_tracing.Plane(galaxies=[g0], coordinates_collection=all_grids, compute_deflections=True)
            plane_1 = ray_tracing.Plane(galaxies=[g1], coordinates_collection=all_grids, compute_deflections=True)
            plane_2 = ray_tracing.Plane(galaxies=[g2], coordinates_collection=all_grids, compute_deflections=False)

            plane_image = (plane_0.generate_image_of_galaxy_light_profiles() +
                           plane_1.generate_image_of_galaxy_light_profiles() +
                           plane_2.generate_image_of_galaxy_light_profiles())

            assert (plane_image == ray_trace_image).all()

        def test__galaxy_light_sersic_mass_sis__source_plane_image_includes_deflections(self, all_grids):
            sersic = light_profiles.EllipticalSersic(axis_ratio=0.5, phi=0.0, intensity=1.0, effective_radius=0.6,
                                                     sersic_index=4.0)

            sis = mass_profiles.SphericalIsothermal(einstein_radius=1.0)

            g0 = galaxy.Galaxy(redshift=0.1, light_profile=sersic, mass_profile=sis)
            g1 = galaxy.Galaxy(redshift=1.0, light_profile=sersic, mass_profile=sis)
            g2 = galaxy.Galaxy(redshift=2.0, light_profile=sersic, mass_profile=sis)

            ray_trace = ray_tracing.MultiTracer(galaxies=[g0, g1, g2], image_plane_grids=all_grids,
                                                cosmology=cosmo.Planck15)
            ray_trace_image = ray_trace.generate_image_of_galaxy_light_profiles()

            plane_0 = ray_trace.planes[0]
            plane_1 = ray_trace.planes[1]
            plane_2 = ray_trace.planes[2]

            plane_image = (plane_0.generate_image_of_galaxy_light_profiles() +
                           plane_1.generate_image_of_galaxy_light_profiles() +
                           plane_2.generate_image_of_galaxy_light_profiles())

            assert (plane_image == ray_trace_image).all()

    class TestBlurringImageFromGalaxies:

        def test__galaxy_light_sersic_no_mass__image_sum_of_all_3_planes(self, all_grids):
            sersic = light_profiles.EllipticalSersic(axis_ratio=0.5, phi=0.0, intensity=1.0, effective_radius=0.6,
                                                     sersic_index=4.0)

            g0 = galaxy.Galaxy(redshift=0.1, light_profile=sersic)
            g1 = galaxy.Galaxy(redshift=1.0, light_profile=sersic)
            g2 = galaxy.Galaxy(redshift=2.0, light_profile=sersic)

            ray_trace = ray_tracing.MultiTracer(galaxies=[g0, g1, g2], image_plane_grids=all_grids,
                                                cosmology=cosmo.Planck15)
            ray_trace_image = ray_trace.generate_blurring_image_of_galaxy_light_profiles()

            plane_0 = ray_tracing.Plane(galaxies=[g0], coordinates_collection=all_grids, compute_deflections=True)
            plane_1 = ray_tracing.Plane(galaxies=[g1], coordinates_collection=all_grids, compute_deflections=True)
            plane_2 = ray_tracing.Plane(galaxies=[g2], coordinates_collection=all_grids, compute_deflections=False)

            plane_image = (plane_0.generate_blurring_image_of_galaxy_light_profiles() +
                           plane_1.generate_blurring_image_of_galaxy_light_profiles() +
                           plane_2.generate_blurring_image_of_galaxy_light_profiles())

            assert (plane_image == ray_trace_image).all()

        def test__galaxy_light_sersic_mass_sis__source_plane_image_includes_deflections(self, all_grids):
            sersic = light_profiles.EllipticalSersic(axis_ratio=0.5, phi=0.0, intensity=1.0, effective_radius=0.6,
                                                     sersic_index=4.0)

            sis = mass_profiles.SphericalIsothermal(einstein_radius=1.0)

            g0 = galaxy.Galaxy(redshift=0.1, light_profile=sersic, mass_profile=sis)
            g1 = galaxy.Galaxy(redshift=1.0, light_profile=sersic, mass_profile=sis)
            g2 = galaxy.Galaxy(redshift=2.0, light_profile=sersic, mass_profile=sis)

            ray_trace = ray_tracing.MultiTracer(galaxies=[g0, g1, g2], image_plane_grids=all_grids,
                                                cosmology=cosmo.Planck15)
            ray_trace_image = ray_trace.generate_blurring_image_of_galaxy_light_profiles()

            plane_0 = ray_trace.planes[0]
            plane_1 = ray_trace.planes[1]
            plane_2 = ray_trace.planes[2]

            plane_image = (plane_0.generate_blurring_image_of_galaxy_light_profiles() +
                           plane_1.generate_blurring_image_of_galaxy_light_profiles() +
                           plane_2.generate_blurring_image_of_galaxy_light_profiles())

            assert (plane_image == ray_trace_image).all()

    class TestPixelizationFromGalaxy:

        def test__3_galaxies__non_have_pixelization__returns_none_x3(self, all_grids, sparse_mask):
            sis = mass_profiles.SphericalIsothermal(einstein_radius=1.0)

            g0 = galaxy.Galaxy(redshift=0.1, mass_profile=sis)
            g1 = galaxy.Galaxy(redshift=1.0, mass_profile=sis)
            g2 = galaxy.Galaxy(redshift=2.0, mass_profile=sis)

            tracing = ray_tracing.MultiTracer(galaxies=[g0, g1, g2], image_plane_grids=all_grids,
                                              cosmology=cosmo.Planck15)

            pix_matrix = tracing.generate_pixelization_matrices_of_galaxies(sparse_mask)

            assert pix_matrix == [None, None, None]

        def test__3_galaxies__1_has_pixelization__returns_none_x2_and_pixelization(self, all_grids, sparse_mask):
            sis = mass_profiles.SphericalIsothermal(einstein_radius=1.0)

            g0 = galaxy.Galaxy(redshift=0.1, mass_profile=sis)
            g1 = galaxy.Galaxy(redshift=1.0, pixelization=MockPixelization(value=1), mass_profile=sis)
            g2 = galaxy.Galaxy(redshift=2.0, mass_profile=sis)

            tracing = ray_tracing.MultiTracer(galaxies=[g0, g1, g2], image_plane_grids=all_grids,
                                              cosmology=cosmo.Planck15)

            pix_matrix = tracing.generate_pixelization_matrices_of_galaxies(sparse_mask)

            assert pix_matrix == [None, 1, None]

        def test__3_galaxies__all_have_pixelization__returns_pixelizations(self, all_grids, sparse_mask):
            sis = mass_profiles.SphericalIsothermal(einstein_radius=1.0)

            g0 = galaxy.Galaxy(redshift=0.1, pixelization=MockPixelization(value=0.5), mass_profile=sis)
            g1 = galaxy.Galaxy(redshift=1.0, pixelization=MockPixelization(value=1), mass_profile=sis)
            g2 = galaxy.Galaxy(redshift=2.0, pixelization=MockPixelization(value=2), mass_profile=sis)

            tracing = ray_tracing.MultiTracer(galaxies=[g0, g1, g2], image_plane_grids=all_grids,
                                              cosmology=cosmo.Planck15)

            pix_matrix = tracing.generate_pixelization_matrices_of_galaxies(sparse_mask)

            assert pix_matrix == [0.5, 1, 2]


class TestPlane(object):
    class TestBasicSetup:

        def test__all_grids__sis_lens__coordinates_and_deflections_setup_for_every_grid(self, all_grids,
                                                                                        galaxy_mass_sis):
            plane = ray_tracing.Plane(galaxies=[galaxy_mass_sis], coordinates_collection=all_grids)

            assert plane.coordinates_collection.image[0] == pytest.approx(np.array([1.0, 1.0]), 1e-3)
            assert plane.coordinates_collection.sub[0] == pytest.approx(np.array([1.0, 1.0]), 1e-3)
            assert plane.coordinates_collection.sub[1] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
            assert plane.coordinates_collection.sub[2] == pytest.approx(np.array([1.0, 1.0]), 1e-3)
            assert plane.coordinates_collection.sub[3] == pytest.approx(np.array([1.0, 0.0]), 1e-3)
            assert plane.coordinates_collection.blurring[0] == pytest.approx(np.array([1.0, 0.0]), 1e-3)

        def test__all_grids__3_identical_sis_lenses__deflections_triple_compared_to_above(self, all_grids,
                                                                                          galaxy_mass_sis):
            lens_plane = ray_tracing.Plane(galaxies=[galaxy_mass_sis, galaxy_mass_sis, galaxy_mass_sis],
                                           coordinates_collection=all_grids, compute_deflections=True)

            assert lens_plane.coordinates_collection.image[0] == pytest.approx(np.array([1.0, 1.0]), 1e-5)
            assert lens_plane.coordinates_collection.sub[0] == pytest.approx(np.array([1.0, 1.0]), 1e-5)
            assert lens_plane.coordinates_collection.sub[1] == pytest.approx(np.array([1.0, 0.0]), 1e-5)
            assert lens_plane.coordinates_collection.sub[2] == pytest.approx(np.array([1.0, 1.0]), 1e-5)
            assert lens_plane.coordinates_collection.sub[3] == pytest.approx(np.array([1.0, 0.0]), 1e-5)
            assert lens_plane.coordinates_collection.blurring[0] == pytest.approx(np.array([1.0, 0.0]), 1e-5)

            assert lens_plane.deflections.image[0] == pytest.approx(np.array([3.0 * 0.707, 3.0 * 0.707]),
                                                                               1e-3)
            assert lens_plane.deflections.sub[0] == pytest.approx(np.array([3.0 * 0.707, 3.0 * 0.707]),
                                                                             1e-3)
            assert lens_plane.deflections.sub[1] == pytest.approx(np.array([3.0, 0.0]), 1e-3)
            assert lens_plane.deflections.sub[2] == pytest.approx(np.array([3.0 * 0.707, 3.0 * 0.707]),
                                                                             1e-3)
            assert lens_plane.deflections.sub[3] == pytest.approx(np.array([3.0, 0.0]), 1e-3)
            assert lens_plane.deflections.blurring[0] == pytest.approx(np.array([3.0, 0.0]), 1e-3)

        def test__all_grids__lens_is_3_identical_sis_profiles__deflections_triple_like_above(self, all_grids,
                                                                                             lens_sis_x3):
            lens_plane = ray_tracing.Plane(galaxies=[lens_sis_x3], coordinates_collection=all_grids,
                                           compute_deflections=True)

            assert lens_plane.coordinates_collection.image[0] == pytest.approx(np.array([1.0, 1.0]), 1e-5)
            assert lens_plane.coordinates_collection.sub[0] == pytest.approx(np.array([1.0, 1.0]), 1e-5)
            assert lens_plane.coordinates_collection.sub[1] == pytest.approx(np.array([1.0, 0.0]), 1e-5)
            assert lens_plane.coordinates_collection.sub[2] == pytest.approx(np.array([1.0, 1.0]), 1e-5)
            assert lens_plane.coordinates_collection.sub[3] == pytest.approx(np.array([1.0, 0.0]), 1e-5)
            assert lens_plane.coordinates_collection.blurring[0] == pytest.approx(np.array([1.0, 0.0]), 1e-5)

            assert lens_plane.deflections.image[0] == pytest.approx(np.array([3.0 * 0.707, 3.0 * 0.707]),
                                                                               1e-3)
            assert lens_plane.deflections.sub[0] == pytest.approx(np.array([3.0 * 0.707, 3.0 * 0.707]),
                                                                             1e-3)
            assert lens_plane.deflections.sub[1] == pytest.approx(np.array([3.0, 0.0]), 1e-3)
            assert lens_plane.deflections.sub[2] == pytest.approx(np.array([3.0 * 0.707, 3.0 * 0.707]),
                                                                             1e-3)
            assert lens_plane.deflections.sub[3] == pytest.approx(np.array([3.0, 0.0]), 1e-3)
            assert lens_plane.deflections.blurring[0] == pytest.approx(np.array([3.0, 0.0]), 1e-3)

        # TODO : Commented out until quad works in deflections

        # def test__all_grids__complex_mass_model__deflections_in_grid_are_sum_of_individual_profiles(self, all_grids):
        #
        #     power_law = mass_profiles.EllipticalPowerLaw(centre=(1.0, 4.0), axis_ratio=0.7, phi=30.0,
        #                                                  einstein_radius=1.0, slope=2.2)
        #
        #     nfw = mass_profiles.SphericalNFW(kappa_s=0.1, scale_radius=5.0)
        #
        #     lens_galaxy = galaxy.Galaxy(redshift=0.1, mass_profile_1=power_law, mass_profile_2=nfw)
        #
        #     lens_plane = ray_tracing.Plane(galaxies=[lens_galaxy], grids=all_grids, compute_deflections=True)
        #
        #     assert lens_plane.grids.image[0] == pytest.approx(np.array([1.0, 1.0]), 1e-5)
        #     assert lens_plane.grids.sub[0] == pytest.approx(np.array([1.0, 1.0]), 1e-5)
        #     assert lens_plane.grids.sub[1] == pytest.approx(np.array([1.0, 0.0]), 1e-5)
        #     assert lens_plane.grids.sub[2] == pytest.approx(np.array([1.0, 1.0]), 1e-5)
        #     assert lens_plane.grids.sub[3] == pytest.approx(np.array([1.0, 0.0]), 1e-5)
        #     assert lens_plane.grids.blurring[0] == pytest.approx(np.array([1.0, 0.0]), 1e-5)
        #
        #     defls = power_law.deflections_at_coordinates(all_grids.image[0]) + \
        #             nfw.deflections_at_coordinates(all_grids.image[0])
        #
        #     sub_defls_0 = power_law.deflections_at_coordinates(all_grids.sub[0, 0]) + \
        #                   nfw.deflections_at_coordinates(all_grids.sub[0, 0])
        #
        #     sub_defls_1 = power_law.deflections_at_coordinates(all_grids.sub[1, 0]) + \
        #                   nfw.deflections_at_coordinates(all_grids.sub[1, 0])
        #
        #     blurring_defls = power_law.deflections_at_coordinates(all_grids.blurring[0]) + \
        #                      nfw.deflections_at_coordinates(all_grids.blurring[0])
        #
        #     assert lens_plane.coordinates_collection.image[0] == pytest.approx(defls, 1e-3)
        #     assert lens_plane.coordinates_collection.sub[0] == pytest.approx(sub_defls_0, 1e-3)
        #     assert lens_plane.coordinates_collection.sub[1] == pytest.approx(sub_defls_1, 1e-3)
        #     assert lens_plane.coordinates_collection.sub[2] == pytest.approx(sub_defls_0, 1e-3)
        #     assert lens_plane.coordinates_collection.sub[3] == pytest.approx(sub_defls_1, 1e-3)
        #     assert lens_plane.coordinates_collection.blurring[0] == pytest.approx(blurring_defls, 1e-3)

    class TestImageFromGalaxies:

        def test__sersic_light_profile__intensities_equal_to_profile_and_galaxy_values(self, all_grids,
                                                                                       galaxy_light_sersic):
            sersic = galaxy_light_sersic.light_profiles[0]

            profile_intensity_0 = sersic.intensity_at_coordinates(all_grids.sub[0])
            profile_intensity_1 = sersic.intensity_at_coordinates(all_grids.sub[1])
            profile_intensity_2 = sersic.intensity_at_coordinates(all_grids.sub[2])
            profile_intensity_3 = sersic.intensity_at_coordinates(all_grids.sub[3])

            profile_intensity = (profile_intensity_0 +
                                 profile_intensity_1 +
                                 profile_intensity_2 +
                                 profile_intensity_3) / 4

            galaxy_intensity = ray_tracing.intensities_via_sub_grid(all_grids.sub,
                                                                    galaxies=[galaxy_light_sersic])

            plane = ray_tracing.Plane(galaxies=[galaxy_light_sersic], coordinates_collection=all_grids)
            image = plane.generate_image_of_galaxy_light_profiles()

            assert (image[0] == profile_intensity == galaxy_intensity).all()

        # def test__same_as_above__now_with_multiple_sets_of_coordinates(self, all_grids, galaxy_light_sersic):
        #     all_grids.sub = mask.SubCoordinateGrid(
        #         np.array([[1.0, 1.0], [3.0, 3.0], [5.0, -9.0], [-3.2, -5.0],
        #                   [1.0, 1.0], [3.0, 3.0], [5.0, -9.0], [-3.1, -2.0]]), None,
        #         sub_size=2)
        #
        #     # sparse_mask = mask.GridMapping(image_shape=(3, 3), image_pixels=2,
        #     #                            data_to_image=np.array([[1, 1], [2, 2]]),
        #     #                            sub_size=2, sub_to_image=np.array([0, 0, 0, 0, 1, 1, 1, 1]))
        #
        #     sersic = galaxy_light_sersic.light_profiles[0]
        #     profile_intensity_0 = sersic.intensity_at_coordinates(all_grids.sub[0])
        #     profile_intensity_1 = sersic.intensity_at_coordinates(all_grids.sub[1])
        #     profile_intensity_2 = sersic.intensity_at_coordinates(all_grids.sub[2])
        #     profile_intensity_3 = sersic.intensity_at_coordinates(all_grids.sub[3])
        #
        #     profile_intensity_image_0 = (profile_intensity_0 + profile_intensity_1 + profile_intensity_2 +
        #                                  profile_intensity_3) / 4
        #
        #     profile_intensity_4 = sersic.intensity_at_coordinates(all_grids.sub[4])
        #     profile_intensity_5 = sersic.intensity_at_coordinates(all_grids.sub[5])
        #     profile_intensity_6 = sersic.intensity_at_coordinates(all_grids.sub[6])
        #     profile_intensity_7 = sersic.intensity_at_coordinates(all_grids.sub[7])
        #
        #     profile_intensity_image_1 = (profile_intensity_4 + profile_intensity_5 + profile_intensity_6 +
        #                                  profile_intensity_7) / 4
        #
        #     galaxy_intensity = ray_tracing.intensities_via_sub(all_grids.sub,
        # galaxies=[galaxy_light_sersic],
        #                                                                       )
        #
        #     plane = ray_tracing.Plane(galaxies=[galaxy_light_sersic], coordinates_collection=all_grids)
        #     image = plane.generate_image_of_galaxy_light_profiles()
        #
        #     assert (image[0] == profile_intensity_image_0 == galaxy_intensity[0]).all()
        #     assert (image[1] == profile_intensity_image_1 == galaxy_intensity[1]).all()
        #
        # def test__same_as_above__now_galaxy_entered_3_times__intensities_triple(self, all_grids, galaxy_light_sersic):
        #     all_grids.sub = mask.SubCoordinateGrid(
        #         np.array([[1.0, 1.0], [3.0, 3.0], [5.0, -9.0], [-3.2, -5.0],
        #                   [1.0, 1.0], [3.0, 3.0], [5.0, -9.0], [-3.1, -2.0]]), None,
        #         sub_size=2)
        #
        #     # sparse_mask = mask.GridMapping(image_shape=(3, 3), image_pixels=2,
        #     #                            data_to_image=np.array([[1, 1], [2, 2]]),
        #     #                            sub_size=2, sub_to_image=np.array([0, 0, 0, 0, 1, 1, 1, 1]))
        #
        #     sersic = galaxy_light_sersic.light_profiles[0]
        #     profile_intensity_0 = 3.0 * sersic.intensity_at_coordinates(all_grids.sub[0])
        #     profile_intensity_1 = 3.0 * sersic.intensity_at_coordinates(all_grids.sub[1])
        #     profile_intensity_2 = 3.0 * sersic.intensity_at_coordinates(all_grids.sub[2])
        #     profile_intensity_3 = 3.0 * sersic.intensity_at_coordinates(all_grids.sub[3])
        #
        #     profile_intensity_image_0 = (profile_intensity_0 + profile_intensity_1 + profile_intensity_2 +
        #                                  profile_intensity_3) / 4
        #
        #     profile_intensity_4 = 3.0 * sersic.intensity_at_coordinates(all_grids.sub[4])
        #     profile_intensity_5 = 3.0 * sersic.intensity_at_coordinates(all_grids.sub[5])
        #     profile_intensity_6 = 3.0 * sersic.intensity_at_coordinates(all_grids.sub[6])
        #     profile_intensity_7 = 3.0 * sersic.intensity_at_coordinates(all_grids.sub[7])
        #
        #     profile_intensity_image_1 = (profile_intensity_4 + profile_intensity_5 + profile_intensity_6 +
        #                                  profile_intensity_7) / 4
        #
        #     galaxy_intensity = ray_tracing.intensities_via_sub(all_grids.sub,
        # galaxies=[galaxy_light_sersic,
        #                                                                                 galaxy_light_sersic,
        #                                                                                 galaxy_light_sersic],
        #                                                                       )
        #
        #     plane = ray_tracing.Plane(galaxies=[galaxy_light_sersic, galaxy_light_sersic, galaxy_light_sersic],
        #                               coordinates_collection=all_grids)
        #     image = plane.generate_image_of_galaxy_light_profiles()
        #
        #     assert (image[0] == profile_intensity_image_0 == galaxy_intensity[0]).all()
        #     assert (image[1] == profile_intensity_image_1 == galaxy_intensity[1]).all()

    class TestBlurringImageFromGalaxies:

        def test__sersic_light_profile__intensities_equal_to_profile_and_galaxy_values(self, all_grids,
                                                                                       galaxy_light_sersic):
            all_grids.image = mask.CoordinateGrid(np.array([[9.0, 9.0]]))
            all_grids.blurring = mask.CoordinateGrid(np.array([[1.0, 1.0]]))

            sersic = galaxy_light_sersic.light_profiles[0]
            profile_intensity = sersic.intensity_at_coordinates(all_grids.blurring[0])

            blurring_galaxy_intensity = ray_tracing.intensities_via_grid(all_grids.blurring,
                                                                         galaxies=[galaxy_light_sersic])

            plane = ray_tracing.Plane(galaxies=[galaxy_light_sersic], coordinates_collection=all_grids)
            blurring_image = plane.generate_blurring_image_of_galaxy_light_profiles()

            assert (blurring_image[0] == profile_intensity == blurring_galaxy_intensity).all()

        def test__same_as_above__now_with_multiple_sets_of_coordinates(self, all_grids, galaxy_light_sersic):
            all_grids.image = mask.CoordinateGrid(np.array([[1.0, 1.0], [3.0, 3.0], [5.0, -9.0], [-3.2, -5.0]]))
            all_grids.blurring = mask.CoordinateGrid(
                np.array([[1.0, 1.0], [5.0, 5.0], [-2.0, -9.0], [5.0, 7.0]]))

            sersic = galaxy_light_sersic.light_profiles[0]
            profile_intensity_0 = sersic.intensity_at_coordinates(all_grids.blurring[0])
            profile_intensity_1 = sersic.intensity_at_coordinates(all_grids.blurring[1])
            profile_intensity_2 = sersic.intensity_at_coordinates(all_grids.blurring[2])
            profile_intensity_3 = sersic.intensity_at_coordinates(all_grids.blurring[3])

            blurring_galaxy_intensity = ray_tracing.intensities_via_grid(all_grids.blurring,
                                                                         galaxies=[galaxy_light_sersic])

            plane = ray_tracing.Plane(galaxies=[galaxy_light_sersic], coordinates_collection=all_grids)
            blurring_image = plane.generate_blurring_image_of_galaxy_light_profiles()

            assert (blurring_image[0] == profile_intensity_0 == blurring_galaxy_intensity[0]).all()
            assert (blurring_image[1] == profile_intensity_1 == blurring_galaxy_intensity[1]).all()
            assert (blurring_image[2] == profile_intensity_2 == blurring_galaxy_intensity[2]).all()
            assert (blurring_image[3] == profile_intensity_3 == blurring_galaxy_intensity[3]).all()

        def test__same_as_above__now_galaxy_entered_3_times__intensities_triple(self, all_grids, galaxy_light_sersic):
            all_grids.image = mask.CoordinateGrid(np.array([[1.0, 1.0], [3.0, 3.0], [5.0, -9.0], [-3.2, -5.0]]))
            all_grids.blurring = mask.CoordinateGrid(
                np.array([[1.0, 1.0], [5.0, 5.0], [-2.0, -9.0], [5.0, 7.0]]))

            sersic = galaxy_light_sersic.light_profiles[0]
            profile_intensity_0 = sersic.intensity_at_coordinates(all_grids.blurring[0])
            profile_intensity_1 = sersic.intensity_at_coordinates(all_grids.blurring[1])
            profile_intensity_2 = sersic.intensity_at_coordinates(all_grids.blurring[2])
            profile_intensity_3 = sersic.intensity_at_coordinates(all_grids.blurring[3])

            blurring_galaxy_intensity = ray_tracing.intensities_via_grid(all_grids.blurring,
                                                                         galaxies=[galaxy_light_sersic])

            plane = ray_tracing.Plane(galaxies=[galaxy_light_sersic, galaxy_light_sersic, galaxy_light_sersic],
                                      coordinates_collection=all_grids)
            blurring_image = plane.generate_blurring_image_of_galaxy_light_profiles()

            assert (blurring_image[0] == 3.0 * profile_intensity_0 == 3.0 * blurring_galaxy_intensity[0]).all()
            assert (blurring_image[1] == 3.0 * profile_intensity_1 == 3.0 * blurring_galaxy_intensity[1]).all()
            assert (blurring_image[2] == 3.0 * profile_intensity_2 == 3.0 * blurring_galaxy_intensity[2]).all()
            assert (blurring_image[3] == 3.0 * profile_intensity_3 == 3.0 * blurring_galaxy_intensity[3]).all()

    class TestPixelizationFromGalaxies:

        def test__no_galaxies_with_pixelizations_in_plane__returns_none(self, all_grids, sparse_mask):
            galaxy_no_pix = galaxy.Galaxy()

            plane = ray_tracing.Plane(galaxies=[galaxy_no_pix], coordinates_collection=all_grids)

            pix_matrix = plane.generate_pixelization_matrices_of_galaxy(sparse_mask)

            assert pix_matrix is None

        def test__1_galaxy_in_plane__it_has_pixelization__extracts_pixelization_matrix(self, all_grids, sparse_mask):
            galaxy_pix = galaxy.Galaxy(pixelization=MockPixelization(value=1))

            plane = ray_tracing.Plane(galaxies=[galaxy_pix], coordinates_collection=all_grids)

            pix_matrix = plane.generate_pixelization_matrices_of_galaxy(sparse_mask)

            assert pix_matrix == 1

        def test__2_galaxies_in_plane__1_has_pixelization__extracts_pixelization_matrix(self, all_grids, sparse_mask):
            galaxy_pix = galaxy.Galaxy(pixelization=MockPixelization(value=1))
            galaxy_no_pix = galaxy.Galaxy()

            plane = ray_tracing.Plane(galaxies=[galaxy_no_pix, galaxy_pix], coordinates_collection=all_grids)

            pix_matrix = plane.generate_pixelization_matrices_of_galaxy(sparse_mask)

            assert pix_matrix == 1

        def test__2_galaxies_in_plane__both_have_pixelization__raises_error(self, all_grids, sparse_mask):
            galaxy_pix_0 = galaxy.Galaxy(pixelization=MockPixelization(value=1))
            galaxy_pix_1 = galaxy.Galaxy(pixelization=MockPixelization(value=2))

            plane = ray_tracing.Plane(galaxies=[galaxy_pix_0, galaxy_pix_1], coordinates_collection=all_grids)

            with pytest.raises(exc.PixelizationException):
                plane.generate_pixelization_matrices_of_galaxy(sparse_mask)

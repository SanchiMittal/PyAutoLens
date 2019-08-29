import autofit as af
import autolens as al
from test.integration.tests import runner

test_type = "lens__source"
test_name = "lens_light_mass__source__hyper"
data_type = "lens_light__source_smooth"
data_resolution = "LSST"


def make_pipeline(name, phase_folders, optimizer_class=af.MultiNest):

    phase1 = al.PhaseImaging(
        phase_name="phase_1",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                light=al.light_profiles.SphericalDevVaucouleurs,
                mass=al.mass_profiles.EllipticalIsothermal,
            ),
            source=al.GalaxyModel(
                redshift=1.0, light=al.light_profiles.EllipticalSersic
            ),
        ),
        optimizer_class=optimizer_class,
    )

    phase1.optimizer.const_efficiency_mode = True
    phase1.optimizer.n_live_points = 60
    phase1.optimizer.sampling_efficiency = 0.8

    phase1 = phase1.extend_with_multiple_hyper_phases(hyper_galaxy=True)

    class HyperLensSourcePlanePhase(al.PhaseImaging):
        def customize_priors(self, results):

            self.galaxies.lens.light = results.from_phase(
                "phase_1"
            ).variable.galaxies.lens.light

            self.galaxies.lens.mass = results.from_phase(
                "phase_1"
            ).variable.galaxies.lens.mass

            self.galaxies.source.light = results.from_phase(
                "phase_1"
            ).variable.galaxies.source.light

            self.galaxies.lens.hyper_galaxy = (
                results.last.hyper_combined.constant.galaxies.lens.hyper_galaxy
            )

            self.galaxies.source.hyper_galaxy = (
                results.last.hyper_combined.constant.galaxies.source.hyper_galaxy
            )

    phase2 = HyperLensSourcePlanePhase(
        phase_name="phase_2",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                light=al.light_profiles.SphericalDevVaucouleurs,
                mass=al.mass_profiles.EllipticalIsothermal,
                hyper_galaxy=al.HyperGalaxy,
            ),
            source=al.GalaxyModel(
                redshift=1.0,
                light=al.light_profiles.EllipticalSersic,
                hyper_galaxy=al.HyperGalaxy,
            ),
        ),
        optimizer_class=optimizer_class,
    )

    phase2.optimizer.const_efficiency_mode = True
    phase2.optimizer.n_live_points = 40
    phase2.optimizer.sampling_efficiency = 0.8

    phase2 = phase2.extend_with_multiple_hyper_phases(hyper_galaxy=True)

    return al.PipelineImaging(name, phase1, phase2)


if __name__ == "__main__":
    import sys

    runner.run(sys.modules[__name__])

import autofit as af
import autolens as al
from test_autolens.integration.tests.imaging import runner

test_type = "reult_passing"
test_name = "lens_light_instance_via_af_last_dont_specify_light"
data_type = "lens_sie__source_smooth"
data_resolution = "lsst"


def make_pipeline(name, phase_folders, optimizer_class=af.MultiNest):

    phase1 = al.PhaseImaging(
        phase_name="phase_1",
        phase_folders=phase_folders,
        galaxies=dict(
            lens=al.GalaxyModel(
                redshift=0.5,
                light=al.lp.SphericalDevVaucouleurs,
                mass=al.mp.EllipticalIsothermal,
            ),
            source=al.GalaxyModel(redshift=1.0, light=al.lp.EllipticalSersic),
        ),
        sub_size=1,
        optimizer_class=optimizer_class,
    )

    phase1.optimizer.const_efficiency_mode = True
    phase1.optimizer.n_live_points = 60
    phase1.optimizer.sampling_efficiency = 0.8

    # This is an example of how we would like to pass a lens between pipelines without specifying the lens light model.

    # It doesn't work - the parameter space has N = 7 meaning the lens light AND mass are not being passed.

    lens = af.last.instance.galaxies.lens
    lens.mass = af.last.model.galaxies.lens.mass

    phase2 = al.PhaseImaging(
        phase_name="phase_2",
        phase_folders=phase_folders,
        galaxies=dict(lens=lens, source=phase1.result.model.galaxies.source),
        sub_size=1,
        optimizer_class=optimizer_class,
    )

    return al.PipelineDataset(name, phase1, phase2)


if __name__ == "__main__":
    import sys

    runner.run(sys.modules[__name__])

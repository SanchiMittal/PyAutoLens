from autolens.pipeline import phase
from autolens.pipeline import pipeline
from autolens.autofit import non_linear as nl
from autolens.imaging import image as im
from autolens.imaging import mask
from autolens.lensing import galaxy_model as gp
from autolens.profiles import light_profiles as lp
from autolens.profiles import mass_profiles as mp
import os

# In chapter 2, we fitted a strong lens which included the contribution of light from the lens galaxy. We're going to
# fit this lens again (I promise, this is the last time). However, now we're approaching lens modeling with pipelines,
# we can perform a completely different, and indeed significantly faster, analysis of this lens system.

# Load up the PDFs from the previous tutorial,
# specifically 'output/howtolens/5_linking_phase_2/optimizer/chains/pdfs/Triangle.png'.

pipeline_name = 'pl_basic' # Give the pipeline a name.

def make():

    pipeline.setup_pipeline_path(pipeline_name) # Setup the path using the pipeline name.

    # This line follows the same syntax as our phase did in phase/2_phase.py. However, as we're breaking the analysis
    # down to only fit the lens's light, that means we use the 'LensPlanePhase' and just specify the lens galaxy.
    phase1 = phase.LensPlanePhase(lens_galaxies=[gp.GalaxyModel(sersic=lp.EllipticalSersic)],
                                  optimizer_class=nl.MultiNest, phase_name='ph1')

    # In phase 2, we fit the source galaxy's light. Thus, we want to make 2 changes from the previous phase:
    # 1) We want to fit the lens subtracted _image computed in phase 1, instead of the observed _image.
    # 2) We want to mask the central regions of this _image, where there are residuals from the lens light subtraction.

    # Below, we use the 'modify_image' and 'mask_function' to overwrite the _image and mask that are used in this phase.
    # The modify_image function has access to and uses 'previous_results' - these are the results computed in phase 1.
    class LensSubtractedPhase(phase.LensSourcePlanePhase):

        def modify_image(self, masked_image, previous_results):
            phase_1_results = previous_results[0]
            return phase_1_results.lens_subtracted_image

    def mask_function(img):
        return mask.Mask.annular(img.shape, pixel_scale=img.pixel_scale, inner_radius_arcsec=0.4,
                                 outer_radius_arcsec=3.)

    # We setup phase 2 just like any other phase, now using the LensSubtracted phase we created above so that our new
    # _image and masks are used.

    phase2 = LensSubtractedPhase(lens_galaxies=[gp.GalaxyModel(sie=mp.EllipticalIsothermal)],
                                 source_galaxies=[gp.GalaxyModel(sersic=lp.EllipticalSersic)],
                                 optimizer_class=nl.MultiNest, mask_function=mask_function,
                                 phase_name='ph2')

    # Finally, in phase 3, we want to fit all of the lens and source component simulateously, using the results of
    # phases 1 and 2 to initialize the analysis. To do this, we use the 'pass_priors' function, which allows us to
    # map the previous_results of the lens and source galaxies to the galaxies in this phase.
    # The term 'variable' signifies that when we map these results to setup the GalaxyModel, we want the parameters

    # To still be treated as free parameters that are varied during the fit.

    class LensSourcePhase(phase.LensSourcePlanePhase):

        def pass_priors(self, previous_results):
            phase_1_results = previous_results[0]
            phase_2_results = previous_results[1]
            self.lens_galaxies[0] = gp.GalaxyModel(sersic=phase_1_results.variable.lens_galaxies[0].sersic,
                                                   sie=phase_2_results.variable.lens_galaxies[0].sie)
            self.source_galaxies = phase_2_results.variable.source_galaxies

    phase3 = LensSourcePhase(lens_galaxies=[gp.GalaxyPrior(sersic=lp.EllipticalSersicLP,
                                                           sie=mp.EllipticalIsothermalMP)],
                              source_galaxies=[gp.GalaxyPrior(sersic=lp.EllipticalSersicLP)],
                              optimizer_class=nl.MultiNest, phase_name='ph3')

    return pipeline.PipelineImaging(pipeline_name, phase1, phase2, phase3)

# Load the _image data, make the pipeline above and run it.
path = "{}".format(os.path.dirname(os.path.realpath(__file__)))
image = im.load(path=path + '/../data/1_basic/', pixel_scale=0.07)
pipeline_basic = make()
pipeline_basic.run(image=image)
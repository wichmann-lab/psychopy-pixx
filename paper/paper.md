---
title: 'psychopy-pixx: A PsychoPy plugin for VPixx Technologies hardware with highly-precise calibration'
tags:
  - Python
  - Psychopy
  - VPixx
  - ResponsePixx
  - Luminance
  - Buttonbox
authors:
  - name: David-Elias Künstle
    affiliation: "1,2"
    corresponding: true
  - name: Barbara Mühlbauer
    affiliation: 1
  - name: Felix and/or Tom (we have to ask)?
    affiliation: 1
affiliations:
 - name: University of Tübingen
   index: 1
 - name: Tübingen AI Center
   index: 2
date: 26 June 2023
bibliography: paper.bib
---

# Summary

Human vision is remarkable: we can distinguish a wide range of colors, detect
very small changes in brightness, and perceive depth and motion.
These capabilities exceed what normal computers can display.
Research into human vision must push it to the limit and
 therefore uses special software and hardware that is particularly accurate,
 fast, and of high resolution in the colorspace.
The experimental software must control and calibrate the hardware to ensure
that the stimuli are displayed correctly; this is especially important for
experiments that require precise color reproduction.

# Statement of need
`psychopy-pixx` is a Python package that extends PsychoPy [@peirce2007psychopy] for
vision experiments with VPixx Technologies hardware and highly-precise calibration routines.
For vision experiments, there are mainly two software packages, `Psychtoolbox` [@brainard1997psychophysics; @pelli1997videotoolbox; @kleiner2007psychtoolbox3] in MATLAB and `Psychopy` in Python, and only a few hardware manufacturers.
Due to the lack of support in `Psychopy`, users of VPixx hardware had to use their monitors, button boxes or beamers with the MATLAB solution, which requires a license, or create custom software, which is time-consuming and error-prone.
As an official plugin for PsychoPy, `psychopy-pixx` is the first solution that
is well integrated into the PsychoPy ecosystem. Our plugin can be installed
from `Psychopy`'s plugin manager. It provides both graphical user interfaces (called "components")
and a Python API for VPixx monitor *ViewPixx* and button box *ResponsePixx*,
where it exposes many hardware configurations.
The open-source nature of the plugin and its modular design allows the community to contribute to the project and extend it to other hardware like the *ProPixx* projector.
Internally, `psychopy-pixx` uses the hardware manufacturers' low-level API to maximize reliability;
we support *ViewPixx* 16-bit color resolution modes by replacing `Psychopy`'s graphic shader with a custom one that
encodes the 16-bit information in two 8-bit channels.

In addition to the hardware support, `psychopy-pixx` also provides a calibration routine for the monitor
and elevates the accuracy of `Psychopy`'s brightness linearisation to a new level.
Calibration is necessary because different monitors do not display the same color for the same pixel values, but in the experiments, we need high control over the display;
for convenience, we want a linearised display in which twice the pixel value results in twice as bright a screen pixel.
A calibration procedure uses a photometer to measure the displayed brightness of different pixel values and creates a conversion function from desired display to the required pixel value.
The procedure in `Psychopy` uses relatively few measurements to fit as a transfer function using an exponential function.
However, since the brightness of LCD monitors such as the ViewPixx is not exactly exponential, this function can never provide an accurate linearisation [TODO: Figure with ViewPixx luminance measurement].
Therefore, `psychopy-pixx` uses many more readings and interpolates them to obtain a more accurate transfer function; the increased calibration time is easily masked by the significantly increased accuracy. Control measurements prove an accuracy of $10^{-12}$ to $10^{-14} \frac{cd}{m^2}$, which corresponds to several thousand brightness levels.
This means that `psychopy-pixx` meets the highest demands on the brightness accuracy of experiments.


# Citations (remove this before submission)

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures (remove this before submission)

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

- VPixx Technologies: We are not affiliated nor financially supported by VPixx Technologies. We thank them for allowing us to use the logo in the plugin.
- uli for a lot of discussions and teaching about calibration
- silke for administrative support
- tom wallis for the vision of building a plugin that helps the community
- jon peirce, matthew cutone for their help with building a psychopy plugin
- funding (cluster, ai center, imprs-is)

# References
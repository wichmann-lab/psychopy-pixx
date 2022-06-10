import numpy as np
from psychopy.monitors import GammaCalculator


"""
Utility function to fit gamma curve from measurements. 

Psychopy estimates an inverse gamma function from these luminances
as described here: https://www.psychopy.org/general/gamma.html

We would like to use the full inverse (Eq. 3), which
is for some reason called eq.4 in the code.
"""     

# eq4: y = a + (b + k*xx)**gamma  # Pelli & Zhang 1991
# https://www.psychopy.org/_modules/psychopy/monitors
#     /calibTools.html#Monitor.linearizeLums        
EQ_FULL_GAMMA = 4 

def fit_gamma_grid(used_levels: np.ndarray, measured_lums: np.ndarray):
    used_levels = np.asarray(used_levels)
    measured_lums = np.asarray(measured_lums)
    if measured_lums.ndim == 1:
        measured_lums = measured_lums.reshape(1, -1)  

    n_gun, n_measures = measured_lums.shape
    if n_gun not in (1, 4):
        raise ValueError(f"Expect either 1 or 4 measurement series for the guns, got {n_guns}.")    
    if len(used_levels) != n_measures:
        raise ValueError("Expect same number of entries for levels and measures, "
                         f"got {used_levels.shape} and {measured_lums.shape}")
    
    gamma_grid = np.zeros([4, 6])
    for gun in range(4):
        gamma_calc= GammaCalculator(inputs=used_levels, lums=measured_lums[gun], eq=EQ_FULL_GAMMA)
        gamma_grid[gun, 0] = gamma_calc.min
        gamma_grid[gun, 1] = gamma_calc.max
        gamma_grid[gun, 2] = gamma_calc.gamma
        gamma_grid[gun, 3] = gamma_calc.a
        gamma_grid[gun, 4] = gamma_calc.b
        gamma_grid[gun, 5] = gamma_calc.k
    if n_gun == 1:
        gamma_grid[1:, :] = gamma_grid[0, :]
    return gamma_grid

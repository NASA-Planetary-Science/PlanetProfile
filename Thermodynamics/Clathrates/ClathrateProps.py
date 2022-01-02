import numpy as np
from Utilities.dataStructs import Constants

def ClathProps(Plin_MPa, Tlin_K):
    """ Evaluate methane clathrate physical properties using Helgerud et al. (2009): https://doi.org/10.1029/2009JB006451
        for density, Ning et al. (2015): https://doi.org/10.1039/C4CP04212C for thermal expansivity and heat capacity,
        and Waite et al. (2005): https://www.researchgate.net/profile/W-Waite/publication/252708287_Thermal_Property_Measurements_in_Tetrahydrofuran_THF_Hydrate_Between_-25_and_4deg_C_and_Their_Application_to_Methane_Hydrate/links/57b900ae08aedfe0ec94abd7/Thermal-Property-Measurements-in-Tetrahydrofuran-THF-Hydrate-Between-25-and-4deg-C-and-Their-Application-to-Methane-Hydrate.pdf
        for thermal conductivity.
        Range of validity:
            rho_kgm3: P from 30.5 to 97.7 MPa, T from -20 to 15 C
            Cp_JkgK: P at 20 MPa, T from 5 to 292 K
            alpha_pK: P at 0.1 MPa, T from 5 to 268 K (note that Ning et al. also give a parameterization for
                alpha_pK at 20 MPa that differs slightly. Since clathrates only appear at the surface of icy moons,
                we use just the 1 bar value for simplicity.
            kTherm_WmK: P from 13.8 to 24.8 MPa, T from -30 to 20 C


        Args:
            Plin_MPa (float, shape M): Pressures to evaluate in MPa
            Tlin_K (float, shape N): Temperatures to evaluate in K
        Returns:
            rho_kgm3 (float, shape MxN): Mass density in kg/m^3 for each P and T. rho_gcm3 = aT_C + bP_MPa + c
            Cp_JkgK (float, shape MxN): Heat capacity in J/(kg K) for each P and T. Cp_JkgK = aT_K + b
            alpha_pK (float, shape MxN): Thermal expansivity in 1/K for each P and T. alpha_pK = (2aT_K + b)/(aT_K^2 + bT_K + c)
            kTherm_WmK (float, shape MxN): Thermal conductivity in W/(m K) for each P and T. kTherm_WmK = c, a constant, over the specified range.
    """
    P_MPa, T_K = np.meshgrid(Plin_MPa, Tlin_K, indexing='ij')

    T_C = T_K - Constants.T0

    rho_kgm3 = (-2.3815e-4*T_C + 1.1843e-4*P_MPa + 0.92435) * 1e3
    Cp_JkgK = 3.19*T_K + 2150
    alpha_pK = (3.5697e-4*T_K + 0.2558)/(3.5697e-4*T_K**2 + 0.2558*T_K + 1612.8597)
    kTherm_WmK = np.zeros_like(P_MPa) + 0.5

    return rho_kgm3, Cp_JkgK, alpha_pK, kTherm_WmK


""" Dissociation temperatures for clathrates based on a degree-2 fit to
    the dissociation curve at low pressure and a logarithmic fit at higher pressures,
    for curves from Sloan (1998) as reported in Choukron et al. (2010):
    https://doi.org/10.1016/j.icarus.2009.08.011
"""
# For use when P_MPa < 2.567 and T < 273
TclathDissocLower_K = lambda P_MPa: 212.33820985 + 43.37319252*P_MPa - 7.83348412*P_MPa**2
# For use when P_MPa >= 2.567 and T >= 273
TclathDissocUpper_K = lambda P_MPa: -20.3058036 + 8.09637199*np.log(P_MPa/4.56717945e-16)

def ClathStableSloan1998(P_MPa, T_K):
    """ Returns a grid of boolean values to say whether fully occupied methane
        clathrates are stable at the given P,T conditions, based on the dissocation
        curves above.

        Args:
            P_MPa (float, shape N): Pressures in MPa
            T_K (float, shape M): Temperatures in K
        Returns:
            stable (int, shape NxM): Set to Constants.phaseClath (phase ID) if clathrates are stable
                at this P,T and 0 if they are not (if not stable, Ocean.EOS.fn_phase should be
                queried to determine the phase)
    """

    # Avoid log of 0 for surface pressure
    P_MPa[P_MPa==0] = 1e-12
    # Get (P,T) pairs relevant for each portion of the dissociation curve
    Plow_MPa, Tlow_K = np.meshgrid(P_MPa[P_MPa < 2.567], T_K, indexing='ij')
    Pupp_MPa, Tupp_K = np.meshgrid(P_MPa[P_MPa >= 2.567], T_K, indexing='ij')
    # Get evaluation points for lower and upper dissociation curves
    TdissocLower_K = TclathDissocLower_K(Plow_MPa)
    TdissocUpper_K = TclathDissocUpper_K(Pupp_MPa)
    # Assign clathrate phase ID to (P,T) points below the dissociation curves and 0 otherwise
    stableLow = np.zeros_like(Tlow_K).astype(np.int_)
    stableUpp = np.zeros_like(Tupp_K).astype(np.int_)
    stableLow[Tlow_K < TdissocLower_K] = Constants.phaseClath
    stableUpp[Tupp_K < TdissocUpper_K] = Constants.phaseClath
    stable = np.concatenate((stableLow, stableUpp), axis=0)

    return stable


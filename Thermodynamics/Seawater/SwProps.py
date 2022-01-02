import numpy as np
from Utilities.dataStructs import Constants
from gsw.freezing import t_freezing as gswTfreeze
from gsw.conversions import CT_from_t
from gsw.density import sound_speed as gswVP_ms, rho, alpha
from gsw.energy import enthalpy

def SwProps(P_MPa, T_K, wOcean_ppt):
    """ Determine density rho, heat capacity Cp, thermal expansivity alpha,
        and thermal conductivity kTherm as functions of pressure P and
        temperature T for a Seawater composition at a concentration wOcean in
        ppt by mass. Uses the Gibbs Seawater (GSW) implementation of the
        Thermodynamic Equation of Seawater (TEOS-10).

        Args:
            P_MPa (float, shape N): Pressures in MPa
            T_K (float, shape M): Temperature in K
            wOcean_ppt (float): (Absolute) salinity of Seawater in ppt by mass (g/kg)
        Returns:
            rho_kgm3 (float, shape NxM): Mass density of liquid in kg/m^3
            Cp_JkgK (float, shape NxM): Isobaric heat capacity of liquid in J/(kg K)
            alpha_pK (float, shape NxM): Thermal expansivity of liquid in 1/K
            kTherm_WmK (float, shape NxM): Thermal conductivity of liquid in W/(m K)
    """
    T_C = T_K - Constants.T0
    SP_dbar = MPa2seaPressure(P_MPa)
    CT_C = gswT2conservT(wOcean_ppt, T_C, SP_dbar)
    rho_kgm3 = gswDensity_kgm3(wOcean_ppt, CT_C, SP_dbar)

    dCTdT, Cp_JkgK = GetdCTdTanddHdT(wOcean_ppt, CT_C, SP_dbar, T_C)
    print('WARNING: The Python GSW package does not yet contain a calculation for alpha with respect to ' +
          'in-situ temperature, which we use as T_K. alpha_pK will be scaled approximately by evaluating ' +
          'd(CT_C)/d(T_K) numerically and multiplying this by the result from GSW.')
    alpha_pK = gswExpansivity_pK(wOcean_ppt, CT_C, SP_dbar) * dCTdT
    kTherm_WmK = np.zeros_like(alpha_pK) + Constants.kThermWater_WmK  # Placeholder until we implement a self-consistent calculation

    return rho_kgm3, Cp_JkgK, alpha_pK, kTherm_WmK


def gswT2conservT(wOcean_ppt, T_C, SP_dbar, DO_1D=False):
    """ Wrapper for GSW function CT_from_t that can simultaneously handle
        P and T arrays.

        Optional args:
            DO_1D (bool): If True, treat T_C and SP_dbar as same-length arrays that
                represent the values of a depth profile and return a 1D array of CT_C
                values.
    """
    if DO_1D:
        CT_C = np.array([CT_from_t(wOcean_ppt, T_C[i], SP_dbar[i]) for i in range(np.size(SP_dbar))])
    else:
        CT_C = np.array([CT_from_t(wOcean_ppt, T_C, SPi_dbar) for SPi_dbar in SP_dbar])
    return CT_C


def gswEnthalpy_Jkg(wOcean_ppt, CT_C, SP_dbar):
    """ Wrapper for GSW function enthalpy that can simultaneously handle
        P and T arrays.
    """
    H_Jkg = np.array([enthalpy(wOcean_ppt, CT_C[i,:], SP_dbar[i]) for i in range(np.size(SP_dbar))])
    return H_Jkg


def gswDensity_kgm3(wOcean_ppt, CT_C, SP_dbar, DO_1D=False):
    """ Wrapper for GSW function rho that can simultaneously handle
        P and T arrays.

        Optional args:
            DO_1D (bool): If True, treat CT_C and SP_dbar as same-length arrays that
                represent the values of a depth profile and return a 1D array of rho
                values.
    """
    if DO_1D:
        rho_kgm3 = np.array([rho(wOcean_ppt, CT_C[i], SP_dbar[i]) for i in range(np.size(SP_dbar))])
    else:
        rho_kgm3 = np.array([rho(wOcean_ppt, CT_C[i,:], SP_dbar[i]) for i in range(np.size(SP_dbar))])
    return rho_kgm3


def gswExpansivity_pK(wOcean_ppt, CT_C, SP_dbar):
    """ Wrapper for GSW function alpha that can simultaneously handle
        P and T arrays.
    """
    alphawrtCT_pK = np.array([alpha(wOcean_ppt, CT_C[i,:], SP_dbar[i]) for i in range(np.size(SP_dbar))])
    return alphawrtCT_pK


def GetdCTdTanddHdT(wOcean_ppt, CT_C, SP_dbar, T_C, dT=0.01):
    """ Evaluate the first partial derivative of conservative temperature CT in celsius
        with respect to in-situ temperature T in C.

        Args:
            wOcean_ppt (float): (Absolute) salinity of Seawater in ppt by mass (g/kg)
            CT_C (float, shape NxM): Conservative temperature values corresponding
                to input (P,T) arrays in celsius
            SP_dbar (float, shape N): Sea pressures in dbar
            T_C (float, shape M): In-situ temperatures in C
            dT (optional, float): Half the small change in temperature to use to get dCT/dT
                (as we are not dividing this quantity by 2 in operations, it is dT/2)
        Returns:
            dCTdT (float, shape NxM): First partial derivative of CT with respect to T
            dHdT (float, shape NxM): First partial derivative of specific enthalpy H with
                respect to T (equal to Cp_JkgK)
    """
    # Get CT a bit above and a bit below each of the evaluated points
    CTplus_C = gswT2conservT(wOcean_ppt, T_C+dT, SP_dbar)
    CTless_C = gswT2conservT(wOcean_ppt, T_C-dT, SP_dbar)
    # Get dCT, the difference in CT with respect to this small change in T dT
    dCTplus = CTplus_C - CT_C
    dCTless = CT_C - CTless_C
    # Take the average value between the numerically evaluated derivatives above and below
    dCTdT = np.mean([dCTplus/dT, dCTless/dT], axis=0)

    # Use the 3 sets of CT values to also evaluate H(T+/-dT)
    Hmid_Jkg = gswEnthalpy_Jkg(wOcean_ppt, CT_C, SP_dbar)
    Hplus_Jkg = gswEnthalpy_Jkg(wOcean_ppt, CTplus_C, SP_dbar)
    Hless_Jkg = gswEnthalpy_Jkg(wOcean_ppt, CTless_C, SP_dbar)
    # Get differences in H
    dHplus = Hplus_Jkg - Hmid_Jkg
    dHless = Hmid_Jkg - Hless_Jkg
    # Take the average value between the numerically evaluated derivatives above and below
    dHdT = np.mean([dHplus/dT, dHless/dT], axis=0)

    return dCTdT, dHdT


def GetPhaseFnSw(wOcean_ppt):
    """ Return a function for the expected phase for given P and T for the
        salinity w, based on the freezing temperature as determined by GSW.

        Args:
            wOcean_ppt (float): Mass concentration (salinity) in ppt of dissolved salt in ocean waters
        Returns:
            fn_phase (class PhaseFunc): A function of P_MPa and T_K that determines if ocean fluid is
                ice (phase 1) or liquid (phase 0) for given (P,T) for the given salinity
    """
    fn_phase = PhaseFunc(wOcean_ppt)

    return fn_phase


class PhaseFunc:
    def __init__(self, wOcean_ppt):
        self.w_ppt = wOcean_ppt

    def __call__(self, P_MPa, T_K):
        P_MPa = np.asarray(P_MPa)
        T_K = np.asarray(T_K)
        if(np.size(P_MPa)==0 or np.size(T_K)==0):
            # If input is empty, return empty array
            return np.array([])
        elif((np.size(P_MPa) != np.size(T_K)) and not (np.size(P_MPa)==1 or np.size(T_K)==1)):
            # If arrays are different lengths, they are probably meant to get a 2D output
            P_MPa, T_K = np.meshgrid(P_MPa, T_K, indexing='ij')

        # 1. Convert to "sea pressure" and T in celsius as needed for GSW input
        # 2. Subtract the freezing temperature from the input temperature
        # 3. Compare to zero -- if we are below the freezing temp, it's ice I, above, liquid
        # 4. Cast the above comparison (True if less than Tfreeze, False if greater) to int,
        #       so that we get 1 if we are below the freezing temp and 0 if above.
        return (((T_K - Constants.T0) - gswTfreeze(self.w_ppt, MPa2seaPressure(P_MPa), 0)) < 0).astype(np.int_)


def SwSeismic(P_MPa, T_K, wOcean_ppt):
    """ Calculate P-wave sound speed and bulk modulus for Seawater
        composition with salinity wOcean for all (P,T) points,
        from GSW functions.

        Args:
            P_MPa (float, shape N): Pressures in MPa
            T_K (float, shape N): Temperatures in K
            wOcean_ppt (float): Salinity in ppt (g/kg)
        Returns:
            VP_kms (float, shape N): P-wave sound speed in km/s
            KS_GPa (float, shape N): Bulk modulus in GPa
    """
    T_C = T_K - Constants.T0
    SP_dbar = MPa2seaPressure(P_MPa)
    CT_C = gswT2conservT(wOcean_ppt, T_C, SP_dbar, DO_1D=True)
    VP_kms = gswVP_ms(wOcean_ppt, CT_C, SP_dbar) * 1e-3  # 1e-3 to convert from m/s to km/s
    KS_GPa = gswDensity_kgm3(wOcean_ppt, CT_C, SP_dbar, DO_1D=True) * VP_kms**2 * 1e-3  # 1e-3 because (km/s)^2 * (kg/m^3) gives units of MPa, so 1e-3 to convert to GPa
    # KS and VP are returning squared shapes
    return VP_kms, KS_GPa


def MPa2seaPressure(P_MPa):
    """ Calculates "sea pressure" as needed for inputs to GSW functions.
        Sea pressure is defined as the pressure relative to the top of
        the ocean, equal to the absolute pressure less 10.1325 dbar.

        Args:
            P_MPa (float, shape N or NxM): Pressures in MPa
        Returns:
            SP_dbar (float, shape N or NxM): Sea pressures in dbar (1 dbar = 0.1 bar = 0.1 * bar2MPa MPa)
    """
    # Subtract off Earth atmospheric pressure
    SP_MPa = P_MPa - Constants.bar2MPa
    # Convert to dbar
    SP_dbar = SP_MPa * 10 / Constants.bar2MPa

    return SP_dbar

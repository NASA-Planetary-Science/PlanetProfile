import numpy as np
import logging as log
from scipy.io import loadmat
from scipy.interpolate import RegularGridInterpolator, interp1d
from Utilities.dataStructs import Constants
from seafreeze import seafreeze as SeaFreeze

def Molal2ppt(b_molkg, m_gmol):
    """ Convert dissolved salt concentration from molality to ppt

        Args:
            b_molkg (float, shape N): Concentration(s) in mol/kg (molal)
            m_gmol (float, shape 1 or shape N): Molecular weight of solute in g/mol
        Returns:
            w_ppt (float, shape N): Corresponding concentration(s) in ppt by mass
    """
    m_kgmol = m_gmol / 1e3
    w_ppt = b_molkg*m_kgmol / (1 + b_molkg*m_kgmol) * 1e3

    return w_ppt


def Ppt2molal(w_ppt, m_gmol):
    """ Convert dissolved salt concentration from ppt to molal

        Args:
            b_molkg (float, shape N): Concentration(s) in mol/kg (molal)
            m_gmol (float, shape 1 or shape N): Molecular weight of solute in g/mol
        Returns:
            w_ppt (float, shape N): Corresponding concentration(s) in ppt by mass
    """
    m_kgmol = m_gmol / 1e3
    w_frac = w_ppt / 1e3
    b_molkg = w_frac / (1 - w_frac) / m_kgmol

    return b_molkg


def Massppt2molFrac(w_ppt, m_gmol):
    """ Convert dissolved salt concentration from ppt to molar fraction
        of water in the liquid

        Args:
            w_ppt (float, shape N): Mass concentration(s) in g/kg (ppt)
            m_gmol (float): Molecular weight of dissolved salt in g/mol
        Returns:
            xH2O (float, shape N): Corresponding molar fraction(s)
            mBar_gmol (float): Average molar mass of liquid
    """
    mBar_gmol = 1/((1 - w_ppt*1e-3)/Constants.mH2O_gmol + (w_ppt*1e-3)/m_gmol)
    xSalt = (w_ppt*1e-3) * mBar_gmol / m_gmol

    return 1 - xSalt, mBar_gmol


def MgSO4Props(P_MPa, T_K, wOcean_ppt):
    """ Determine density rho, heat capacity Cp, thermal expansivity alpha,
        and thermal conductivity kTherm as functions of pressure P and
        temperature T for dissolved MgSO4 at a concentration wOcean in
        ppt by mass.

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
    fMgSO4Props = loadmat('Thermodynamics/MgSO4/MgSO4EOS2_planetary_smaller_20121116.mat')
    TMgSO4_K = fMgSO4Props['T_smaller_C'][0] + Constants.T0
    wMgSO4_ppt = Molal2ppt(fMgSO4Props['m_smaller_molal'], Constants.mMgSO4_gmol)[0]
    evalPts = np.array([[wOcean_ppt, P, T] for T in T_K for P in P_MPa])
    nPs = np.size(P_MPa)
    # Interpolate the input data to get the values corresponding to the current ocean comp,
    # then get the property values for the input P,T pairs and reshape to how they need
    # to be formatted for use in the ocean EOS.
    rho_kgm3 = np.reshape(RegularGridInterpolator((wMgSO4_ppt, fMgSO4Props['P_smaller_MPa'][0], TMgSO4_K),
                            fMgSO4Props['rho'], bounds_error=False, fill_value=None)(evalPts), (nPs,-1))
    Cp_JkgK = np.reshape(RegularGridInterpolator((wMgSO4_ppt, fMgSO4Props['P_smaller_MPa'][0], TMgSO4_K),
                            fMgSO4Props['Cp'], bounds_error=False, fill_value=None)(evalPts), (nPs,-1))
    alpha_pK = np.reshape(RegularGridInterpolator((wMgSO4_ppt, fMgSO4Props['P_smaller_MPa'][0], TMgSO4_K),
                            fMgSO4Props['alpha'], bounds_error=False, fill_value=None)(evalPts), (nPs,-1))
    kTherm_WmK = np.zeros_like(alpha_pK) + Constants.kThermWater_WmK  # Placeholder until we implement a self-consistent calculation

    return rho_kgm3, Cp_JkgK, alpha_pK, kTherm_WmK


class CG2010:
    # Values from the Choukron and Grasset (2010) thermodynamic model (Table 1):
    # https://doi.org/10.1063/1.3487520
    T0_K = np.array([Constants.T0, 251.16, 252.32, 256.16, np.nan, 256.16, 273.31])
    P0_MPa = np.array([Constants.P0, 209.9, 300.0, 350.1, np.nan, 350.1, 632.4])
    DeltaS0_JkgK = np.array([0.0, -18.79, -21.82, -16.19, np.nan, -17.43, -18.78]) / (Constants.mH2O_gmol*1e-3)
    DeltaH0_Jkg = DeltaS0_JkgK * T0_K  # There is an error in CG2010--T0 should be multiplied here, not divided.
    # Now Table 2 values, for calculation of Cp in finding mu:
    c0 = np.array([4190, 74.11, 2200, 820, np.nan, 700, 940])
    c1 = np.array([9, 7.56, 0, 7, np.nan, 7.56, 5.5])
    # Now Table 3 values, for calculation of V in finding mu:
    V0_m3kg = np.array([0.815, 1.086, 0.8425, 0.855, np.nan, 0.783, 0.743]) * 1e-3
    Tref_K = np.array([400, 273.16, 238.45, 256.43, np.nan, 273.31, 356.15])
    a0 = np.array([0.1, 0.019, 0.06, 0.0375, np.nan, 0.005, 0.024])
    a1 = np.array([0.005, 0.0075, 0.0070, 0.0203, np.nan, 0.01, 0.002])
    b0 = np.array([1.0, 0.974, 0.976, 0.951, np.nan, 0.977, 0.969])
    b1 = np.array([0.284, 0.0302, 0.0425, 0.097, np.nan, 0.12, 0.05])
    b2 = np.array([0.00136, 0.00395, 0.0022, 0.002, np.nan, 0.0016, 0.00102])
    # Set number of integration points to use to evaluate chemical potentials
    nIntPts = 100

    def __init__(self):
        self.zeta1 = lambda T_K, phase: 1 + self.a0[phase] * np.tanh(self.a1[phase] * (T_K - self.Tref_K[phase]))
        self.zeta2 = lambda P_MPa, phase: self.b0[phase] + self.b1[phase] * (1 - np.tanh(self.b2[phase] * P_MPa))
        self.CpIce_JkgK = [lambda T, phase=icePhase: self.c0[phase] + self.c1[phase] * T for icePhase in range(1,7)]
        self.CpLiq_JkgK = lambda T: self.c0[0] + self.c1[0] * np.exp(-0.11 * (T - 281.6))
        self.CpRelativeIntegral = [lambda T, phase=icePhase: Integral(lambda Tp: (self.CpIce_JkgK[phase-1](Tp) - self.CpLiq_JkgK(Tp)) -
                                                                               T*(self.CpIce_JkgK[phase-1](Tp) - self.CpLiq_JkgK(Tp))/Tp,
                                                                      self.T0_K[phase], T, nPts=self.nIntPts) for icePhase in range(1,7)]
        self.Vsp_m3kg = [lambda P, T, phase=icePhase: self.V0_m3kg[phase] * self.zeta1(T, phase) * self.zeta2(P, phase) for icePhase in range(7)]
        self.VRelativeIntegral = [lambda P, T, phase=icePhase: Integral(lambda Pp: self.Vsp_m3kg[phase](Pp, T) - self.Vsp_m3kg[0](Pp, T),
                                                                        self.P0_MPa[phase], P, nPts=self.nIntPts)*1e6 for icePhase in range(7)]
        self.W_Jkg = lambda P_MPa, T_K: -1.8e6 * (1 + 150 * np.tanh(1.45e-4 * P_MPa)) * (1 + -12/(T_K - 246)**2)

CG = CG2010()


def Integral(func, a, b, nPts=50):
    """ A function to integrate a Reimann sum, as scipy.integrate.quad seems
        to keep getting the wrong answer. Lower bound must be only one point,
        but upper bound may be an array. This is because where we need the
        integration in evaluating chemical potential, the reference point
        (lower bound) is fixed for each phase.
    """
    b = np.array(b)
    nb = np.size(b)
    result = np.zeros(nb)
    for ib, xb in np.ndenumerate(b):
        if a != xb:
            evalPts = np.linspace(a, xb, nPts)
            dx = evalPts[1] - evalPts[0]
            integrand = np.array([func(evalPt)*dx for evalPt in evalPts])
            result[ib] = np.sum(integrand)

    if nb == 1:
        return result[0]
    else:
        return result


class MgSO4Phase:
    """ Calculate phase of liquid/ice within the hydrosphere for an ocean with
        dissolved MgSO4, given a span of P_MPa, T_K, and w_ppt, based on models
        from Vance et al. 2014: https://doi.org/10.1016/j.pss.2014.03.011
    """
    def __init__(self, wOcean_ppt):
        self.w_ppt = wOcean_ppt
        self.xH2O, self.mBar_gmol = Massppt2molFrac(self.w_ppt, Constants.mMgSO4_gmol)

    def __call__(self, P_MPa, T_K):
        self.nPs = np.size(P_MPa)
        self.nTs = np.size(T_K)
        if(self.nPs == 0 or self.nTs == 0):
            # If input is empty, return empty array
            return np.array([])
        elif(self.nPs != 1 or self.nTs != 1):
            raise RuntimeError('For computational reasons, the Margules formulation has not been ' +
                               'fully implemented for arrays of P and T. Query MgSO4 phase for ' +
                               'single points only until a more rapid+accurate method is implemented.')
        #
        # elif((self.nPs != self.nTs) and not (self.nPs == 1 or self.nTs == 1)):
        #     # If arrays are different lengths, they are probably meant to get a 2D output
        #     P_MPa, T_K = np.meshgrid(P_MPa, T_K, indexing='ij')

        # Determine the chemical potential mu for the ocean liquid based on
        # the Margules equations as in Eqs. 2-4 of Vance et al. 2014:
        # http://dx.doi.org/10.1016/j.pss.2014.03.011
        DeltamuLiquid_Jkg = (CG.W_Jkg(P_MPa,T_K) * (1 - self.xH2O)**2 + Constants.R*T_K/(self.mBar_gmol*1e-3) * np.log(self.xH2O))
        DeltamuIce_Jkg = np.array([CG.DeltaH0_Jkg[phase] - T_K*CG.DeltaS0_JkgK[phase] + CG.CpRelativeIntegral[phase-1](T_K)
                                    + CG.VRelativeIntegral[phase](P_MPa,T_K) for phase in range(1,7)])
        DeltamuAll_Jkg = np.insert(DeltamuIce_Jkg, 0, DeltamuLiquid_Jkg, axis=0)
        # Set ice IV to have infinite chemical potential so it is never considered energetically favorable
        DeltamuAll_Jkg[4] = np.inf

        return np.argmin(DeltamuAll_Jkg, axis=0)

    def arrays(self, P_MPa, T_K):
        self.nPs = np.size(P_MPa)
        self.nTs = np.size(T_K)
        if(self.nPs == 0 or self.nTs == 0):
            # If input is empty, return empty array
            return np.array([])
        elif self.nPs == 1 and self.nTs == 1:
            phase = self.__call__(P_MPa, T_K)
        elif self.nPs == 1:
            log.info(f'Applying Margules phase finder for MgSO4 with {self.nTs} T values. This may take some time.')
            phase = np.array([self.__call__(P_MPa, T) for T in T_K])
        elif self.nTs == 1:
            log.info(f'Applying Margules phase finder for MgSO4 with {self.nPs} P values. This may take some time.')
            phase = np.array([self.__call__(P, T_K) for P in P_MPa])
        elif self.nTs == self.nPs:
            log.info(f'Applying Margules phase finder for MgSO4 with {self.nPs} (P,T) pairs. This may take some time.')
            phase = np.array([self.__call__(P, T_K[i]) for i, P in np.ndenumerate(P_MPa)])
        else:
            log.info(f'Applying Margules phase finder for MgSO4 with {self.nPs} P values and ' +
                     f'{self.nTs} T values. This may take some time.')
            phase = np.array([[self.__call__(P, T) for T in T_K] for P in P_MPa])

        return phase


class MgSO4Seismic:
    def __init__(self, wOcean_ppt):
        self.w_ppt = wOcean_ppt

    def __call__(self, P_MPa, T_K):
        raise RuntimeError('MgSO4Seismic is not implemented yet. See MgSO4_EOS2_planetary_velocity_smaller_vector.m and fluidSoundSpeeds in PlanetProfile.m')
        return VP_kms, KS_GPa


class MgSO4Conduct:
    def __init__(self, wOcean_ppt, elecType, rhoType=None, scalingType=None):
        self.w_ppt = wOcean_ppt
        self.type = elecType
        if self.type == 'Vance2018':
            self.Pvals_MPa, self.Tvals_K, self.sigma_Sm = LarionovKryukov1984(self.w_ppt,
                                                                              rhoType=rhoType, scalingType=scalingType)
        elif self.type == 'Pan2020':
            self.Pvals_MPa, self.Tvals_K, self.sigma_Sm = Panetal2020()
        else:
            raise ValueError(f'No MgSO4 conductivity model is specified for Ocean.electrical = "{self.type}"')

        self.fn_sigma_Sm = RectBivariateSpline(self.Pvals_MPa, self.Tvals_K, self.sigma_Sm)

    def __call__(self, P_MPa, T_K):
        return self.fn_sigma_Sm(P_MPa, T_K)


def LarionovKryukov1984(w_ppt, rhoType=None, scalingType=None):
    """ Get conductivity values for aqueous MgSO4 consistent with extrapolation of Larionov and
        Kryuokov (1984), as detailed in Vance et al. (2018): https://doi.org/10.1002/2017JE005341

        Args:
            w_ppt (float): Mass concentration of MgSO4 in g/kg (ppt)
            rhoType (optional string): Whether to use Millero (?) densities as in the Matlab or
                SeaFreeze for pure water as in Larionov and Kryukov (1984)
            scalingType (optional string): Whether to use scaling law from Vance et al. (2018) or the
                proportional relationship with molality from Larionov and Kryukov (1984)
        Returns:
            Pextrap_MPa (float, shape 20): Pressure range for extrapolation in MPa
            Textrap_K (float, shape 8): Temperature range for extrapolation in K
            sigmaExtrap_Sm (float, shape 20x8): Extrapolated conductivity values corresponding to each P,T pair in S/m
    """
    if rhoType is None:
        rhoType = 'Millero'
    if scalingType is None:
        scalingType = 'Vance2018'

    # Molality of measurements from Larionov and Kryuokov (1984) is 0.01
    b_molkg = 0.01
    if scalingType == 'Vance2018':
        # Define empirical scaling used in Vance 2018 to be consistent with Hand and Chyba (2007)
        Vance2018scaling = 1 + 0.4*w_ppt
    elif scalingType == 'LK1984':
        Vance2018scaling = Ppt2molal(w_ppt, Constants.mMgSO4_gmol) / b_molkg
    else:
        raise ValueError(f'Unrecognized scalingType "{scalingType}".')
    # Define scaling used in Hand and Chyba for 273 K entry from the 298 K entry
    HC2007scaling = 0.525
    PLK_MPa = np.array([0.1, 98.1, 196.1, 294.2, 392.3, 490.3, 588.4, 686.5, 784.6])
    TLK_K = np.array([273, 298, 323, 348, 373, 398, 423])
    LambdaLK_cm2Ohmmol = np.array([[154.6, 238.6, 317.5, 375.6, 412.1, 408.6],
                                   [169.7, 252.5, 334.2, 404.0, 452.3, 472.5],
                                   [174.3, 257.2, 340.3, 415.0, 473.0, 507.4],
                                   [173.8, 256.3, 340.8, 417.1, 480.7, 525.0],
                                   [170.4, 252.4, 336.5, 414.2, 481.1, 531.9],
                                   [164.5, 245.9, 329.4, 407.2, 475.8, 530.8],
                                   [157.6, 237.7, 320.3, 398.0, 468.3, 526.2],
                                   [149.3, 229.0, 310.4, 387.7, 458.2, 517.7],
                                   [139.8, 219.5, 229.9, 376.3, 446.4, 508.4]])
    LambdaLK_cm2Ohmmol = np.insert(LambdaLK_cm2Ohmmol, 0, LambdaLK_cm2Ohmmol[:,0]*HC2007scaling, axis=1)
    if rhoType == 'Millero':
        rhoLK_kgm3 = np.array([[1.0011, 0.9980, 0.9851, 0.9630, 0.9331, 0.9331, 0.9331],
                               [1.0016, 0.9985, 0.9855, 0.9635, 0.9337, 0.9337, 0.9337],
                               [1.0021, 0.9989, 0.9859, 0.9640, 0.9342, 0.9342, 0.9342],
                               [1.0026, 0.9993, 0.9864, 0.9644, 0.9347, 0.9347, 0.9347],
                               [1.0031, 0.9998, 0.9868, 0.9649, 0.9353, 0.9353, 0.9353],
                               [1.0036, 1.0002, 0.9872, 0.9654, 0.9358, 0.9358, 0.9358],
                               [1.0041, 1.0007, 0.9877, 0.9658, 0.9364, 0.9364, 0.9364],
                               [1.0046, 1.0011, 0.9881, 0.9663, 0.9369, 0.9369, 0.9369],
                               [1.0051, 1.0015, 0.9885, 0.9668, 0.9374, 0.9374, 0.9374]]) * 1e3
    elif rhoType == 'SeaFreeze':
        # Values in Larionov and Kryukov are calculated assuming pure water densities
        rhoLK_kgm3 = SeaFreeze(np.array([PLK_MPa, TLK_K], dtype=object), 'water1').rho
    else:
        raise ValueError(f'Unrecognized rhoType "{rhoType}".')
    # Reconfiguring the first Eq. from Larionov and Kryukov (1984), and using
    # rho in kg/m^3 instead of 1000 * rho_gcm3, we can get sigma in S/m:
    sigmaLK_Sm = LambdaLK_cm2Ohmmol * 1e2 * b_molkg / rhoLK_kgm3

    nPs = 20
    nTs = 8
    Pextrap_MPa = np.linspace(0.1, 1900.1, nPs)
    Textrap_K = np.concatenate((np.linspace(250, 270, nTs-3), [273, 298, 323]))
    sigmaPextrap_Sm = np.array([interp1d(PLK_MPa, sigmaLK_Sm[:,iT], kind='linear', fill_value='extrapolate')(Pextrap_MPa) for iT in range(3)])
    sigmaExtrap_Sm = np.array([interp1d(TLK_K[:3], sigmaPextrap_Sm[:,iP], kind='linear', fill_value='extrapolate')(Textrap_K) for iP in range(nPs)])

    return Pextrap_MPa, Textrap_K, sigmaExtrap_Sm * Vance2018scaling

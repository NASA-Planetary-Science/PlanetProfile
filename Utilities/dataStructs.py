"""
dataStructs: Create empty classes and subclasses for holding body-specific data
Values are typically set to None as defaults; body-specific values should be set in the PPBody.py files.
Optional SWITCHES are in all caps. These typically have a default value of False.

Example usage:
Planet = PlanetStruct('nameOfBody')
Planet.R_m = 1560e3
Planet.Ocean.comp = 'MgSO4'
Planet.Sil.mantleEOS = 'CV3hy1wt_678_1.tab'
Planet.Do.Fe_CORE = False
"""

# We have to define subclasses first in order to make them instanced to each Planet object
""" Run settings """
class BulkSubstruct():

    def __init__(self):
        self.Tb_K = 200  # Temperature at the bottom of the ice I layer (ice-ocean interface when there are no ice III or V underplate layers)
        self.rho_kgm3 = None  # Bulk density in kg/m^3 -- note that this is intended to be derived and not set.
        self.R_m = None  # Mean body outer radius in m
        self.M_kg = None  # Total body mass in kg
        self.Tsurf_K = None  # Surface temperature in K
        self.Psurf_MPa = None  # Surface pressure in MPa
        self.Cmeasured = None  # Axial moment of inertia C/MR^2, dimensionless
        self.Cuncertainty = None  # Uncertainty (std dev) of C/MR^2 (used to constrain models via consistency within the uncertainty), dimensionless
        self.phiSurface = None  # Scaling value for the ice porosity at the surface (void fraction): falls within a range of 0 and 1. 0 is completely non-porous and larger than 0.2 is rare. From Han et al. (2014)
        self.clathMaxDepth = None  # Fixed limit for thickness of clathrate layer in m
        self.TbIII_K = None  # Temperature at bottom of ice III underplate layer in K
        self.TbV_K = None  # Temperature at bottom of ice V underplate layer in K


""" Runtime flags """
class DoSubstruct:

    def __init__(self):
        self.Fe_CORE = False  # Whether to model an iron core for this body
        self.POROUS_ICE = False  # Whether to model porosity in ice
        self.CLATHRATE = False  # Whether to model clathrates
        self.NO_H2O = False  # Whether to model waterless worlds (like Io)
        self.BOTTOM_ICEIII = False  # Whether to allow Ice III between ocean and ice I layer, when ocean temp is set very low- default is that this is off, can turn on as an error condition
        self.BOTTOM_ICEV = False  # Same as above but also including ice V. Takes precedence (forces both ice III and V to be present).
        self.NO_ICEI_CONVECTION = False  # Whether to suppress convection in the ice I layer - if True, checks Rayleigh number to see if convection conditions are met
        self.FORCE_ICEI_CONVECTION = False  # Whether to force convection in the ice I layer- if True, doesn’t check Rayleigh number, just assumes convection conditions are met
        self.ALLOW_NEG_ALPHA = False  # Whether to permit modeling of a Melosh et. al. layer with negative thermal expansivity
        self.MANTLE_HYDRO_THERMAL_EQ = False  # Whether to set thermal equilibrium between mantle and hydrosphere, where the hydrosphere is not gaining external heat via tidal forcing or radiation
        self.POROUS_ROCK = False  # Whether to model silicates as porous
        self.P_EFFECTIVE = False  # Effective pressure due to presence of water in pores (modeled as lithostatic minus hydrostatic pressure).
        self.IONOS_ONLY = False  # Whether to ignore conducting layers within the body and model magnetic induction happening only in the ionosphere
        self.TAUP_SEISMIC = False  # Whether to make TauP model files and some basic plots using obspy.taup
        self.IONOS_ONLY = False  # Whether to model induction happening only in the ionosphere, as if ocean were totally frozen out


""" Layer step settings """
class StepsSubstruct:

    def __init__(self):
        self.nIceI = None  # Fixed number of steps in outermost ice shell
        self.nClath = None  # Fixed number of steps in clathrates
        self.nHydroMax = None  # Derived working length of hydrosphere layers, gets truncated after layer calcs
        self.nOceanMax = None  # Derived working length of ocean layers, also truncated after layer calcs
        self.nHydro = None  # Derived final number of steps in hydrosphere
        self.nIbottom = None  # Derived number of clathrate + ice I layers
        self.nIIIbottom = None  # Derived number of clathrate + ice I + ice V layers
        self.nSurfIce = None  # Derived number of outer ice layers (above ocean) -- sum of nIceI, nClath, nIceIIILitho, nIceVLitho
        self.nStepsRefRho = None  # Number of values for plotting reference density curves (sets resolution)
        self.nSil = None  # Fixed number of steps in silicate layers
        self.nCore = None  # Fixed number of steps in core layers, if present
        self.nIceIIILitho = 5  # Fixed number of layers to use for ice III when either BOTTOM_ICEIII or BOTTOM_ICEV is True.
        self.nIceVLitho = 5  # Fixed number of layers to use for ice V when BOTTOM_ICEV is True.


""" Hydrosphere assumptions """
class OceanSubstruct:

    def __init__(self):
        self.comp = None  # Type of dominant dissolved salt in ocean. Options: 'Seawater', 'MgSO4', 'NH3', 'NaCl'
        self.wOcean_ppt = None  # Salinity: Concentration of above salt in parts per thousand (ppt)
        self.deltaP = None  # Increment of pressure between each layer in lower hydrosphere/ocean (sets profile resolution)
        self.PHydroMax_MPa = None  # Guessed maximum pressure of the hydrosphere in MPa. Must be greater than the actual pressure, but ideally not by much. Sets initial length of hydrosphere arrays, which get truncated after layer calculations are finished.
        self.electrical = 'Vance2018'  # Type of electrical conductivity model to use. Options: 'Vance2018', 'Pan2020'
        self.QfromMantle_Wm2 = None  # Heat flow from mantle into hydrosphere
        self.sigmaIce_Sm = 1e-8  # Assumed conductivity of ice layers


""" Silicate layers """
class SilSubstruct:

    def __init__(self):
        self.kSil_WmK = None  # Thermal conductivity (k) of silicates in W/(mK)
        self.phiRockMax = None  # Porosity (void fraction) of the rocks at the “seafloor”, where the hydrosphere first comes into contact with rock
        self.sigmaSil_Sm = 1e-16  # Assumed conductivity of silicate rock
        """ Mantle Equation of State (EOS) model """
        self.mantleEOS = None  # Equation of state data to use for silicates
        self.mantleEOSName = None  # Same as above but containing keywords like clathrates in filenames
        self.mantleEOSDry = None  # Name of mantle EOS to use assuming non-hydrated silicates
        self.rhoSilWithCore_kgm3 = 3300  # Assumed density of silicates when a core is present in kg/m^3
        # Derived quantities
        self.Rmean_m = None  # Mantle radius for mean compatible moment of inertia (MoI)
        self.Rrange_m = None  # Mantle radius range for compatible MoI
        self.Rtrade_m = None  # Array of mantle radii for compatible MoIs
        self.rhoMean_kgm3 = None  # Mean mantle density determined from MoI calculations
        self.rhoTrade_kgm3 = None  # Array of mantle densities for compatible MoIs for core vs. mantle tradeoff plot
        self.mFluids = None  # WIP for tracking loss of fluids along the geotherm -- needs a better name.
        # The below not necessary to be implemented until later (says Steve), these 5 are based on DPS presentation in 2017 – 5 diff models of permeability
        #turn off this plot feature until later- create flag, Use POROSITY flag to turn off these plots
        #perm1 = None
        #perm2 = None
        #perm3 = None
        #perm4 = None
        #perm5 = None

""" Core layers """
class CoreSubstruct:

    def __init__(self):
        self.rhoFe_kgm3 = 8000  # Assumed density of pure iron in kg/m^3
        self.rhoFeS_kgm3 = 5150  # Assumed density of iron sulfide in kg/m^3
        self.rhoPoFeFCC = None  # Density of pyrrhottite plus face-centered cubic iron
        self.sigmaCore_Sm = 1e-16  # Fixed electrical conductivity to apply to core (typically low, to ignore core impacts on induction)
        self.coreEOS = 'sulfur_core_partition_SE15_1pctSulfur.tab'  # Default core EOS to use
        # Derived quantities
        self.rho_kgm3 = None  # Core bulk density consistent with assumed mixing ratios of Fe, FeS, etc.
        self.Rmean_m = None  # Core radius for mean compatible moment of inertia (MOI)
        self.Rrange_m = None  # Core radius range for compatible MoI
        self.Rtrade_m = None  # Array of core radii for compatible MoIs
        #Re Steve- put all mass fraction stuff into a separate file until implemented later- remove from dataStructs.py
        #To implement: possible Meteoritics file/class?
        self.xFeSmeteoritic = None  # CM2 mean from Jarosewich 1990
        self.xFeS = None  # Mass fraction of sulfur in the core
        self.xFeCore = None  # This is the total Fe in Fe and FeS
        self.xH2O = None  # Total fraction of water in CM2; use this to compute the excess or deficit indicated by the mineralogical model

""" Seismic properties """
class SeismicSubstruct:
    """ Calculations based on Cammarano et al., 2006 (DOI: 10.1029/2006JE002710)
        in a parameterization for the shear anelasticity quality factor QS (Eqs. 4-6).
        g : Homologous temperature scaling constant- dimensionless constant described as a temperature scaling relative to the melting temperature
        B : Shear anelasticity/quality factor normalization constant, dimensionless - helps quantify the effects of anelastic attenuation on the seismic wavelet caused by fluid movement and grain boundary friction
        gamma : Exponent on the seismic frequency omega, dimensionless - helps describe the frequency dependence of attenuation
        """

    def __init__(self):
        self.lowQDiv = None  # Factor by which to divide the seismic attenuation Q to test out a low-Q value, dimensionless
        # Ice I
        self.BIceI = None
        self.gammaIceI = None
        self.gIceI = None
        # Ice II
        self.BIceII = None
        self.gammaIceII = None
        self.gIceII = None
        # Ice III
        self.BIceIII = None
        self.gammaIceIII = None
        self.gIceIII = None
        # Ice V
        self.BIceV = None
        self.gammaIceV = None
        self.gIceV = None
        # Ice VI
        self.BIceVI = None
        self.gammaIceVI = None
        self.gIceVI = None
        # Silicates
        self.BSil = None
        self.gammaSil = None
        self.gSil = None
        # Derived quantities
        self.VP_kms = None  # Longitudinal (p-wave) sound velocity for each layer in km/s
        self.VS_kms = None  # Shear (s-wave) sound velocity for each layer in km/s
        self.QS = None  # Anelastic shear quality factor Q_S of each layer, divided by omega^gamma to remove frequency dependence. Essentially the ratio of total seismic energy to that lost per cycle, see Stevenson (1983).
        self.KS_GPa = None  # Bulk modulus of each layer in GPa
        self.GS_GPa = None  # Shear modulus of each layer in GPa


""" Magnetic induction """
class MagneticSubstruct:

    def __init__(self):
        self.peaks_Hz = None  # Frequencies in Hz of peaks in Fourier spectrum of magnetic excitations
        self.fOrb_radps = None  # Angular frequency of orbital motion of a moon around its parent planet in radians per second
        self.ionosBounds_m = None  # Upper altitude cutoff for ionosphere layers in m. Omit the surface (don't include 0 in the list).
        self.sigmaIonosPedersen_Sm = None  # Pedersen conductivity for ionospheric layers in S/m. Length must match ionosBounds_m.


""" Main body profile info--settings and variables """
class PlanetStruct:

    # Require a body name as an argument for initialization; define instance attributes
    def __init__(self, name):
        self.name = name

        self.Bulk = BulkSubstruct()
        self.Do = DoSubstruct()
        self.Steps = StepsSubstruct()
        self.Ocean = OceanSubstruct()
        self.Sil = SilSubstruct()
        self.Core = CoreSubstruct()
        self.Seismic = SeismicSubstruct()
        self.Magnetic = MagneticSubstruct()

        # Settings for GetPfreeze start, stop, and step size.
        # Shrink closer to expected melting pressure to improve run times.
        self.PfreezeLower_MPa = 0.1  # Lower boundary for GetPfreeze to search for phase transition
        self.PfreezeUpper_MPa = 300  # Upper boundary for GetPfreeze to search for phase transition
        self.PfreezeRes_MPa = 0.1  # Step size in pressure for GetPfreeze to use in searching for phase transition

        """ Derived quantities (assigned during PlanetProfile runs) """
        # Layer arrays
        self.phase = None  # Phase of the layer input as an integer: ocean=0, ice I through VI are 1 through 6, clathrate=30, silicates=50, iron=100.
        self.r_m = None  # Distance from center of body to the outer bound of current layer in m
        self.z_m = None  # Distance from surface of body to the outer bound of current layer in m
        self.T_K = None  # Temperature of each layer in K
        self.P_MPa = None  # Pressure at top of each layer in MPa
        self.rho_kgm3 = None  # Density of each layer in kg/m^3
        self.g_ms2 = None  # Gravitational acceleration at top of each layer, m/s^2
        self.Cp_JkgK = None  # Heat capacity at constant pressure for each layer's material in J/kg/K
        self.alpha_pK = None  # Thermal expansivity of layer material in hydrosphere in K^-1
        self.phi_frac = None  # Porosity of each layer's material as a fraction of void/solid
        self.sigma_Sm = None  # Electrical conductivity (sigma) in S/m of each conducting layer
        self.MLayer_kg = None  # Mass of each layer in kg
        self.rSigChange_m = None  # Radii of outer boundary of each conducting layer in m (i.e., radii where sigma changes)
        # Individual calculated quantities
        self.zb_km = None  # Thickness of outer ice shell/depth of ice-ocean interface in km in accordance with Vance et al. (2014)
        self.zClath_m = None  # Thickness of clathrate layer at body surface in m
        self.Pb_MPa = None  # Pressure at ice-ocean interface in MPa
        self.PbClath_MPa = None  # Pressure at bottom of clathrate layer in MPa
        self.PbI_MPa = None  # Pressure at bottom of ice I layer in MPa
        self.PbIII_MPa = None  # Pressure at ice III/ice V transition in MPa, only used when BOTTOM_ICEV is True
        self.CMR2mean = None  # Mean value of axial moment of inertia that is consistent with profile core/mantle trades
        # self.Q_Wm2 = None  # ??? WAIT UNTIL IMPLEMENT heat flux at ice shell


""" Params substructs """
# Construct filenames for data, saving/reloading
class DataFilesSubstruct:
    def __init__(self, fName):
        self.saveFile = fName + '.txt'
        self.mantCoreFile = fName + '_mantleCore.txt'
        self.permFile = fName + '_mantlePerm.txt'


# Construct filenames for figures etc.
class FigureFilesSubstruct:
    def __init__(self, fName, xtn):
        self.dummyFig = fName + xtn


""" General parameter options """
class ParamsStruct:

    def __init__(self):
        self.DataFiles = DataFilesSubstruct('')
        self.FigureFiles = FigureFilesSubstruct('', '')

        self.PLOT_SIGS = False  # Make a plot of conductivity as a function of radius
        self.wlims = None  # Minimum and maximum to use for frequency spectrum plots (magnetic induction)
        self.LEGEND = False  # Whether to force legends to appear
        self.LegendPosition = None  # Where to place legends when forced
        self.yLim = None  # y axis limits of hydrosphere density in "Conductivity with interior properties" plot
        self.LineStyle = None  # Default line style to use on plots
        self.wRefLine_temporary = None  # Style of lines showing reference melting curves of hydrosphere density plot-should be done in config.py instead, delete this once implemented there
        self.wRef = None  # Salinities in ppt of reference melting curves

    class lbls: # Not sure we need this in Params for the Python implementation.
        pass


class ConstantsStruct:
    """ General physical constants """
    G = 6.673e-11  # "Big G" gravitational constant, m^3/kg/s
    bar2GPa = 1.01325e-4  # Multiply by this to convert pressure from bars to GPa
    bar2MPa = 1.01325e-1  # Same but for MPa
    PbI_MPa = 210  # ~fixed transition pressure between ice Ih and ice III or V
    T0 = 273.15  # The Celsius zero point in K.
    P0 = 101325  # One standard atmosphere in Pa
    DThermalConductIceI_Wm = 632  # Thermal conductivity of ice Ih in W/m from Andersson et al. (2005)
    # Core modeling--Modifying thermal profile of mantle
    rhoMantleMean = 3000  # Density of silicate layer in mantle, roughly, in kg/m3
    alphaMantleMean = 0.2e-4  # Thermal expansivity of silicates, roughly, in 1/K
    CpMantleMean = 2e6  # Heat capacity of silicates, roughly, in J/(kgK)
    KappaMantleMean = 1e-6  # ???
    nu_mantle = 1e21  # Mantle viscosity in Pa*s, a common number for Earth's mantle
    DeltaT = 800  # Temperature differential in K between core and mantle (???)

Constants = ConstantsStruct()
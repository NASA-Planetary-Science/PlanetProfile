function [Q_Wm2,deltaTBL_m,eTBL_m,Tc,rhoIce,alphaIce,CpIce,kIce,nu,CONVECTION_FLAG]=...
    ConvectionDeschampsSotin2001(Ttop,Tm,Pmid_MPa,h_m,g_ms2,ind)
% Inputs:Ttop= surface temp. Tm=temperature at the bottom of the ice at the ocean
% interface, Pmid_MPa is the half the pressure at the bottom of the ice, presumably the midpoint pressure,h_m is ice shell thickness in meters, g_ms2, gravity, ind is the index to use (2 for pure water Ice I, 16 for clathrates, 1 for ocean)


% determine solid state convection for ices
% based on Deschamps and Sotin 2001, Thermal Convection in Icy Satellites, J. Geophys. Res. 106(E3):5107-5121 (DS2001)

%inds 1-6 are [water, Ice Ih, Ice II, Ice III, Ice V, Ice VI]
if ind==1
    error('Solid state convection isn''t computed for liquid water (ind=1)')
end
varstrs = {'water','Ih','II','III','V','VI'};
Rg=8.314; % J/mol/K - Ideal Gas Constant
E_Jmol = [0 60e3...
    mean([98 55])*1e3 mean([103 151])*1e3...
    136e3   110e3]; %assuming DS2001 value for Ice I, mean values for II and III, and high T value for Ice VI
%nu0 = [0 5e13 1e18 5e12 5e14 5e14]; % (viscosity at melting point) Pa s %ice I value independently selected by DS2001 is the one recommended in Fig. 4b of Durham et al. 1997.  Other values are also from that table, minimum, along the melting curve.
nu0 = [0 1e14 1e18 5e12 5e14 5e14];
%nu0 = [0 1e16 1e18 5e12 5e14 5e14]; %updated from Evan --> I think. the
%second value was 1e14 when Steve pushed to github

Dcond = [0 632 418 242 328 183]; % term for ice V was adapted from the scaling of D*T^-0.612 to D*T^-1 based on the Table 1 of Andersson and Inaba


% c1 and c2 from numerical experiments of , Deschamps and Sotin (2000) as
% summarized in DS2001, in connection with Eq. 9
c1 = 1.43;
c2 = -0.03;
DeltaT = Tm-Ttop;
Tlith = Ttop + 0.3*(DeltaT); % approximation that scales 150K from DS2001 to the generic case.



%Replace with seafreeze or alternate for clathrates
if ind<30 % not clathrates
    B = E_Jmol(ind)/2/Rg/c1;
    C = c2*DeltaT;
    Tc = B*(sqrt(1+2/B*(Tm-C))-1); %DS2001 Eq. 18
    A = E_Jmol(ind)/Rg/Tm; % dimensionless
    nu = nu0(ind)*exp(A*(Tm/Tc-1)); % DS2001 Eq. 11., also Durham et al. 1997 %viscosity
    %nu=1.5e15;
    SF=SeaFreeze([Pmid_MPa,Tc],varstrs{ind});
    %rhoIce=1000./getVspChoukroun2010(Pmid_MPa,Tc,ind); % kg/m3
    rhoIce=SF.rho; % density
    %**alphaIce = log(1000./rhoIce)-log(getVspChoukroun2010(Pmid_MPa,Tc-1,ind)); %1/K
    alphaIce=SF.alpha; %coefficent of thermal expansion
    %**CpIce = CpH2O_Choukroun(Pmid_MPa,Tc,ind); % J/kg/K
    CpIce=SF.Cp; % specific heat
    kIce = getK_Andersson2005(Pmid_MPa,Tc,varstrs{ind},'T'); % W/m/K
    Ra_crit=10^5;
    %Ra_crit=1;
else  % if clathrates
    ind=7;
    E_Jmol(7)=90000; %Durham 2003
    B = E_Jmol(7)/2/Rg/c1;
    C = c2*DeltaT;
    Tc = B*(sqrt(1+2/B*(Tm-C))-1); %DS2001 Eq. 18
    %kIce = getK_Andersson2005(Pmid_MPa,Tc,varstrs{2},'T'); % W/m/K
    kIce=0.5; % W/m/K from Kalousova and Sotin 2020
    A = E_Jmol(7)/Rg/Tm; % dimensionless
    Vcm=19; %cm3 per mol acitvation volume Durham 2003
    nu0(7)=(1e14)*20; %Durham 2003
    %nu0=nu0(2)*20; % viscosity should be about 20z greater than ice.
    nu = nu0(7)*exp(A*(Tm/Tc-1));%; % DS2001 Eq. 11. also Durham et al. 1997
    %nu=2*10^16 % ignore was testing
    %nu = nu0(2)*exp(E_Jmol(2)/Rg/Tm*(Tm/Tc-1)); % see if clathrates and ice have the same viscosity.
    
    SF=Helgerud_sI(Pmid_MPa,Tc);
    rhoIce=SF.rho;
    alphaIce=SF.alpha;
    CpIce = polyval([3.19 2150],Tc); % values from Ning et al 2014
    Q_crit=kIce*(Tc-Ttop)/(h_m);
    TBL_m_crit=kIce*(Tm-Tc)/Q_crit;
    Kappa = kIce/rhoIce/CpIce; % W m2 s
    Ra_del_crit=TBL_m_crit^3/(nu*Kappa/alphaIce/rhoIce/g_ms2/(Tm-Tc));
    Ra_crit=(Ra_del_crit)^(1/0.21);
    Ra_crit=2e7;
    
    
    
    
end

Kappa = kIce/rhoIce/CpIce; % W m2 s
Ra=alphaIce*rhoIce*g_ms2*DeltaT*(h_m^3)/Kappa/nu; % DS2001 Eq. 4  %Kalosuova 2017 uses nu0
%Ra=alphaIce*rhoIce*g_ms2*DeltaT*(h_m^3)/Kappa/nu0(ind); % DS2001 Eq. 4  %Kalosuova 2017 uses nu0

if Ra>Ra_crit % Convection % this may be a kluge; check nu and Kappa, and read the literature to confirm that 10^5 is considered sufficient as indicated by DS2001Fig3
    CONVECTION_FLAG=1;
    Ra_del = 0.28*Ra^0.21; % DS2001 Eq. 8
    %deltaTBL_m=(nu0(ind)*Kappa/alphaIce/rhoIce/g_ms2/(Tm-Tc)*Ra_del)^(1/3); % thermal boundary layer thickness, DS2001 Eq. 19
    deltaTBL_m=(nu*Kappa/alphaIce/rhoIce/g_ms2/(Tm-Tc)*Ra_del)^(1/3); % thermal boundary layer thickness, DS2001 Eq. 19
    Q_Wm2=kIce*(Tm-Tc)/deltaTBL_m; % DS2001 Eq. 20 % heat flux with the ocean
    eTBL_m = kIce*(Tc-Ttop)/Q_Wm2; % Eq. 21
    if eTBL_m>h_m % for now verify the conductive lid thickness is less than thickness of ice shell
        CONVECTION_FLAG=0;
        Tc = DeltaT;
        deltaTBL_m = 0;
        eTBL_m = 0;
        if ind<7
            Q_Wm2=Dcond(ind)*log(Tm/Ttop)/h_m; %heat flux for a conductive lid Ojakangas and Stevenson, 1989 also appears in Barr2009)
        else
            Q_Wm2=kIce*DeltaT/h_m; % clathrates don't have temp dependent Kice so Fourier's law can be used.
        end
    end
%   eTBL_m = kIce*(Tlith-Ttop)/Q_Wm2; % Eq. 22
else % Conduction
    CONVECTION_FLAG=0;
    Tc = DeltaT;
    deltaTBL_m = 0;
    eTBL_m = 0;
    if ind<7
    Q_Wm2=Dcond(ind)*log(Tm/Ttop)/h_m; %heat flux for a conductive lid Ojakangas and Stevenson, 1989 also appears in Barr2009)
    else
        Q_Wm2=kIce*DeltaT/h_m; % clathrates don't have temp dependent Kice so Fourier's law can be used. 
    end
    end


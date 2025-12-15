import numpy as np

class Models():
    """
    This class repertoriates all the models that can be used for the fit.
    """

    models = {}

    def __init__(self):
        self.models["Lorentzian"] = lambda nu, b, a, nu0, gamma, IR=None: self.lorentzian(nu, b, a, nu0, gamma, IR)
        self.models["Lorentzian elastic"] = lambda nu, be, a, nu0, gamma, ae, IR=None: self.lorentzian_elastic(nu, ae, be, a, nu0, gamma, IR)
        self.models["DHO"] = lambda nu, b, a, nu0, gamma, IR=None: self.DHO(nu, b, a, nu0, gamma, IR)
        self.models["DHO elastic"] = lambda nu, be, a, nu0, gamma, ae, IR=None: self.DHO_elastic(nu, ae, be, a, nu0, gamma, IR)
        self.models["Gaussian"] = lambda nu, b, a, nu0, gamma, IR=None: self.gaussian(nu, b, a, nu0, gamma, IR)

    def lorentzian(self, nu, b, a, nu0, gamma, IR = None):
        """Model of a simple lorentzian lineshape

        Parameters
        ----------
        nu : array
            The frequency array
        b : float
            The constant offset of the data
        a : float
            The amplitude of the peak
        nu0 : float
            The center position of the function
        gamma : float
            The linewidth of the function
        IR : array, optional
            The impulse response of the instrument, by default None

        Returns
        -------
        function
            The function associated to the given parameters
        """
        func = b + a*(gamma/2)**2/((nu-nu0)**2+(gamma/2)**2)
        if IR is not None: return np.convolve(func, IR, "same")
        return func
    
    def lorentzian_elastic(self, nu, ae, be, a, nu0, gamma, IR = None):
        """Model of a simple lorentzian lineshape

        Parameters
        ----------
        nu : array
            The frequency array
        ae : float
            The slope of the first order Taylor expansion of the elastic peak at the position of the peak fitted
        be : float
            The constant offset of the data
        a : float
            The amplitude of the peak
        nu0 : float
            The center position of the function
        gamma : float
            The linewidth of the function
        IR : array, optional
            The impulse response of the instrument, by default None

        Returns
        -------
        function
            The function associated to the given parameters
        """
        func =  be + ae*nu + a*(gamma/2)**2/((nu-nu0)**2+(gamma/2)**2)
        if IR is not None: return np.convolve(func, IR, "same")
        return func
    
    def DHO(self, nu, b, a, nu0, gamma, IR = None):
        """Model of a simple lorentzian lineshape

        Parameters
        ----------
        nu : array
            The frequency array
        b : float
            The constant offset of the data
        a : float
            The amplitude of the peak
        nu0 : float
            The center position of the function
        gamma : float
            The linewidth of the function
        IR : array, optional
            The impulse response of the instrument, by default None

        Returns
        -------
        function
            The function associated to the given parameters
        """
        func = b + a * (gamma*nu0)**2/((nu**2-nu0**2)**2+(gamma*nu)**2)
        # This is to only generate one peak and not a doublet
        if np.sign(nu0) == -1: 
            func = func*(nu<=0)
        else: 
            func = func*(nu>=0)
        if IR is not None: return np.convolve(func, IR, "same")
        return func 
    
    def DHO_elastic(self, nu, ae, be, a, nu0, gamma, IR = None):
        """Model of a simple lorentzian lineshape

        Parameters
        ----------
        nu : array
            The frequency array
        ae : float
            The slope of the first order Taylor expansion of the elastic peak at the position of the peak fitted
        be : float
            The constant offset of the data
        a : float
            The amplitude of the peak
        nu0 : float
            The center position of the function
        gamma : float
            The linewidth of the function
        IR : array, optional
            The impulse response of the instrument, by default None

        Returns
        -------
        function
            The function associated to the given parameters
        """
        func = ae*nu + self.DHO(nu, be, a, nu0, gamma)
        if IR is not None: return np.convolve(func, IR, "same")
        return func
  
    def gaussian(self, nu, b, a, nu0, gamma, IR = None):
        """Model of a simple gaussian lineshape
        Parameters
        ----------
        nu : array
            The frequency array
        b : float
            The constant offset of the data
        a : float
            The amplitude of the peak
        nu0 : float
            The center position of the function 
        gamma : float
            The linewidth of the function
        IR : array, optional
            The impulse response of the instrument, by default None
        Returns
        -------
        function
            The function associated to the given parameters
        """
        gamma = 2*np.log(2)/gamma
        func = b + a*np.exp(-(nu-nu0)**2/(2*gamma**2))
        if IR is not None: return np.convolve(func, IR, "same")
        return func 


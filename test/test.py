from HDF5_BLS import Wraper
from HDF5_BLS import Treat

filepath = '/Users/pierrebouvet/Documents/Code/HDF5_BLS/test/test_data/GHOST_example.DAT'

wrp = Wraper()
wrp.open_data(filepath)

scan_amplitude = float(wrp.attributes["SPECTROMETER.Scan_Amplitude"])
wrp.define_abscissa_1D(-scan_amplitude/2, scan_amplitude/2, wrp.data.shape[-1])

treat = Treat()

for i in range(100):
    opt, std = treat.fit_model(wrp.abscissa,
                    wrp.data,
                    7.43,
                    1,
                    normalize = True, 
                    model = "Lorentz", 
                    fit_S_and_AS = True, 
                    window_peak_find = 1, 
                    window_peak_fit = 3, 
                    correct_elastic = True,
                    IR_wndw = [-0.5,0.5])

# print(opt, std)

# for e in treat.treat_steps: print(e)


from HDF5_BLS_analyse import Analyse_VIPA

import matplotlib.pyplot as plt
import numpy as np


def lorentzian(nu, b, a, nu0, gamma):
    return b+a*(gamma/2)**2/((nu-nu0)**2 + (gamma/2)**2)

def simulate_signal_VIPA(nu, b, a, nu0, gamma, FSR, noise, envelope_sigma, a_elastic, gamma_elastic):
    # Get the lower and higher factors of FSR 
    k0 = int(np.floor(nu[0]/FSR))
    kf = int(np.ceil(nu[-1]/FSR))

    # Create signal before envelope and noise
    signal = np.zeros(nu.size)
    for k in range(k0, kf+1):
        signal += lorentzian(nu, b, a, k*FSR - nu0, gamma)
        signal += lorentzian(nu, b, a, k*FSR + nu0, gamma)
        signal += lorentzian(nu, b, a_elastic, k*FSR, gamma_elastic)
    
    # Add envelope
    envelope = np.exp(-np.arange(-nu.size//2, nu.size//2, 1)**2/envelope_sigma**2)
    signal = signal*envelope

    # Add noise
    noise = np.random.normal(0, noise, size = nu.size)
    
    return signal+noise

def freq_to_pixel(nu, b):
    c = nu[0]
    a = (nu[-1]-b*len(nu) - nu[0])/(len(nu)**2)
    pix = np.arange(len(nu))
    f = a*pix**2 + b*pix + c
    return f, pix

    return 

nu = np.linspace(-62, 62, 1000)
f, pixel = freq_to_pixel(nu, b = 5e-2)
signal = simulate_signal_VIPA(nu = f, b = 0, a = 1, nu0 = 5, gamma = 1, FSR = 30, noise = 1e-2, envelope_sigma = 3e2, a_elastic = 0.5, gamma_elastic = 3e-1)

# # p0: pixel of center freauency
# # p1: pixel of k-th order
# # FSR: free spectral range

# b = lambda k, FSR, a, p0, p1: (k*FSR + a * (p0**2 - p1**2))/(p1-p0)
# c = lambda k, FSR, a, p0, p1: (a*p1*p0 * (p1 - p0)- p0*k*FSR)/(p1-p0)

# p0 = 39.130859641455054
# p1 = 554.0326170094557
# p2 = 975.0252357624778

# a_min = lambda k, FSR, p0, p1, pmax: k*FSR / ((p1-p0)*(p0+p1-2*pmax))
# a_max = lambda k, FSR, p0, p1: k*FSR/(p1**2 - p0**2)

# print(a_max(2, 30, p0, p2))

# a_vals = np.array([0.5, 1, 1.5])

# for p in [p0, p1, p2]:
#     plt.axvline(p, color="red")

# for av in a_vals:
#     pix = np.arange(1000)
#     aval = av*a_max(2, 30, p0, p2)
#     bval = b(2, 30, aval, p0, p2)
#     cval = c(2, 30, aval, p0, p2)
#     fr = aval*pix**2 + bval * pix + cval
#     print(av, -bval/(2*aval))
#     plt.plot(pix, fr, label = f"a = {av}")

# p0 = 1000-p0
# p1 = 1000-p1
# p2 = 1000-p2

# for p in [p0, p1, p2]:
#     plt.axvline(p, color="blue")

# for av in a_vals:
#     pix = np.arange(1000)
#     aval = av*a_min(2, 30, p2, p0, 1000)
#     bval = b(2, 30, aval, p2, p0)
#     cval = c(2, 30, aval, p2, p0)
#     fr = aval*pix**2 + bval * pix + cval
#     print(av, -bval/(2*aval))
#     plt.plot(pix, fr, label = f"a = {av}")
# plt.legend()


plt.figure()
plt.subplot(121)
plt.plot(f, signal)
plt.subplot(122)
plt.plot(pixel, signal)

# from HDF5_BLS_analyse.src.VIPA import Analyse_VIPA
analyse = Analyse_VIPA(pixel, signal)

# Identify points
S0 = analyse.add_point(position_center_window=356, window_width=10, type_pnt="Stokes")
E0 = analyse.add_point(position_center_window=401, window_width=10, type_pnt="Elastic")
AS0 = analyse.add_point(position_center_window=446, window_width=10, type_pnt="Anti-Stokes")
S1 = analyse.add_point(position_center_window=602, window_width=10, type_pnt="Stokes")
E1 = analyse.add_point(position_center_window=638, window_width=10, type_pnt="Elastic")
AS1 = analyse.add_point(position_center_window=672, window_width=10, type_pnt="Anti-Stokes")
S2 = analyse.add_point(position_center_window=800, window_width=10, type_pnt="Stokes")
E2 = analyse.add_point(position_center_window=827, window_width=10, type_pnt="Elastic")
AS2 = analyse.add_point(position_center_window=858, window_width=10, type_pnt="Anti-Stokes")


# Plot the points
for p in analyse.points:
    tpe = p[0].split("_")[0]
    val = p[1]

    if tpe == "Stokes":
        plt.axvline(val, color="green")
    elif tpe == "Anti-Stokes":
        plt.axvline(val, color="blue")
    elif tpe == "Elastic":
        plt.axvline(val, color="red")


# Perform interpolation
analyse.interpolate_elastic_inelastic(FSR=30)

new_f = analyse.x
new_f = new_f - new_f[0] + f[0]

plt.subplot(121)
plt.plot(new_f, signal)

plt.show()


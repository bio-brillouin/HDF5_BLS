#include <math.h>  // For mathematical operations

// Lorentzian function in C
double lorentzian_c_func(double nu, double b, double a, double nu0, double gamma) {
    return b + a * pow(gamma / 2, 2) / (pow(nu - nu0, 2) + pow(gamma / 2, 2));
}

// Lorentzian with elastic term in C
double lorentzian_elastic_c_func(double nu, double ae, double be, double a, double nu0, double gamma) {
    return be + ae * nu + a * pow(gamma / 2, 2) / (pow(nu - nu0, 2) + pow(gamma / 2, 2));
}

// Damped Harmonic Oscillator (DHO) function in C
double DHO_c_func(double nu, double b, double a, double nu0, double gamma) {
    return b + a * (gamma * pow(nu0, 2)) / (pow(pow(nu, 2) - pow(nu0, 2), 2) + gamma * pow(nu0, 2));
}

// Damped Harmonic Oscillator (DHO) with elastic term in C
double DHO_elastic_c_func(double nu, double ae, double be, double a, double nu0, double gamma) {
    return be + ae * nu + a * (gamma * pow(nu0, 2)) / (pow(pow(nu, 2) - pow(nu0, 2), 2) + gamma * pow(nu0, 2));
}


// Cost function for Lorentzian fit
double lorentzian_cost_function(const double *parameters, 
                                const double *frequency, 
                                const double *data, 
                                int n_points) {
    double b = parameters[0];     // Offset
    double a = parameters[1];     // Amplitude
    double nu0 = parameters[2];   // Center frequency
    double gamma = parameters[3]; // Linewidth

    double cost = 0.0;  // Initialize cost
    for (int i = 0; i < n_points; ++i) {
        double model_value = lorentzian_c_func(frequency[i], b, a, nu0, gamma);
        double residual = data[i] - model_value;
        cost += pow(residual, 2);  // Sum of squared residuals
    }

    return cost;  // Return total cost
}
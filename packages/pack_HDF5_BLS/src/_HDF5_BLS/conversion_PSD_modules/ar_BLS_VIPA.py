import numpy as np
import scipy.optimize as opt

def extract_center_v0(n_data: np.ndarray, x_0: int, y_0: int, pixel_window: int = 10, threshold: float = 1, error_pos: float = 2, linewidth_IR: float = 0.5):
    """
    Find curvatures in the given data. The curvature is found by performing a lorentzian fit on a window of the data. This window is centered on the pixel (x_0, y_0) and has a width of 2*pixel_window. an initial point is given by (x_0, y_0), and then the maximum is found for each y value. A pixel is considered correct if the maximum value is above the threshold, defined by the product of the parameter "threshold" and the average on the data. The point is then discarded if its position is more than "error_pos" pixels away from the previous point of the curvature (either given or found by the function).

    Parameters
    ----------
    data : ndarray
        2D array of data in which to find curvatures.
    x_0: int
        Initial position (x_0, y_0) to start the search. 
    y_0 : int                        
        Initial position (x_0, y_0) to start the search. 
    pixel_window : int, optional
        Pixel error used to precise pos_0 and perform the polynomial fit to find local maximum. Default is 10.
    threshold : float, optional
        Threshold value to determine valid points based on average intensity. Default is 1.
    error_pos : int, optional
        Maximum allowed error in position change between consecutive points. Default is 2 pixels.

    Returns
    -------
    tuple
        Array of indices where valid curvatures are found in the form of (array of x, array of y)
    """
    
    def initial_guess(n_data, x_0, y_0, pixel_window, threshold, error_pos):
        def fit_function(x, x0, gamma, A, B):
            return B+A/((x-x0)**2+(gamma/2)**2)
            # return B+A*np.exp(-(x-x0)**2/(2*gamma**2))

        x_curv = np.ones(n_data.shape[0]) * x_0 # if there are no curvatures, then the isofrequency corresponds to a single x
        select = np.zeros(n_data.shape[0])

        for j in range(y_0, 0, -1):
            temp = round(x_curv[j+1])
            loc_y = n_data[j, temp-pixel_window : temp+pixel_window]
            loc_x = temp + np.arange(2*pixel_window) - pixel_window 

            popt, _ = opt.curve_fit(fit_function, 
                                    loc_x, 
                                    loc_y, 
                                    p0=[loc_x[np.argmax(loc_y)], linewidth_IR, np.max(loc_y)-np.min(loc_y), np.min(loc_y)])
            x_curv[j] = popt[0]
            
            if np.abs(x_curv[j] - x_curv[j+1]) < error_pos:  select[j] = 1
            else: x_curv[j] = x_curv[j+1]
                
        for j in range(y_0, n_data.shape[0]):
            temp = round(x_curv[j-1])
            loc_y = n_data[j, temp-pixel_window : temp+pixel_window]
            loc_x = temp + np.arange(2*pixel_window) - pixel_window

            popt, _ = opt.curve_fit(fit_function, 
                                    loc_x, 
                                    loc_y, 
                                    p0=[loc_x[np.argmax(loc_y)], linewidth_IR, np.max(loc_y)-np.min(loc_y), np.min(loc_y)])
            x_curv[j] = popt[0]

            if np.abs(x_curv[j] - x_curv[j-1]) < error_pos: 
                select[j] = 1
            else:
                x_curv[j] = x_curv[j-1]

        for j, p in enumerate(x_curv):
            temp = round(p)
            if n_data[j, round(p)] < threshold*np.average(n_data[max(0,j-10):min(j+10, n_data.shape[0]), max(0,temp-10):min(temp+10, n_data.shape[0])]):
                select[j] = 0
    
        return x_curv[np.argwhere(select == 1)], np.arange(n_data.shape[0])[np.argwhere(select == 1)]

    def fit_circle(curv_x, curv_y):
        """Fits a circle to the given data points.

        Parameters
        ----------
        curv_x : array_like
            The x coordinates of the curvatures.
        curv_y : array_like
            The y coordinates of the curvatures.

        Returns
        -------
        cx : float
            The x coordinate of the center of the fitted circle.
        cy : float
            The y coordinate of the center of the fitted circle.
        r : float
            The radius of the fitted circle.
        """
        def fit_circle_radius(c):
            return np.sqrt((curv_x - c[1])**2 + (curv_y - c[0])**2)

        def fit_circle_cost(c):
            Ri = fit_circle_radius(c)
            return np.std(Ri)  # Minimize the standard deviation of radii

        result = opt.minimize(fit_circle_cost, x0=[np.mean(curv_x), -1300])
        return result.x[1], result.x[0], np.mean(fit_circle_radius(result.x)).flatten()[0] # Circle center

    curv_x, curv_y = initial_guess(n_data, x_0, y_0, pixel_window, threshold, error_pos)

    return fit_circle(curv_x, curv_y)

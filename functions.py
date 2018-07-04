import numpy as np
from scipy import optimize
from configparser import ConfigParser

# user defined functions

def LineRamp(initial, final, step):
    return np.linspace(initial, final, num=step)

def ExpRamp(initial, final, step, tau):
    return np.exp(-1*np.linspace(initial, final, num=step)/tau)

def SineMod(initial, final, step, frequency, phase=0):
    return np.sin( (np.linspace(initial, final, num=step)*frequency+phase)/(2*np.pi) )

def StepMod(initial, final, step, frequency):
    return

# physical constants

class Cs133:
    def __init__(self):
        self.mU = 1.667e-27 # Mass: Atomic Mass Unit
        self.bohrmag = 9.27400915e-24
        self.G = 32.889e6 # 2pi x 5.234 MHz
        self.k = 1173230.7104 * 2 * np.pi # 1/m
        self.m = 132.905451 * self.mU  # Cs133

        self.h = 6.626e-34 # J·s
        self.h_bar = 1.055e-34 # J·s
        self.miu = 1.257e-6 # N·A^−2
        self.epsilon = 8.85e-12 # F·m^−1
        self.miu_b = 9.274e-24 # J·T^−1
        self.E_h = 4.35e-18 # J

# atomic properties

class atom(Cs133):

    def __init__(self):
        # initialization
        self.width_x = np.nan
        self.width_y = np.nan
        self.width = (self.width_x + self.width_y)/2
        self.pos_x = np.nan
        self.pos_y = np.nan
        self.od = np.nan
        self.number = np.nan
        self.temperature = np.nan

        # read configuration
        config = ConfigParser()
        config.read('config.ini')

        # absorption imaging
        self.raw_img = np.ones((2, 1024, 1280))
        self.bg_img = config['imaging']['bg_img']
        self.abs_img = -np.log10((self.raw_img[0])/(self.raw_img[1]))

        super().__init__()

    # 2D Gaussian fitting from
    # https://github.com/scipy/scipy-cookbook/blob/master/ipython/FittingData.ipynb
    def gaussian(self, height, center_x, center_y, width_x, width_y):
        """Returns a gaussian function with the given parameters"""
        width_x = float(width_x)
        width_y = float(width_y)
        return lambda x,y: height*np.exp(-(((center_x-x)/width_x)**2+((center_y-y)/width_y)**2)/2)

    def _moments(self, data):
        """Returns (height, x, y, width_x, width_y)
        the gaussian parameters of a 2D distribution by calculating its
        moments """
        total = data.sum()
        X, Y = np.indices(data.shape)
        x = (X*data).sum()/total
        y = (Y*data).sum()/total
        col = data[:, int(y)]
        width_x = np.sqrt(np.abs((np.arange(col.size)-y)**2*col).sum()/col.sum())
        row = data[int(x), :]
        width_y = np.sqrt(np.abs((np.arange(row.size)-x)**2*row).sum()/row.sum())
        height = data.max()
        return height, x, y, width_x, width_y

    def fitgaussian(self, data):
        """Returns (height, x, y, width_x, width_y)
        the gaussian parameters of a 2D distribution found by a fit"""
        params = self._moments(data)
        errorfunction = lambda p: np.ravel(self.gaussian(*p)(*np.indices(data.shape)) - data)
        p, success = optimize.leastsq(errorfunction, params)
        (self.od, self.pos_x, self.pos_y, self.width_x, self.width_y) = p
        return success

if __name__ == "__main__":
    print(LineRamp(0, 10, 10))
    print(ExpRamp(0, 10, 10, 1))
    print(SineMod(0, 10, 10, 1))
    Xin, Yin = np.mgrid[0:201, 0:201]
    test = atom()
    data = test.gaussian(3, 100, 100, 20, 40)(Xin, Yin) + np.random.random(Xin.shape)
    print(test.fitgaussian(data=data))

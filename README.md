# ExpCtrl.py

*Run your BEC experiments pythonically* 🐍


## Feature

* Write your experimental procedures as Python classes and functions.

* 20 MHz (50 ns) step resolution for digital and analog outputs.

* Low cost, flexible hardware.

* Integrated data acquisition (DAQ) and data analysis.

## Hardware Requirements

* Analog and digital output boards based on Professor [Florian Schreck](https://www.uva.nl/en/profile/s/c/f.e.schreck/f.e.schreck.html)'s [design](http://www.strontiumbec.com/)

* [National Instruments](https://www.ni.com/) PCIe-6535B/6536B/6537B 32-Channel digital I/O device

* *(Optional)* [Novatech](http://www.novatechsales.com/) 409B or DDS9m direct digital synthesizer (DDS)

* *(Optional)* [Point Grey](https://www.ptgrey.com/) camera

* *(Optional)* [Andor](http://www.andor.com/) EMCCD

* *(Optional)* [Texas Instruments](https://www.ti.com/) DLP Digital Micromirror Device (DMD)

## Software Requirements

* [Python 3.x](https://www.python.org/)

* [NumPy](https://www.numpy.org/)

* [nidaqmx](https://github.com/ni/nidaqmx-python)

* *(Optional for Point Grey camera)* [Spinnaker SDK](https://www.ptgrey.com/spinnaker-sdk)

* *(Optional for Andor EMCCD)* [andor](https://pypi.org/project/andor/)

## Installation

`$ git clone https://github.com/AceChenX/ExpCtrl.py.git`

## Usage

```python
import experiment
from functions import *
import matplotlib.pyplot as plt

exp = experiment.procedure(simulation=False)

exp.mot()

exp.cmot()

exp.pgc()

exp.drsc()

exp.odt()

exp.evap()

#exp.insitu()
exp.tof(t=20e-3)

exp.abs_img()

exp.run()

print(exp.atom_num)
plt.imshow(exp.atom_img)

```

### Disclaimer

**ExpCtrl** was a personal side project at [Ultracold Quantum Gas and Quantum Optics Lab](https://ultracold.physics.purdue.edu/).

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

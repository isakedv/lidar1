


from typing import Callable, Tuple
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import time
from collections import deque
import serial
from IPython.display import HTML


class AnimatedScatter(object):
    """
    forsøk på en klasse som skulle animere opplegget fra kjor-funksjonen under
    fant på stackoverflow, tror ikke den virka i utgangspunktet
    """

    def __init__(self, stream, numpoints: int = 420):
        self.numpoints = numpoints
        self.stream = stream()

        # Setup the figure and axes...
        self.fig, self.ax = plt.subplots(subplot_kw={"projection": "polar"})
        self.ax.set(ylim=[0, 500])

        # Lagrer punktene i en queue, slik at man de siste punktene
        self.data = deque(maxlen=numpoints)

    def show(self):
        self.ani = animation.FuncAnimation(
            self.fig, self.update, interval=16, init_func=self.setup_plot, blit=True
        )
        plt.show()

    def setup_plot(self):
        """Initial drawing of the scatter plot."""
        x, y = next(self.stream)
        self.scat = self.ax.scatter([x], [y], cmap="jet")
        return (self.scat,)

    def update(self, i: int):
        """Update the scatter plot."""
        self.data.append(next(self.stream))
        # Set x and y data...

        self.scat.set_offsets(np.array(self.data))

        # Smooth alpha, older steps are more transparent
        weights = np.e**np.linspace(1.0,5.0, np.shape(self.data)[0])
        alphas = weights / weights.sum()
        alphas = alphas / alphas[-1]
        #print("alphas:", alphas)
        #self.scat.set_alpha(alphas)
        return (self.scat,)




def kjor_randomwalk() -> Tuple[float, float]:
    """Dummy versjon av kjor, generer random walk"""
    pos = np.array([0, 2], dtype=float)
    while True:
        pos[0] = (pos[0] + np.random.normal() * 0.1) % (2 * np.pi)
        pos[1] = np.clip(pos[1] + np.random.normal() * 0.09, 0, 5)
        yield pos.copy()


def kjor_actual() -> Tuple[float, float]:

    ser = serial.Serial("COM6", 115200, timeout=0, parity=serial.PARITY_NONE)
    state, nof_samples, start_angle, end_angle, angle_diff, angle_incr = 0, 0, 0, 0, 0, 0
    tmp, tmp1, tmp2, x = 0, 0, 0, 0
    nof_bytes = 2
    pos = np.array([0, 2], dtype=float)

    while True:    

        if (ser.inWaiting()>0):
            var = ser.inWaiting()
            x = ser.read()
            x = ord(x)

    
        if (state == 0) : # 2B search for x55AA
            if (x==0xAA) :
                nof_bytes = 1
            elif (nof_bytes == 1) :
                if (x==0x55):
                    nof_bytes = 1
                    state = 1
                else :
                    nof_bytes = 2
        elif (state == 1) : # 1B load packet type
            nof_bytes = 1
            state = 2
        elif (state == 2) : # 1B load nof samples
            nof_samples = x * 2

            tmp = 0
            nof_bytes = 2
            state = 3
        elif (state == 3) : # 2B load start angle
            start_angle = tmp
            tmp = x
            nof_bytes -=1
            if(nof_bytes == 0) :
                start_angle += 256 * x
                start_angle = (start_angle >> 1)/64

                pos[0] = start_angle

                nof_bytes = 2
                state = 4
        elif (state == 4) : # 2B load end angle
            end_angle = tmp
            tmp = x
            nof_bytes -=1
            if(nof_bytes == 0) :
                end_angle += 256 * x
                end_angle = (end_angle >> 1)/64

                angle_diff = end_angle - start_angle

                angle_incr = angle_diff / (nof_samples-1)

                nof_bytes = 2
                state = 5
        elif (state == 5) : # 2B load check code
            nof_bytes -=1
            if(nof_bytes == 0) :
                tmp1 = 0
                tmp2 = 0
                nof_bytes = nof_samples
                state = 6
        elif (state == 6) : # n bytes, load distance data
            nof_bytes -=1
            tmp2 = tmp1
            tmp1 = x
            if (nof_bytes % 2 == 0):
                tmp = (tmp1*256+tmp2) / 4

                pos[1] = tmp


            if(nof_bytes == 0):
                nof_bytes = 2
                state = 0

        yield pos.copy()


if __name__ == "__main__":

    #a = AnimatedScatter(kjor_randomwalk)
    #     
    a = AnimatedScatter(kjor_actual)
    a.show()
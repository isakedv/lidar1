# %%
"""
Oppdrag         : Ta imot raw-data fra YDLIDAR X2
Sist modifisert : 27.11.2020
Forfatter       : Jon M. Sørli
"""

import serial
import time
import numpy as np 

# init variables:

state = 0 
nof_bytes, nof_samples = 2, 0
start_angle, end_angle, angle_diff, angle_incr = 0, 0, 0, 0
tmp, tmp1, tmp2 = 0, 0, 0

# connect to port:

ser = serial.Serial('COM6', 115200, timeout=0,parity=serial.PARITY_NONE)

# run for 5 sec:

t_end = time.time() + 5

while (time.time()  < t_end):

    if ( ser.inWaiting() > 0 ):
        var = ser.inWaiting()
        x = ser.read()
        x = ord(x)

        # 2B search for x55AA
        if(state == 0): 

            if (x==0xAA) :
                nof_bytes = 1

            elif(nof_bytes == 1):

                if (x==0x55):
                    nof_bytes = 1
                    state = 1

                else :
                    nof_bytes = 2

        # 1B load packet type
        elif(state == 1): 
            nof_bytes = 1
            state = 2


        # 1B load nof samples
        elif(state == 2): 

            nof_samples = x * 2
            tmp = 0
            nof_bytes = 2
            state = 3

        # 2B load start angle
        elif(state == 3): 

            start_angle = tmp
            tmp = x
            nof_bytes -=1

            if(nof_bytes == 0):

                start_angle += 256 * x
                start_angle = (start_angle >> 1)/64
                nof_bytes = 2
                state = 4

        # 2B load end angle
        elif(state == 4): 
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

        # 2B load check code
        elif(state == 5): 

            nof_bytes -=1
            if(nof_bytes == 0):
                tmp1 = 0
                tmp2 = 0
                nof_bytes = nof_samples
                state = 6
                print(nof_bytes)


        # n bytes, load distance data
        elif(state == 6): 
            nof_bytes -=1
            tmp2 = tmp1
            tmp1 = x

            if (nof_bytes % 2 == 0):
                tmp = (tmp1*256+tmp2) / 4

            if(nof_bytes == 0) :
                nof_bytes = 2
                state = 0

            
ser.close()   # close port      




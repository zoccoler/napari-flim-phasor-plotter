'''
This function was adapted from PhasorPy v1.0.2 
(https://pypi.org/project/PhasorPy)

MIT License

Copyright (c) 2022 Bruno Schuty

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

def get_phasor_components(flim_data, harmonic=1):
    '''
    Calculate phasor components G and S from the Fourier transform.
    '''
    import numpy as np
    flim_data_fft = np.fft.fft(flim_data, axis=0)
    dc = flim_data_fft[0].real
    # change the zeros to the img average
    dc = np.where(dc != 0, dc, int(np.mean(dc)))
    
    g = flim_data_fft[harmonic].real
    g /= dc
    s = flim_data_fft[harmonic].imag
    s /= -dc

    return g, s, dc
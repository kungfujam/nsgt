'''
Created on 05.11.2011

@author: thomas
'''

import numpy as N
from math import ceil
from itertools import izip
from util import chkM,fftp,ifftp

#@profile
def nsgtf_sl(f_slices,g,wins,nn,M=None,real=False,reducedform=False,measurefft=False):
    M = chkM(M,g)
    
    fft = fftp(measure=measurefft)
    ifft = ifftp(measure=measurefft)
    
    if real:
        if reducedform:
            sl = slice(1,len(g)//2)
#            sl = slice(2,len(g)//2-1)  # more lossy....
        else:
            sl = slice(0,len(g)//2+1)
    else:
        sl = slice(0,None)
    
    maxLg = max(int(ceil(float(len(gii))/mii))*mii for mii,gii in izip(M[sl],g[sl]))
    temp0 = None
    
    loopparams = []
    for mii,gii,win_range in izip(M[sl],g[sl],wins[sl]):
        Lg = len(gii)
        col = int(ceil(float(Lg)/mii))
        assert col*mii >= Lg
        gi1 = gii[:(Lg+1)//2]
        gi2 = gii[-(Lg//2):]
        p = (mii,gii,gi1,gi2,win_range,Lg,col)
        loopparams.append(p)
    
    for f in f_slices:
        Ls = len(f)
        
        # some preparation    
        ft = fft(f)

        if temp0 is None:
            # pre-allocate buffer
            temp0 = N.empty(maxLg,dtype=ft.dtype)
        
        # A small amount of zero-padding might be needed (e.g. for scale frames)
        if nn > Ls:
            ft = N.concatenate((ft,N.zeros(nn-Ls,dtype=ft.dtype)))
        
        c = [] # Initialization of the result
            
        # The actual transform
        for mii,gii,gi1,gi2,win_range,Lg,col in loopparams:
#            Lg = len(gii)            
            # if the number of time channels is too small (mii < Lg), aliasing is introduced
            # wrap around and sum up in the end (below)
#            col = int(ceil(float(Lg)/mii)) # normally col == 1                        
#            assert col*mii >= Lg                        

            temp = temp0[:col*mii]

            # original version
#            t = ft[win_range]*N.fft.fftshift(N.conj(gii))
#            temp[:(Lg+1)//2] = t[Lg//2:]  # if mii is odd, this is of length mii-mii//2
#            temp[-(Lg//2):] = t[:Lg//2]  # if mii is odd, this is of length mii//2

            # modified version to avoid superfluous memory allocation
            t1 = temp[:(Lg+1)//2]
            t1[:] = gi1  # if mii is odd, this is of length mii-mii//2
            t2 = temp[-(Lg//2):]
            t2[:] = gi2  # if mii is odd, this is of length mii//2

            ftw = ft[win_range]
            t2 *= ftw[:Lg//2]
            t1 *= ftw[Lg//2:]

#            (wh1a,wh1b),(wh2a,wh2b) = win_range
#            t2[:wh1a.stop-wh1a.start] *= ft[wh1a]
#            t2[wh1a.stop-wh1a.start:] *= ft[wh1b]
#            t1[:wh2a.stop-wh2a.start] *= ft[wh2a]
#            t1[wh2a.stop-wh2a.start:] *= ft[wh2b]
            
            temp[(Lg+1)//2:-(Lg//2)] = 0  # clear gap (if any)
            
            if col > 1:
                temp = N.sum(temp.reshape((mii,-1)),axis=1)
                
            ci = ifft(temp)
            c.append(ci)
            
        yield c
        
# non-sliced version
def nsgtf(f,g,wins,nn,M=None,real=False,reducedform=False,measurefft=False):
    return nsgtf_sl((f,),g,wins,nn,M=M,real=real,reducedform=reducedform,measurefft=measurefft).next()

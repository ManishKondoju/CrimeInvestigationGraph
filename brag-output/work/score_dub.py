"""Dubstep cut: siren, half-time drums, wobble bass. D minor, 144 BPM.

Tempo is chosen so the grid lands on the film's act breaks: at 144 BPM a
bar is 50 frames, so the title impact (f250) is bar 5 and the second drop
sits on bar 9. The cue is written to the picture, not laid over it.
"""
import numpy as np
from scipy.io import wavfile
from scipy import signal

SR, DUR, FPS, BPM = 44100, 24.0, 30, 144
N = int(SR*DUR); t = np.arange(N)/SR
at = lambda f: f/FPS
BEAT = 60/BPM                      # 0.4167s = 12.5 frames
BAR  = BEAT*4                      # 1.6667s = 50 frames
rng = np.random.default_rng(5)
L = np.zeros(N); R = np.zeros(N)

NOTE = dict(D1=36.71, D2=73.42, F2=87.31, A2=110.0, Bb2=116.54, C3=130.81,
            D3=146.83, F3=174.61, A3=220.0, Bb3=233.08, C4=261.63, D4=293.66, F4=349.23)

def adsr(s,d,a=.01,dec=.3,sus=.7,rel=.6):
    e=np.zeros(N); si,ei=int(s*SR),min(N,int((s+d)*SR))
    if ei<=si: return e
    n=ei-si; ai,di=max(1,int(a*SR)),max(1,int(dec*SR))
    seg=np.ones(n)*sus; k=min(ai,n); seg[:k]=np.linspace(0,1,k)
    if n>ai:
        k2=min(di,n-ai); seg[ai:ai+k2]=np.linspace(1,sus,k2)
    e[si:ei]=seg
    ri=max(1,int(rel*SR)); rs=max(si,ei-ri); e[rs:ei]*=np.linspace(1,0,ei-rs)**1.5
    return e

def saw_stack(f0,det=.012,v=5):
    o=np.zeros(N)
    for i in range(v):
        o+=signal.sawtooth(2*np.pi*f0*(1+(i-(v-1)/2)*det)*t + rng.random()*6.28)
    return o/v

def lp(x,c,blk=256):
    """Lowpass. Small block size so an LFO-driven cutoff actually wobbles."""
    if np.isscalar(c):
        b,a=signal.butter(2,min(c,SR/2-100)/(SR/2),'low'); return signal.lfilter(b,a,x)
    out=np.zeros_like(x); zi=None
    for i in range(0,len(x),blk):
        cc=float(np.mean(c[i:i+blk])) if i<len(c) else 800.
        b,a=signal.butter(2,min(max(cc,50),SR/2-100)/(SR/2),'low')
        if zi is None: zi=signal.lfilter_zi(b,a)*x[i]
        seg,zi=signal.lfilter(b,a,x[i:i+blk],zi=zi); out[i:i+blk]=seg
    return out

def place(sig,pan=0.,amp=1.,off=0):
    global L,R
    p=(pan+1)/2; n=min(len(sig),N-off)
    if n<=0: return
    L[off:off+n]+=sig[:n]*np.cos(p*np.pi/2)*amp
    R[off:off+n]+=sig[:n]*np.sin(p*np.pi/2)*amp

# ======================= COP SIREN =======================
def siren(f_start, dur, mode='wail', amp=.16, pan=0.):
    """Band-limited siren. A real one is a swept tone, not a sawtooth -
    keeping it narrow stops it shredding the top end of the mix."""
    s=int(at(f_start)*SR); n=int(dur*SR); n=min(n,N-s)
    if n<=0: return
    seg=np.arange(n)/SR
    if mode=='wail':      f=720+480*np.sin(2*np.pi*0.33*seg)        # slow sweep
    elif mode=='yelp':    f=760+430*signal.sawtooth(2*np.pi*3.4*seg)# fast
    else:                 f=np.where((seg*2)%2<1, 660., 880.)       # hi-lo
    ph=2*np.pi*np.cumsum(f)/SR
    tone=np.sin(ph)+0.28*np.sin(2*ph)+0.1*np.sin(3*ph)
    env=np.minimum(np.minimum(seg/0.25,1),np.clip((dur-seg)/0.4,0,1))
    tone=lp(tone*env, 2600)
    # a touch of ping-pong so it moves across the stereo field
    place(tone, pan, amp, off=s)
    d=int(0.013*SR)
    place(tone*0.55, -pan, amp, off=s+d)

siren(10, 3.6, 'wail', .10,  .5)     # establishes the world over the cold open
siren(150, 2.4, 'yelp', .085, -.5)    # tension into the turn
siren(218, 1.3, 'yelp', .13,  .3)    # into the first drop
siren(410, 1.0, 'yelp', .115, -.4)    # into the second drop

# ======================= DRUMS (half-time) =======================
duck=np.ones(N)
def kick(f,amp=1.0):
    s=int(at(f)*SR); n=min(int(.6*SR),N-s)
    if n<=0: return
    seg=np.arange(n)/SR
    pitch=165*np.exp(-seg*34)+44
    body=np.sin(2*np.pi*np.cumsum(pitch)/SR)*np.exp(-seg*6.5)
    body=np.tanh(body*2.1)/2.1
    place(body+rng.normal(0,1,n)*np.exp(-seg*200)*.2, 0, amp, off=s)
    dl=min(N-s,int(.30*SR)); duck[s:s+dl]=np.minimum(duck[s:s+dl],np.linspace(.35,1,dl)**.8)

def snare(f,amp=.75):
    s=int(at(f)*SR); n=min(int(.42*SR),N-s)
    if n<=0: return
    seg=np.arange(n)/SR
    b,a=signal.butter(2,1100/(SR/2),'high')
    noise=signal.lfilter(b,a,rng.normal(0,1,n))*np.exp(-seg*24)*.72
    tone=(np.sin(2*np.pi*185*seg)+np.sin(2*np.pi*331*seg))*np.exp(-seg*34)*.5
    place(np.tanh((noise+tone)*1.5), 0, amp, off=s)

def hat(f,amp=.055,open_=False):
    s=int(at(f)*SR); n=min(int((.14 if open_ else .045)*SR),N-s)
    if n<=0: return
    seg=np.arange(n)/SR
    b,a=signal.butter(3,6800/(SR/2),'high')
    place(signal.lfilter(b,a,rng.normal(0,1,n))*np.exp(-seg*(13 if open_ else 55)),
          .35 if (f//6)%2 else -.35, amp, off=s)

BARF = BAR*FPS                      # 50 frames per bar
DROP1, DROP2 = 250, 450             # bar 5 and bar 9
# half-time: kick on 1, snare on 3
for bar in range(int(DUR/BAR)+1):
    b0 = bar*BARF
    if b0 < DROP1-BARF: continue                        # drums enter before drop 1
    inDrop = (DROP1 <= b0 < 330) or (DROP2 <= b0 < 620)
    kick(b0, 1.0 if inDrop else .7)
    snare(b0+BARF/2, .8 if inDrop else .5)
    if inDrop:
        kick(b0+BARF*0.75, .6)
        for k in range(8): hat(b0+k*BARF/8, .05, open_=(k==5))
    else:
        for k in range(4): hat(b0+k*BARF/4, .035)

# ======================= WOBBLE BASS =======================
def wobble(f0, f_start, dur_f, rate_hz, amp=.5, drive=2.4):
    """LFO-swept resonant lowpass on a saw stack - the dubstep signature."""
    s, d = at(f_start), at(dur_f)
    lfo=(np.sin(2*np.pi*rate_hz*(t-s))+1)/2
    cutoff=90+(lfo**2.2)*2500
    sig=lp(saw_stack(f0,.008,4)+saw_stack(f0*0.5,.004,2)*.8, cutoff)
    sig=np.tanh(sig*drive)/drive
    sig*=adsr(s,d,a=.012,dec=.1,sus=.95,rel=.25)
    place(sig, 0, amp*1.9)
    # Dedicated sub an octave down, plus its octave, so the low end is felt
    # rather than merely present.
    sub=np.sin(2*np.pi*(f0/2)*t)*adsr(s,d,a=.02,dec=.1,sus=.95,rel=.3)
    sub+=np.sin(2*np.pi*(f0/4)*t)*adsr(s,d,a=.03,dec=.1,sus=.9,rel=.35)*.75
    place(sub, 0, amp*1.5)

EIGHTH = 1/(BEAT*2)                 # 2.4 Hz
QUARTER= 1/BEAT                     # 4.8 Hz... (rate in Hz)
# drop 1: four bars, alternating wobble rates
wobble(NOTE['D2'], DROP1,            int(BARF),   2.4, .46)
wobble(NOTE['D2'], DROP1+BARF,       int(BARF),   4.8, .46)
wobble(NOTE['Bb2'],DROP1+BARF*2,     int(BARF),   2.4, .44)
wobble(NOTE['C3'], DROP1+BARF*3,     int(BARF*0.8),3.6, .42)
# drop 2: harder, faster
wobble(NOTE['D2'], DROP2,            int(BARF),   4.8, .60)
wobble(NOTE['D2'], DROP2+BARF,       int(BARF),   7.2, .60)
wobble(NOTE['F2'], DROP2+BARF*2,     int(BARF),   4.8, .58)
wobble(NOTE['D2'], DROP2+BARF*3,     int(BARF*1.4),2.4,.56)

# ======================= PADS (keep the film's harmony) =======================
PROG=[(0,250,['D3','F3','A3']),(250,100,['D3','F3','A3']),(350,100,['Bb3','D4','F4']),
      (450,130,['D3','F3','A3']),(580,140,['D3','F3','A3','D4'])]
for (f0,nf,tones) in PROG:
    s,d=at(f0),at(nf)+.8
    for i,nm in enumerate(tones):
        fr=NOTE.get(nm,146.83); e=adsr(s,d,a=.5,dec=.7,sus=.6,rel=1.2)
        vL=lp(saw_stack(fr,.010),1400)*e; vR=lp(saw_stack(fr*1.0008,.011),1500)*e
        hz=int(SR*(.007+.004*i))
        L[:]+=vL*0.055; R[hz:]+=vR[:N-hz]*0.055

# ======================= RISERS / IMPACTS =======================
def riser(f0,f1,amp=.3):
    s,e=int(at(f0)*SR),int(at(f1)*SR); n=e-s; k=np.linspace(0,1,n)
    sw=signal.sawtooth(2*np.pi*np.cumsum(120+k**2*900)/SR)
    body=lp(sw*k**2*.6+rng.normal(0,1,n)*k**2.5*.5,
            np.concatenate([300+k**2*7000]))
    place(body,0,amp,off=s)
riser(200,DROP1,.30); riser(400,DROP2,.24)

def impact(f,amp=.75):
    s=int(at(f)*SR); n=min(int(2.2*SR),N-s); seg=np.arange(n)/SR
    hit=(np.sin(2*np.pi*NOTE['D1']*seg)*np.exp(-seg*2.6)
         +np.sin(2*np.pi*NOTE['D2']*seg)*np.exp(-seg*4)*.55
         +rng.normal(0,1,n)*np.exp(-seg*26)*.3)
    place(np.tanh(hit*1.6)/1.6,0,amp,off=s)
impact(DROP1,.80); impact(DROP2,.72); impact(600,.4)

# ======================= MIX =======================
arc=np.interp(t,[0,at(60),at(150),at(DROP1),at(330),at(DROP2),at(600),DUR],
                [.34,.46,.62,1.0,.80,1.0,.74,.42])
L*=arc*duck; R*=arc*duck
M,S=(L+R)/2,(L-R)/2
b,a=signal.butter(2,170/(SR/2),'high'); S=signal.lfilter(b,a,S)*1.8
L,R=M+S,M-S
L,R=lp(L,15500),lp(R,15500)
pk=max(np.max(np.abs(L)),np.max(np.abs(R))); L,R=L/pk*.86,R/pk*.86
L=np.tanh(L*1.25)/1.25; R=np.tanh(R*1.25)/1.25
fi,fo=int(.05*SR),int(1.6*SR)
for ch in (L,R):
    ch[:fi]*=np.linspace(0,1,fi); ch[-fo:]*=np.linspace(1,0,fo)**1.2
wavfile.write("score_dub.wav",SR,(np.stack([L,R],1)*32767).astype(np.int16))
print(f"score_dub.wav: stereo {DUR}s @ {BPM}BPM, drops at f{DROP1}/f{DROP2}")

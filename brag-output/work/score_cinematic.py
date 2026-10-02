"""Trailer cue in D minor. Stereo, 24s, synthesised from scratch.

The previous pass was mono sine tones over a static drone - thin, and
harmonically motionless. This one has an actual progression, detuned saw
stacks through a moving resonant filter, percussion, reverb, and
sidechain ducking so the low end breathes with the pulse.
"""
import numpy as np
from scipy.io import wavfile
from scipy import signal

SR, DUR, FPS = 44100, 24.0, 30
N = int(SR * DUR)
t = np.arange(N) / SR
at = lambda f: f / FPS
rng = np.random.default_rng(23)
L = np.zeros(N); R = np.zeros(N)

# ---------------------------------------------------------------- helpers
def adsr(s, d, a=0.01, dec=0.3, sus=0.7, rel=0.6):
    """Proper ADSR rather than a raw gate - notes have an attack shape."""
    e = np.zeros(N)
    si, ei = int(s*SR), min(N, int((s+d)*SR))
    if ei <= si: return e
    n = ei - si
    ai, di = max(1,int(a*SR)), max(1,int(dec*SR))
    seg = np.ones(n) * sus
    k = min(ai, n); seg[:k] = np.linspace(0, 1, k)
    if n > ai:
        k2 = min(di, n-ai); seg[ai:ai+k2] = np.linspace(1, sus, k2)
    e[si:ei] = seg
    ri = max(1, int(rel*SR)); rs = max(si, ei-ri)
    e[rs:ei] *= np.linspace(1, 0, ei-rs)**1.5
    return e

def saw_stack(f0, detune=0.012, voices=5):
    """Detuned saw stack - the width and beating a single osc cannot give."""
    out = np.zeros(N)
    for i in range(voices):
        d = (i - (voices-1)/2) * detune
        ph = rng.random()
        out += signal.sawtooth(2*np.pi*f0*(1+d)*t + ph*6.28)
    return out / voices

def lp(x, cutoff, q=0.9):
    """Resonant lowpass. cutoff may be an array - the filter moves."""
    if np.isscalar(cutoff):
        b, a = signal.butter(2, min(cutoff, SR/2-100)/(SR/2), 'low')
        return signal.lfilter(b, a, x)
    # time-varying: process in blocks so the sweep is audible
    out = np.zeros_like(x); blk = 1024; zi = None
    for i in range(0, len(x), blk):
        c = float(np.mean(cutoff[i:i+blk])) if i < len(cutoff) else 800.0
        b, a = signal.butter(2, min(max(c, 60), SR/2-100)/(SR/2), 'low')
        if zi is None: zi = signal.lfilter_zi(b, a) * x[i]
        seg, zi = signal.lfilter(b, a, x[i:i+blk], zi=zi)
        out[i:i+blk] = seg
    return out

def place(sig, pan=0.0, amp=1.0, at_sample=0):
    """Equal-power pan into the stereo bus.

    Accepts a short segment plus an offset so one-shots (kick, perc) do not
    each have to allocate a full-length buffer.
    """
    global L, R
    p = (pan + 1) / 2
    n = min(len(sig), N - at_sample)
    if n <= 0: return
    seg = sig[:n]
    L[at_sample:at_sample+n] += seg * np.cos(p*np.pi/2) * amp
    R[at_sample:at_sample+n] += seg * np.sin(p*np.pi/2) * amp

def reverb(x, decay=0.42, mix=0.3):
    """Schroeder-ish: parallel combs into series allpasses."""
    out = np.zeros_like(x)
    for d_ms, g in ((37.1, decay), (41.3, decay*.92), (49.7, decay*.86), (57.3, decay*.78)):
        d = int(SR*d_ms/1000); buf = np.zeros_like(x)
        if d < len(x):
            buf[d:] = x[:-d]
            for _ in range(5):
                nb = np.zeros_like(buf); nb[d:] = buf[:-d]*g; buf = buf + nb
        out += buf
    out /= 4
    for d_ms, g in ((5.0, .7), (1.7, .7)):
        d = int(SR*d_ms/1000); ap = np.zeros_like(out)
        if d < len(out): ap[d:] = out[:-d]
        out = -g*out + ap + g*np.concatenate([np.zeros(d), out[:-d]]) if d < len(out) else out
    return x*(1-mix) + lp(out, 3200)*mix

# --------------------------------------------------------------- harmony
# Dm -> Bb -> F -> C -> Dm : a real progression, so the cue moves.
NOTE = dict(D2=73.42, F2=87.31, A2=110.0, Bb2=116.54, C3=130.81, D3=146.83,
            F3=174.61, A3=220.0, Bb3=233.08, C4=261.63, D4=293.66, F4=349.23, A4=440.0)
PROG = [  # (start_frame, dur_frames, root, chord tones)
    (  0, 150, NOTE['D2'], ['D3','F3','A3']),
    (150, 100, NOTE['Bb2'], ['Bb3','D4','F4']),
    (250, 100, NOTE['F2'],  ['F3','A3','C4']),
    (350,  80, NOTE['C3'],  ['C4','E4' if 'E4' in NOTE else 'C4','G4' if 'G4' in NOTE else 'C4']),
    (430, 150, NOTE['D2'],  ['D3','F3','A3']),
    (580, 140, NOTE['D2'],  ['D3','F3','A3','D4']),
]

# --------------------------------------------- pads: saw stacks, filtered
for (f0, nf, root, tones) in PROG:
    s, d = at(f0), at(nf) + 0.9
    prog_t = np.clip((t - s) / max(d, .001), 0, 1)
    # filter opens as the cue builds, closes again in the outro
    base = 260 + 1500 * np.clip((t - at(250)) / at(330), 0, 1)
    cutoff = base * (0.55 + 0.75*prog_t)
    for i, nm in enumerate(tones):
        fr = NOTE.get(nm, root*2)
        envp = adsr(s, d, a=0.55, dec=0.8, sus=0.62, rel=1.4)
        # Two independently-seeded stacks, one per channel: genuinely
        # decorrelated rather than one signal panned (which stays mono).
        vL = lp(saw_stack(fr, detune=0.010), cutoff) * envp
        vR = lp(saw_stack(fr*1.0008, detune=0.011), cutoff) * envp
        hz = int(SR * (0.008 + 0.004*i))          # Haas offset widens further
        L[:] += np.concatenate([np.zeros(0), vL])[:N] * 0.085
        R[hz:] += vR[:N-hz] * 0.085
    # sub root
    sub = np.sin(2*np.pi*root*t) * adsr(s, d, a=0.3, dec=0.6, sus=0.85, rel=1.2)
    place(sub, 0.0, 0.30)

# ------------------------------------------------- percussion + sidechain
duck = np.ones(N)
def kick(f, amp=0.9):
    s = int(at(f)*SR); e = min(N, s+int(0.55*SR)); n = e-s
    if n <= 0: return
    seg = np.arange(n)/SR
    pitch = 110*np.exp(-seg*28) + 41            # pitch drop = the thump
    body = np.sin(2*np.pi*np.cumsum(pitch)/SR) * np.exp(-seg*7.5)
    click = rng.normal(0,1,n) * np.exp(-seg*180) * .22
    place((body+click)*amp, 0.0, 1.0, at_sample=s)
    # sidechain: everything dips under the kick and recovers
    dl = min(N-s, int(0.34*SR))
    duck[s:s+dl] = np.minimum(duck[s:s+dl], np.linspace(0.42, 1.0, dl)**0.7)

def perc(f, amp=0.18, pan=0.0, hp=4000, dur=0.1):
    s = int(at(f)*SR); e = min(N, s+int(dur*SR)); n = e-s
    if n <= 0: return
    seg = np.arange(n)/SR
    b, a = signal.butter(2, hp/(SR/2), 'high')
    place(signal.lfilter(b, a, rng.normal(0,1,n))*np.exp(-seg*42), pan, amp, at_sample=s)

# rhythm enters with the turn, drives through the payoff, resolves at the end
for f in range(150, 580, 30):   kick(f, 0.85 if f % 60 == 0 else 0.55)
for f in range(170, 580, 30):   perc(f, 0.10, pan=((f//30)%2)*0.7-0.35)
for f in range(160, 580, 15):   perc(f, 0.045, pan=-0.5 if (f//15)%2 else 0.5, hp=7000, dur=0.05)
kick(250, 1.0); kick(430, 0.95); kick(580, 0.8); kick(700, 0.6)

# ------------------------------------------------------- transition FX
def riser(f0, f1, amp=0.3):
    s, e = int(at(f0)*SR), int(at(f1)*SR); n = e-s
    k = np.linspace(0, 1, n)
    sw = signal.sawtooth(2*np.pi*np.cumsum(110 + k**2*700)/SR)
    nz = rng.normal(0, 1, n) * k**2.5
    body = lp(np.concatenate([np.zeros(s), sw*k**2*.5 + nz*.5, np.zeros(N-e)]),
              np.concatenate([np.full(s, 300), 300+k**2*6500, np.full(N-e, 300)]))
    place(body, 0.0, amp)
riser(195, 250, 0.26)      # into the title
riser(395, 430, 0.18)      # into the payoff

def braam(f, amp=0.42):
    """Low brass-ish stab: detuned saws, fast attack, filtered."""
    s, d = at(f), 2.2
    sig = (saw_stack(NOTE['D2'], .02, 7) + saw_stack(NOTE['A2'], .02, 5)*.6)
    sig = lp(sig, 900) * adsr(s, d, a=0.015, dec=0.5, sus=0.45, rel=1.5)
    place(sig, 0.0, amp)
braam(250, 0.40); braam(430, 0.30)

# ------------------------------------------------------------- mixdown
# Macro arrangement envelope: quiet, sparse open -> build -> peak at the
# payoff -> resolve. Previously the cue opened at full level, so it had
# nowhere to go.
arc = np.interp(t,
    [0, at(60), at(150), at(250), at(330), at(430), at(560), at(600), DUR],
    [0.30, 0.42,  0.58,   0.95,    0.78,    1.00,    0.95,    0.80,  0.55])
L *= arc; R *= arc
L *= duck; R *= duck
L = reverb(L, 0.40, 0.26); R = reverb(R, 0.42, 0.28)   # slightly decorrelated
# Mid/side: widen the sides, keep the low end mono so the sub stays solid.
M, Sd = (L+R)/2, (L-R)/2
b, a = signal.butter(2, 180/(SR/2), 'high')
Sd = signal.lfilter(b, a, Sd) * 1.9          # sides only above 180Hz
L, R = M + Sd, M - Sd
L, R = lp(L, 15000), lp(R, 15000)
peak = max(np.max(np.abs(L)), np.max(np.abs(R)))
L, R = L/peak*0.80, R/peak*0.80
L = np.tanh(L*1.18)/1.18; R = np.tanh(R*1.18)/1.18      # soft clip, glue
fi, fo = int(0.06*SR), int(2.0*SR)
for ch in (L, R):
    ch[:fi] *= np.linspace(0,1,fi); ch[-fo:] *= np.linspace(1,0,fo)**1.25

wavfile.write("score.wav", SR, (np.stack([L, R], axis=1)*32767).astype(np.int16))
print(f"score.wav: stereo {DUR}s, peak L {np.max(np.abs(L)):.2f} R {np.max(np.abs(R)):.2f}")

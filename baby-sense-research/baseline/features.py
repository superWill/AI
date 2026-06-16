#!/usr/bin/env python3
"""零依赖 MFCC 特征(仅 numpy/scipy)。

对每条音频提取 40 维 mel → 20 维 MFCC，在时间轴上做统计池化:
  [mean, std] of MFCC + [mean, std] of delta-MFCC  -> 80 维向量
外加少量谱统计(质心/带宽/过零率/能量)。这是文献里"手工特征"基线的标准做法,
作为 L3 公开数据天花板的保守估计(YAMNet embedding 通常更高,但结论方向一致)。
"""
import numpy as np
import soundfile as sf
from scipy.fft import dct
from scipy.signal import get_window, resample_poly

SR = 16000
N_FFT = 512
HOP = 160          # 10ms
WIN = 400          # 25ms
N_MELS = 40
N_MFCC = 20


def _hz_to_mel(f):
    return 2595.0 * np.log10(1.0 + f / 700.0)


def _mel_to_hz(m):
    return 700.0 * (10.0 ** (m / 2595.0) - 1.0)


def _mel_filterbank(sr=SR, n_fft=N_FFT, n_mels=N_MELS):
    low, high = _hz_to_mel(0), _hz_to_mel(sr / 2)
    mels = np.linspace(low, high, n_mels + 2)
    hz = _mel_to_hz(mels)
    bins = np.floor((n_fft + 1) * hz / sr).astype(int)
    fb = np.zeros((n_mels, n_fft // 2 + 1))
    for m in range(1, n_mels + 1):
        l, c, r = bins[m - 1], bins[m], bins[m + 1]
        if c == l:
            c += 1
        if r == c:
            r += 1
        for k in range(l, c):
            fb[m - 1, k] = (k - l) / max(c - l, 1)
        for k in range(c, r):
            fb[m - 1, k] = (r - k) / max(r - c, 1)
    return fb


_FB = _mel_filterbank()
_WINDOW = get_window("hann", WIN, fftbins=True)


def _frames(y):
    if len(y) < WIN:
        y = np.pad(y, (0, WIN - len(y)))
    n = 1 + (len(y) - WIN) // HOP
    idx = np.arange(WIN)[None, :] + HOP * np.arange(n)[:, None]
    return y[idx] * _WINDOW


def _logmel(y):
    fr = _frames(y)
    spec = np.abs(np.fft.rfft(fr, n=N_FFT, axis=1)) ** 2
    mel = spec @ _FB.T
    return np.log(mel + 1e-6)            # (T, n_mels)


def _delta(x):
    return np.diff(x, axis=0, prepend=x[:1])


def feature_vector(path: str) -> np.ndarray:
    y, sr = sf.read(path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    if sr != SR:                                    # 兼容 ESC-50(44.1k) 等
        from math import gcd
        g = gcd(int(sr), SR)
        y = resample_poly(y, SR // g, int(sr) // g).astype(np.float32)
    y = y - y.mean()
    y = np.append(y[0], y[1:] - 0.97 * y[:-1])     # pre-emphasis

    lm = _logmel(y)
    mfcc = dct(lm, type=2, axis=1, norm="ortho")[:, :N_MFCC]
    d = _delta(mfcc)

    # 谱统计
    fr = _frames(y)
    mag = np.abs(np.fft.rfft(fr, n=N_FFT, axis=1))
    freqs = np.fft.rfftfreq(N_FFT, 1 / SR)
    msum = mag.sum(axis=1) + 1e-9
    centroid = (mag @ freqs) / msum
    bandwidth = np.sqrt((mag * (freqs[None] - centroid[:, None]) ** 2).sum(axis=1) / msum)
    zcr = np.mean(np.abs(np.diff(np.sign(fr), axis=1)) > 0, axis=1)
    rms = np.sqrt((fr ** 2).mean(axis=1) + 1e-9)

    return np.concatenate([
        mfcc.mean(0), mfcc.std(0), d.mean(0), d.std(0),
        [centroid.mean(), centroid.std(), bandwidth.mean(),
         zcr.mean(), np.log(rms.mean() + 1e-9)],
    ]).astype(np.float32)


DIM = N_MFCC * 4 + 5

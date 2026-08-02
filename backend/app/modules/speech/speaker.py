"""Speaker Recognition, the classical-DSP way: MFCC statistics as a coarse
voice-print, compared by cosine similarity.

Real speaker-embedding models (pyannote.audio, resemblyzer, SpeechBrain's
ECAPA-TDNN) are all PyTorch — blocked here, same story as everywhere else in
this module. MFCCs won't match state-of-the-art diarization accuracy, but
they're a genuine, well-established acoustic feature for this task.

MFCC extraction is hand-rolled from numpy/scipy rather than pulled from
librosa: librosa depends on numba for its JIT-compiled inner loops, and
numba's compiled extension gets blocked by this host's Smart App Control
policy exactly like PyTorch (community-signed native code, not Microsoft's).
numpy/scipy's FFT and DCT are enough to implement the standard MFCC pipeline
directly — pre-emphasis, framing, FFT power spectrum, mel filterbank, log,
DCT.
"""

import tempfile
import wave
from pathlib import Path

import numpy as np
from scipy.fft import dct
from scipy.signal import resample

TARGET_SR = 16000
N_MFCC = 20
N_MELS = 26
FRAME_MS = 25
HOP_MS = 10
PRE_EMPHASIS = 0.97


def _read_wav(path: str) -> tuple[np.ndarray, int]:
    with wave.open(path, "rb") as wf:
        sr = wf.getframerate()
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        raw = wf.readframes(wf.getnframes())

    dtype = {1: np.uint8, 2: np.int16, 4: np.int32}.get(sampwidth)
    if dtype is None:
        raise ValueError(f"Unsupported WAV sample width: {sampwidth} bytes")

    samples = np.frombuffer(raw, dtype=dtype).astype(np.float32)
    if n_channels > 1:
        samples = samples.reshape(-1, n_channels).mean(axis=1)

    max_val = float(np.iinfo(dtype).max) if dtype != np.uint8 else 128.0
    samples = samples / max_val
    return samples, sr


def _hz_to_mel(hz: np.ndarray) -> np.ndarray:
    return 2595 * np.log10(1 + hz / 700)


def _mel_to_hz(mel: np.ndarray) -> np.ndarray:
    return 700 * (10 ** (mel / 2595) - 1)


def _mel_filterbank(n_fft: int, sr: int, n_mels: int) -> np.ndarray:
    mel_points = np.linspace(_hz_to_mel(np.array(0)), _hz_to_mel(np.array(sr / 2)), n_mels + 2)
    hz_points = _mel_to_hz(mel_points)
    bins = np.floor((n_fft + 1) * hz_points / sr).astype(int)

    fbank = np.zeros((n_mels, n_fft // 2 + 1))
    for m in range(1, n_mels + 1):
        left, center, right = bins[m - 1], bins[m], bins[m + 1]
        for k in range(left, center):
            if center > left:
                fbank[m - 1, k] = (k - left) / (center - left)
        for k in range(center, right):
            if right > center:
                fbank[m - 1, k] = (right - k) / (right - center)
    return fbank


def _mfcc(signal: np.ndarray, sr: int) -> np.ndarray:
    emphasized = np.append(signal[0], signal[1:] - PRE_EMPHASIS * signal[:-1])

    frame_len = int(sr * FRAME_MS / 1000)
    hop_len = int(sr * HOP_MS / 1000)
    n_frames = max(1, 1 + (len(emphasized) - frame_len) // hop_len)

    n_fft = 1
    while n_fft < frame_len:
        n_fft *= 2

    window = np.hamming(frame_len)
    fbank = _mel_filterbank(n_fft, sr, N_MELS)

    mfccs = []
    for i in range(n_frames):
        start = i * hop_len
        frame = emphasized[start : start + frame_len]
        if len(frame) < frame_len:
            frame = np.pad(frame, (0, frame_len - len(frame)))
        frame = frame * window

        power = (np.abs(np.fft.rfft(frame, n=n_fft)) ** 2) / n_fft
        mel_energy = fbank @ power
        mel_energy = np.where(mel_energy == 0, np.finfo(float).eps, mel_energy)
        log_mel = np.log(mel_energy)

        coeffs = dct(log_mel, type=2, norm="ortho")[:N_MFCC]
        mfccs.append(coeffs)

    return np.array(mfccs).T  # (n_mfcc, n_frames)


def _delta(mfcc: np.ndarray) -> np.ndarray:
    if mfcc.shape[1] < 2:
        return np.zeros_like(mfcc)
    return np.gradient(mfcc, axis=1)


def _embed(audio_bytes: bytes, suffix: str = ".wav") -> np.ndarray:
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(audio_bytes)
        tmp_path = tmp.name

    try:
        signal, sr = _read_wav(tmp_path)
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    if sr != TARGET_SR:
        signal = resample(signal, int(len(signal) * TARGET_SR / sr))
        sr = TARGET_SR

    mfcc = _mfcc(signal, sr)
    delta = _delta(mfcc)
    features = np.concatenate(
        [mfcc.mean(axis=1), mfcc.std(axis=1), delta.mean(axis=1), delta.std(axis=1)]
    )
    return features / (np.linalg.norm(features) or 1.0)


def compare(audio_a: bytes, audio_b: bytes) -> float:
    emb_a = _embed(audio_a)
    emb_b = _embed(audio_b)
    return float(np.dot(emb_a, emb_b))

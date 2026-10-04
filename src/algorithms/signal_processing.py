"""
Signal processing algorithms - sampling, quantization, FFT, modulation.

Pure functions with type hints, suitable for unit testing.
"""

from typing import Tuple, List, Optional, Dict, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class SampledSignal:
    """Represents a sampled signal."""
    samples: np.ndarray
    sample_rate: float
    bit_depth: int
    duration: float
    
    @property
    def nyquist_frequency(self) -> float:
        return self.sample_rate / 2.0
    
    @property
    def num_samples(self) -> int:
        return len(self.samples)


@dataclass
class Spectrum:
    """FFT spectrum data."""
    frequencies: np.ndarray
    magnitudes: np.ndarray
    phases: np.ndarray
    sample_rate: float


def sample_signal(signal: np.ndarray, original_rate: float, 
                  target_rate: float, bit_depth: int = 16) -> SampledSignal:
    """
    Sample a signal at a target rate.
    
    Args:
        signal: Input signal array
        original_rate: Original sampling rate in Hz
        target_rate: Target sampling rate in Hz
        bit_depth: Bit depth for quantization (8, 16, 24, 32)
        
    Returns:
        SampledSignal object
        
    Raises:
        ValueError: If target_rate > original_rate (aliasing warning)
    """
    if target_rate > original_rate:
        raise ValueError(f"Target rate {target_rate} > original rate {original_rate}. "
                        f"Use interpolation for upsampling.")
    
    # Anti-aliasing: low-pass filter at Nyquist of target rate
    nyquist = target_rate / 2.0
    from scipy import signal as scipy_signal
    sos = scipy_signal.butter(8, nyquist, fs=original_rate, output='sos')
    filtered = scipy_signal.sosfilt(sos, signal)
    
    # Decimate
    ratio = int(original_rate / target_rate)
    if ratio < 1:
        ratio = 1
    samples = filtered[::ratio]
    
    # Quantize to bit depth
    max_val = 2 ** (bit_depth - 1)
    samples = np.clip(samples, -1.0, 1.0)
    samples = np.round(samples * max_val) / max_val
    
    duration = len(signal) / original_rate
    
    return SampledSignal(
        samples=samples,
        sample_rate=target_rate,
        bit_depth=bit_depth,
        duration=duration
    )


def quantize_signal(signal: np.ndarray, num_levels: int, 
                    range_min: float = -1.0, range_max: float = 1.0,
                    method: str = "uniform") -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Quantize a signal to a specified number of levels.
    
    Args:
        signal: Input signal array
        num_levels: Number of quantization levels
        range_min: Minimum signal value
        range_max: Maximum signal value
        method: "uniform", "mu_law", or "a_law"
        
    Returns:
        Tuple of (quantized_signal, quantization_error, metadata)
    """
    if method == "uniform":
        levels = np.linspace(range_min, range_max, num_levels)
        indices = np.digitize(signal, levels) - 1
        indices = np.clip(indices, 0, num_levels - 1)
        quantized = levels[indices]
        
    elif method == "mu_law":
        # μ-law companding (μ = 255)
        mu = 255.0
        signal_norm = np.clip(signal / max(abs(range_min), abs(range_max)), -1.0, 1.0)
        companded = np.sign(signal_norm) * np.log(1 + mu * np.abs(signal_norm)) / np.log(1 + mu)
        levels = np.linspace(-1.0, 1.0, num_levels)
        indices = np.digitize(companded, levels) - 1
        indices = np.clip(indices, 0, num_levels - 1)
        # Expand
        expanded = levels[indices]
        quantized = np.sign(expanded) * ((1 + mu) ** np.abs(expanded) - 1) / mu
        
    elif method == "a_law":
        # A-law companding (A = 87.6)
        A = 87.6
        signal_norm = np.clip(signal / max(abs(range_min), abs(range_max)), -1.0, 1.0)
        companded = np.where(
            np.abs(signal_norm) < 1.0 / A,
            A * np.abs(signal_norm) / (1 + np.log(A)),
            (1 + np.log(A * np.abs(signal_norm))) / (1 + np.log(A))
        )
        companded = np.sign(signal_norm) * companded
        levels = np.linspace(-1.0, 1.0, num_levels)
        indices = np.digitize(companded, levels) - 1
        indices = np.clip(indices, 0, num_levels - 1)
        quantized = levels[indices]
    else:
        raise ValueError(f"Unknown quantization method: {method}")
    
    error = quantized - signal
    sqnr = 10 * np.log10(np.var(signal) / max(np.var(error), 1e-10))
    
    metadata = {
        "num_levels": num_levels,
        "method": method,
        "sqnr_db": float(sqnr),
        "max_error": float(np.max(np.abs(error))),
        "rms_error": float(np.sqrt(np.mean(error ** 2)))
    }
    
    return quantized, error, metadata


def compute_fft(signal: np.ndarray, sample_rate: float) -> Spectrum:
    """
    Compute FFT spectrum of a signal.
    
    Args:
        signal: Input signal array
        sample_rate: Sampling rate in Hz
        
    Returns:
        Spectrum object with frequencies, magnitudes, phases
    """
    n = len(signal)
    fft = np.fft.fft(signal)
    freqs = np.fft.fftfreq(n, 1.0 / sample_rate)
    
    # Only positive frequencies
    positive = freqs >= 0
    freqs = freqs[positive]
    magnitudes = np.abs(fft[positive]) / n
    phases = np.angle(fft[positive])
    
    return Spectrum(
        frequencies=freqs,
        magnitudes=magnitudes,
        phases=phases,
        sample_rate=sample_rate
    )


def compute_waterfall(signal: np.ndarray, sample_rate: float, 
                      window_size: int = 1024, hop_size: int = 512) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute spectrogram (waterfall) display.
    
    Args:
        signal: Input signal
        sample_rate: Sampling rate
        window_size: FFT window size
        hop_size: Hop size between windows
        
    Returns:
        Tuple of (times, frequencies, spectrogram)
    """
    from scipy import signal as scipy_signal
    frequencies, times, Sxx = scipy_signal.spectrogram(
        signal, fs=sample_rate, nperseg=window_size, noverlap=window_size - hop_size
    )
    return times, frequencies, 10 * np.log10(Sxx + 1e-10)


def modulate_am(signal: np.ndarray, carrier_freq: float, 
                sample_rate: float, modulation_index: float = 0.8) -> np.ndarray:
    """
    Amplitude modulation.
    
    Args:
        signal: Baseband signal (-1 to 1)
        carrier_freq: Carrier frequency in Hz
        sample_rate: Sampling rate in Hz
        modulation_index: Modulation index (0-1)
        
    Returns:
        AM modulated signal
    """
    t = np.arange(len(signal)) / sample_rate
    carrier = np.cos(2 * np.pi * carrier_freq * t)
    modulated = (1 + modulation_index * signal) * carrier
    return modulated


def demodulate_am(modulated: np.ndarray, carrier_freq: float, 
                  sample_rate: float) -> np.ndarray:
    """
    Envelope detection AM demodulation.
    
    Args:
        modulated: AM modulated signal
        carrier_freq: Carrier frequency in Hz
        sample_rate: Sampling rate in Hz
        
    Returns:
        Demodulated baseband signal
    """
    # Rectify
    rectified = np.abs(modulated)
    
    # Low-pass filter
    from scipy import signal as scipy_signal
    cutoff = carrier_freq * 0.5
    sos = scipy_signal.butter(4, cutoff, fs=sample_rate, output='sos')
    demodulated = scipy_signal.sosfilt(sos, rectified)
    
    # Remove DC offset and normalize
    demodulated = demodulated - np.mean(demodulated)
    max_val = np.max(np.abs(demodulated))
    if max_val > 0:
        demodulated = demodulated / max_val
    
    return demodulated


def modulate_fm(signal: np.ndarray, carrier_freq: float, 
                sample_rate: float, frequency_deviation: float = 1000.0) -> np.ndarray:
    """
    Frequency modulation.
    
    Args:
        signal: Baseband signal
        carrier_freq: Carrier frequency in Hz
        sample_rate: Sampling rate in Hz
        frequency_deviation: Frequency deviation in Hz
        
    Returns:
        FM modulated signal
    """
    t = np.arange(len(signal)) / sample_rate
    # Integrate signal for phase
    phase = 2 * np.pi * frequency_deviation * np.cumsum(signal) / sample_rate
    modulated = np.cos(2 * np.pi * carrier_freq * t + phase)
    return modulated


def demodulate_fm(modulated: np.ndarray, carrier_freq: float, 
                  sample_rate: float) -> np.ndarray:
    """
    FM demodulation using phase discriminator.
    
    Args:
        modulated: FM modulated signal
        carrier_freq: Carrier frequency in Hz
        sample_rate: Sampling rate in Hz
        
    Returns:
        Demodulated baseband signal
    """
    # Hilbert transform for analytic signal
    from scipy import signal as scipy_signal
    analytic = scipy_signal.hilbert(modulated)
    instantaneous_phase = np.unwrap(np.angle(analytic))
    
    # Differentiate to get instantaneous frequency
    demodulated = np.diff(instantaneous_phase) * sample_rate / (2 * np.pi)
    
    # Remove carrier frequency offset
    demodulated = demodulated - carrier_freq
    
    # Low-pass filter
    sos = scipy_signal.butter(4, carrier_freq * 0.5, fs=sample_rate, output='sos')
    demodulated = scipy_signal.sosfilt(sos, demodulated)
    
    # Normalize
    max_val = np.max(np.abs(demodulated))
    if max_val > 0:
        demodulated = demodulated / max_val
    
    return demodulated


def generate_test_signal(signal_type: str, duration: float, 
                         sample_rate: float, **kwargs) -> np.ndarray:
    """
    Generate test signals for simulation.
    
    Args:
        signal_type: "sine", "square", "sawtooth", "triangle", "noise", "chirp"
        duration: Duration in seconds
        sample_rate: Sampling rate in Hz
        **kwargs: Additional parameters (frequency, amplitude, etc.)
        
    Returns:
        Generated signal array
    """
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    freq = kwargs.get("frequency", 440.0)
    amplitude = kwargs.get("amplitude", 1.0)
    
    if signal_type == "sine":
        signal = amplitude * np.sin(2 * np.pi * freq * t)
    elif signal_type == "square":
        signal = amplitude * np.sign(np.sin(2 * np.pi * freq * t))
    elif signal_type == "sawtooth":
        from scipy import signal as scipy_signal
        signal = amplitude * scipy_signal.sawtooth(2 * np.pi * freq * t)
    elif signal_type == "triangle":
        from scipy import signal as scipy_signal
        signal = amplitude * scipy_signal.sawtooth(2 * np.pi * freq * t, width=0.5)
    elif signal_type == "noise":
        noise_type = kwargs.get("noise_type", "white")
        if noise_type == "white":
            signal = amplitude * np.random.randn(len(t))
        elif noise_type == "pink":
            # Pink noise: 1/f spectrum
            white = np.random.randn(len(t))
            fft = np.fft.fft(white)
            freqs = np.fft.fftfreq(len(t), 1.0 / sample_rate)
            fft = fft / np.sqrt(np.abs(freqs) + 1e-10)
            signal = amplitude * np.real(np.fft.ifft(fft))
            signal = signal / np.std(signal) * amplitude
        else:
            signal = amplitude * np.random.randn(len(t))
    elif signal_type == "chirp":
        from scipy import signal as scipy_signal
        f1 = kwargs.get("f1", 100.0)
        f2 = kwargs.get("f2", 1000.0)
        signal = amplitude * scipy_signal.chirp(t, f0=f1, f1=f2, t1=duration)
    else:
        raise ValueError(f"Unknown signal type: {signal_type}")
    
    return signal
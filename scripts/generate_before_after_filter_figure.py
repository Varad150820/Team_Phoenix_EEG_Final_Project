"""
Generate before/after filtering visualization comparing raw signal with filtered signal.
Shows time-domain and frequency-domain comparison of the 5-20 Hz bandpass filter.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
import mne

# Configuration
RAW_BIDS_PATH = Path(__file__).parent.parent / "milestone4" / "raw_bids" / "sub-1" / "ses-TestVisual" / "eeg"
RAW_FILE = RAW_BIDS_PATH / "sub-1_ses-TestVisual_task-PredError_eeg.vhdr"
OUTPUT_PATH = Path(__file__).parent.parent / "milestone5" / "reports" / "before_after_filter_visualization.png"

# Filter parameters (from pipeline config)
L_FREQ = 5
H_FREQ = 20
DOWNSAMPLE_RATE = 250
TIME_WINDOW = (10, 15)  # Show 5 seconds of signal starting at 10s

def load_and_prepare_data():
    """Load raw data and prepare for visualization."""
    print(f"Loading raw data from: {RAW_FILE}")
    raw = mne.io.read_raw_brainvision(RAW_FILE, preload=True, verbose=False)
    
    # Downsample to match pipeline
    print(f"Downsampling to {DOWNSAMPLE_RATE} Hz...")
    raw_downsampled = raw.copy().resample(DOWNSAMPLE_RATE, verbose=False)
    
    # Create copies for filtering
    raw_filtered = raw_downsampled.copy()
    
    # Apply filter
    print(f"Applying {L_FREQ}-{H_FREQ} Hz bandpass filter...")
    raw_filtered.filter(L_FREQ, H_FREQ, method='iir', verbose=False)
    
    return raw_downsampled, raw_filtered

def get_signal_section(raw, t_min, t_max, ch_idx=0):
    """Extract signal section and time vector."""
    start_idx = int(t_min * raw.info['sfreq'])
    end_idx = int(t_max * raw.info['sfreq'])
    signal = raw.get_data(picks=[ch_idx])[0, start_idx:end_idx]
    times = np.linspace(t_min, t_max, len(signal))
    return signal, times

def compute_psd(raw, fmax=50):
    """Compute power spectral density using Welch's method (faster)."""
    # Use only first 60 seconds to speed up computation
    duration = min(60, raw.times[-1])
    raw_subset = raw.copy().crop(tmax=duration)
    
    # Use Welch's method for faster PSD computation
    psd, freqs = mne.time_frequency.psd_array_welch(
        raw_subset.get_data(), 
        sfreq=raw.info['sfreq'],
        fmin=0, 
        fmax=fmax,
        n_jobs=1,
        verbose=False
    )
    # Average across channels
    psd_mean = psd.mean(axis=0)
    return freqs, psd_mean

def create_visualization(raw_original, raw_filtered):
    """Create 4-panel before/after filtering comparison."""
    print("Creating visualization...")
    
    fig = plt.figure(figsize=(16, 10))
    gs = gridspec.GridSpec(2, 2, figure=fig, hspace=0.35, wspace=0.3)
    
    # Channel to visualize (Cz - central)
    ch_idx = 0
    ch_name = raw_original.info['ch_names'][ch_idx]
    
    # Get signal sections (5 seconds)
    signal_raw, times = get_signal_section(raw_original, TIME_WINDOW[0], TIME_WINDOW[1], ch_idx)
    signal_filt, _ = get_signal_section(raw_filtered, TIME_WINDOW[0], TIME_WINDOW[1], ch_idx)
    
    # Compute PSDs
    freqs_raw, psd_raw = compute_psd(raw_original, fmax=50)
    freqs_filt, psd_filt = compute_psd(raw_filtered, fmax=50)
    
    # ========== Panel A: Raw Signal (Time Domain) ==========
    ax_a = fig.add_subplot(gs[0, 0])
    ax_a.plot(times, signal_raw, color='#d62728', linewidth=1.2, alpha=0.9)
    ax_a.fill_between(times, signal_raw, alpha=0.3, color='#d62728')
    ax_a.set_xlabel('Time (s)', fontsize=11, fontweight='bold')
    ax_a.set_ylabel('Amplitude (µV)', fontsize=11, fontweight='bold')
    ax_a.set_title('A) Raw Signal (Unfiltered)', fontsize=13, fontweight='bold', pad=10)
    ax_a.grid(True, alpha=0.3, linestyle='--')
    ax_a.spines['top'].set_visible(False)
    ax_a.spines['right'].set_visible(False)
    ax_a.text(0.02, 0.98, f'Channel: {ch_name}\nSample Rate: {raw_original.info["sfreq"]:.0f} Hz',
              transform=ax_a.transAxes, fontsize=10, verticalalignment='top',
              bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # ========== Panel B: Filtered Signal (Time Domain) ==========
    ax_b = fig.add_subplot(gs[0, 1])
    ax_b.plot(times, signal_filt, color='#2ca02c', linewidth=1.2, alpha=0.9)
    ax_b.fill_between(times, signal_filt, alpha=0.3, color='#2ca02c')
    ax_b.set_xlabel('Time (s)', fontsize=11, fontweight='bold')
    ax_b.set_ylabel('Amplitude (µV)', fontsize=11, fontweight='bold')
    ax_b.set_title(f'B) Filtered Signal ({L_FREQ}-{H_FREQ} Hz)', fontsize=13, fontweight='bold', pad=10)
    ax_b.grid(True, alpha=0.3, linestyle='--')
    ax_b.spines['top'].set_visible(False)
    ax_b.spines['right'].set_visible(False)
    ax_b.text(0.02, 0.98, f'Bandpass: {L_FREQ}-{H_FREQ} Hz\nMethod: IIR Butterworth',
              transform=ax_b.transAxes, fontsize=10, verticalalignment='top',
              bbox=dict(boxstyle='round', facecolor='lightgreen', alpha=0.5))
    
    # ========== Panel C: Raw PSD (Frequency Domain) ==========
    ax_c = fig.add_subplot(gs[1, 0])
    ax_c.semilogy(freqs_raw, psd_raw, color='#d62728', linewidth=2, label='Raw', alpha=0.8)
    ax_c.axvspan(L_FREQ, H_FREQ, alpha=0.2, color='yellow', label=f'Filter passband ({L_FREQ}-{H_FREQ} Hz)')
    ax_c.set_xlabel('Frequency (Hz)', fontsize=11, fontweight='bold')
    ax_c.set_ylabel('Power (µV²/Hz)', fontsize=11, fontweight='bold')
    ax_c.set_title('C) Power Spectral Density: Raw', fontsize=13, fontweight='bold', pad=10)
    ax_c.set_xlim([0, 50])
    ax_c.grid(True, which='both', alpha=0.3, linestyle='-', linewidth=0.5)
    ax_c.spines['top'].set_visible(False)
    ax_c.spines['right'].set_visible(False)
    ax_c.legend(loc='upper right', fontsize=10, framealpha=0.9)
    
    # ========== Panel D: Filtered PSD (Frequency Domain) ==========
    ax_d = fig.add_subplot(gs[1, 1])
    ax_d.semilogy(freqs_filt, psd_filt, color='#2ca02c', linewidth=2, label='Filtered', alpha=0.8)
    ax_d.axvspan(L_FREQ, H_FREQ, alpha=0.2, color='yellow', label=f'Filter passband ({L_FREQ}-{H_FREQ} Hz)')
    ax_d.set_xlabel('Frequency (Hz)', fontsize=11, fontweight='bold')
    ax_d.set_ylabel('Power (µV²/Hz)', fontsize=11, fontweight='bold')
    ax_d.set_title(f'D) Power Spectral Density: Filtered ({L_FREQ}-{H_FREQ} Hz)', fontsize=13, fontweight='bold', pad=10)
    ax_d.set_xlim([0, 50])
    ax_d.grid(True, which='both', alpha=0.3, linestyle='-', linewidth=0.5)
    ax_d.spines['top'].set_visible(False)
    ax_d.spines['right'].set_visible(False)
    ax_d.legend(loc='upper right', fontsize=10, framealpha=0.9)
    
    # Add overall title
    fig.suptitle('Signal Processing Impact: Before vs After Bandpass Filtering (5-20 Hz)',
                 fontsize=16, fontweight='bold', y=0.995)
    
    # Add description
    description = (
        'Left: Time-domain view of raw (red, top) vs filtered (green, middle) signal showing noise reduction.\n'
        'Right: Frequency-domain view showing selective attenuation of out-of-band frequencies. '
        'Yellow region = passband (preserved frequencies).'
    )
    fig.text(0.5, 0.01, description, ha='center', fontsize=10, style='italic',
             bbox=dict(boxstyle='round', facecolor='lightgray', alpha=0.3, pad=0.8))
    
    return fig

def main():
    """Main execution."""
    try:
        # Load and prepare data
        raw_original, raw_filtered = load_and_prepare_data()
        
        # Create visualization
        fig = create_visualization(raw_original, raw_filtered)
        
        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Save figure
        fig.savefig(OUTPUT_PATH, dpi=220, bbox_inches='tight', facecolor='white')
        print(f"✓ Saved: {OUTPUT_PATH}")
        
        plt.close(fig)
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()

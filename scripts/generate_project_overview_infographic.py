"""
Generate comprehensive project overview infographic showing:
- Project objectives
- Data flow and statistics
- All processing stages
- Key outputs and results
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from matplotlib.patches import Rectangle
import numpy as np
from pathlib import Path

OUTPUT_PATH = Path(__file__).parent.parent / "milestone5" / "reports" / "project_overview_infographic.png"

def create_project_overview():
    """Create comprehensive project overview infographic with clean grid layout."""
    
    fig = plt.figure(figsize=(22, 14))
    ax = fig.add_subplot(111)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')
    
    # Color scheme
    blue = '#1f77b4'
    orange = '#ff7f0e'
    green = '#2ca02c'
    red = '#d62728'
    cyan = '#17becf'
    
    # ========== TITLE ==========
    ax.text(50, 97.5, 'EEG Prediction Error Response Analysis Pipeline', 
            ha='center', va='top', fontsize=26, fontweight='bold')
    
    # ========== TOP LEFT: 4 BOXES (2x2 GRID) ==========
    # Box 1: DATA SOURCES
    box1 = FancyBboxPatch((2, 83), 15, 10, boxstyle="round,pad=0.2", 
                          edgecolor=blue, facecolor='#e7f0ff', linewidth=2.2)
    ax.add_patch(box1)
    ax.text(9.5, 91.5, 'DATA SOURCES', ha='center', fontweight='bold', fontsize=10.5, color=blue)
    ax.text(9.5, 89.5, 'ds003846 Dataset', ha='center', fontsize=8.5)
    ax.text(9.5, 88.2, '60 Recordings', ha='center', fontsize=8.5)
    ax.text(9.5, 86.9, '19 Subjects', ha='center', fontsize=8.5)
    ax.text(9.5, 85.6, '64 EEG Channels', ha='center', fontsize=8.5)
    ax.text(9.5, 84.3, '3 Sessions', ha='center', fontsize=8)
    
    # Box 2: TASK DESIGN
    box2 = FancyBboxPatch((19, 83), 15, 10, boxstyle="round,pad=0.2",
                          edgecolor=orange, facecolor='#fff3e7', linewidth=2.2)
    ax.add_patch(box2)
    ax.text(26.5, 91.5, 'TASK DESIGN', ha='center', fontweight='bold', fontsize=10.5, color=orange)
    ax.text(26.5, 89.5, 'Prediction-Error', ha='center', fontsize=8.5)
    ax.text(26.5, 88.2, 'Oddball Paradigm', ha='center', fontsize=8.5)
    ax.text(26.5, 86.9, '~200 trials/session', ha='center', fontsize=8.5)
    ax.text(26.5, 85.6, 'Match vs Mismatch', ha='center', fontsize=8)
    
    # Box 3: PREPROCESSING PIPELINE (vertical list)
    box3 = FancyBboxPatch((2, 68), 15, 14, boxstyle="round,pad=0.2",
                          edgecolor=green, facecolor='#e8f5e9', linewidth=2.2)
    ax.add_patch(box3)
    ax.text(9.5, 80.8, 'PREPROCESSING', ha='center', fontweight='bold', fontsize=9.5, color=green)
    ax.text(9.5, 80, 'PIPELINE', ha='center', fontweight='bold', fontsize=9.5, color=green)
    
    pipeline_items = [
        ('1. Load', '1000 Hz'),
        ('2. Filter', '5-20 Hz'),
        ('3. Resample', '250 Hz'),
        ('4. Bad Ch', '5.0σ'),
        ('5. ICA', '12 comp'),
        ('6. Epochs', '-100/+1s'),
        ('7. Reject', 'AutoReject'),
        ('8. Metrics', 'Evoked')
    ]
    
    pipeline_y = 78.5
    for stage, param in pipeline_items:
        ax.text(4, pipeline_y, stage, ha='left', fontsize=7.5, fontweight='bold', color=green)
        ax.text(13.5, pipeline_y, param, ha='right', fontsize=7.5, color='#666')
        pipeline_y -= 1.4
    
    # Box 4: (empty or summary)
    box4 = FancyBboxPatch((19, 68), 15, 14, boxstyle="round,pad=0.2",
                          edgecolor='#999', facecolor='#f9f9f9', linewidth=1.5)
    ax.add_patch(box4)
    ax.text(26.5, 80.5, 'KEY CONFIG', ha='center', fontweight='bold', fontsize=9.5, color='#333')
    
    config_items = [
        'Filter: 5-20 Hz',
        'Resample: 250 Hz',
        'ICA: Infomax',
        'Components: 12',
        'Baseline: -100-0 ms',
        'Epoch: -100 to +1000',
        'Rejection: AutoReject',
        'Outlier: 2.5×MAD'
    ]
    
    config_y = 79
    for item in config_items:
        ax.text(26.5, config_y, item, ha='center', fontsize=7.5, color='#444')
        config_y -= 1.32
    
    # ========== TOP RIGHT: 2 BOXES ==========
    # Box 5: QUALITY METRICS
    box5 = FancyBboxPatch((38, 73), 28, 20, boxstyle="round,pad=0.2",
                          edgecolor=red, facecolor='#ffe7e0', linewidth=2.2)
    ax.add_patch(box5)
    ax.text(52, 91.8, 'QUALITY METRICS', ha='center', fontweight='bold', fontsize=11.5, color=red)
    
    quality_items = [
        'Recordings Processed: 60 → 59',
        'Subjects Processed: 19 → 18',
        'Bad Channels Detected: 53 recordings',
        '• 8 (2 recordings)',
        'Mean Epochs/Subject: ~180',
        'Mean Artifact Rejection: ~15%',
        'ICA Components Removed: 3-5/rec',
        '• Outlier Subjects Excluded: 1'
    ]
    
    quality_y = 89.5
    for i, item in enumerate(quality_items):
        if i in [3, 7]:
            color = red
            weight = 'bold'
        else:
            color = '#333'
            weight = 'normal'
        ax.text(40, quality_y, item, ha='left', fontsize=8, color=color, fontweight=weight)
        quality_y -= 1.95
    
    # Box 6: GRAND AVERAGE ANALYSIS
    box6 = FancyBboxPatch((68, 73), 30, 20, boxstyle="round,pad=0.2",
                          edgecolor=cyan, facecolor='#e0f7ff', linewidth=2.2)
    ax.add_patch(box6)
    ax.text(83, 91.8, 'GRAND AVERAGE ANALYSIS', ha='center', fontweight='bold', fontsize=11.5, color=cyan)
    
    ga_items = [
        '✓ Match ERP (all sessions)',
        '✓ Mismatch ERP (all sessions)',
        '✓ TestVisual Match/Mismatch',
        '✓ TestVibro Match/Mismatch',
        '✓ TestEMS Match/Mismatch',
        '',
        'KEY FINDINGS:',
        '✓ Mismatch > Match (150-300ms)',
        '✓ Prediction error robust',
        '✓ All stimulus modalities',
        '✓ Consistent across subjects'
    ]
    
    ga_y = 89.5
    for item in ga_items:
        if item == '':
            ga_y -= 0.6
        elif 'KEY' in item:
            ax.text(83, ga_y, item, ha='center', fontsize=8.5, fontweight='bold', color=cyan)
            ga_y -= 1.3
        else:
            ax.text(83, ga_y, item, ha='center', fontsize=7.8, color='#333')
            ga_y -= 1.3
    
    # ========== MIDDLE: OUTPUTS & DELIVERABLES ==========
    ax.text(50, 67, 'OUTPUTS & DELIVERABLES', ha='center', fontweight='bold', 
            fontsize=11.5, bbox=dict(boxstyle='round,pad=0.5', facecolor='#fff9e6', 
            edgecolor='#b8860b', linewidth=2))
    
    outputs = [
        ('Raw FIF Files', '59 rec.\n(~236 MB)'),
        ('Grand Average\nFiles', '6 formats\nHarmonized'),
        ('Statistical\nSummary', '20 metrics\nCSV format'),
        ('ERP\nVisualizations', '3-panel\nComparison'),
        ('Pipeline\nInfographic', 'Flow\nDiagram'),
        ('Full HTML\nReport', 'MNE Native\nInteractive')
    ]
    
    output_positions_x = [9, 21, 33, 50, 67, 83]
    for i, (x_pos, (title, desc)) in enumerate(zip(output_positions_x, outputs)):
        box_out = FancyBboxPatch((x_pos-6.5, 48), 13, 15.5, boxstyle="round,pad=0.15",
                               edgecolor='#666', facecolor='#fafafa', linewidth=1.5)
        ax.add_patch(box_out)
        ax.text(x_pos, 61.5, title, ha='center', fontsize=8.5, fontweight='bold', color='#333')
        ax.text(x_pos, 53, desc, ha='center', fontsize=7, color='#555')
    
    # ========== BOTTOM: PROJECT STATUS & NEXT STEPS ==========
    box_status = FancyBboxPatch((2, 2), 96, 43.5, boxstyle="round,pad=0.25",
                               edgecolor='#333', facecolor='#f5f5f5', linewidth=2.2)
    ax.add_patch(box_status)
    
    ax.text(50, 44, 'PROJECT STATUS & NEXT STEPS', ha='center', fontweight='bold', 
            fontsize=11.5, color='#333')
    
    # Status items with proper spacing
    status_items = [
        ('✓', 'DATA LOADING', 'Raw BIDS data imported and validated', 42.5),
        ('✓', 'PREPROCESSING', 'All 8 stages: filter, resample, ICA, rejection', 39.5),
        ('✓', 'ARTIFACT REMOVAL', 'ICA (12 comp) + AutoReject optimized', 36.5),
        ('✓', 'GRAND AVERAGES', 'Group-level ERPs computed with harmonization', 33.5),
        ('✓', 'QUALITY CONTROL', 'Outlier subjects identified and excluded', 30.5),
        ('✓', 'VISUALIZATIONS', 'ERP plots + filter demo + overview infographics', 27.5),
        ('✓', 'DOCUMENTATION', 'Parameter intent report + pipeline flow', 24.5),
        ('→', 'NEXT STEP', 'Export to GitHub + Share with Professor (via index.html)', 21.5),
    ]
    
    for check, title, description, y_pos in status_items:
        if check == '→':
            color = orange
            weight = 'bold'
        else:
            color = green
            weight = 'normal'
        
        # Check mark or arrow
        ax.text(5, y_pos, check, fontsize=12, fontweight=weight, color=color)
        # Title
        ax.text(8, y_pos, title, fontsize=8.5, fontweight='bold', color=color)
        # Description
        ax.text(22, y_pos, description, fontsize=8, ha='left', color='#333')
    
    # Bottom parameter line
    ax.text(50, 2, 'Key Configuration: 5-20 Hz IIR Butterworth | 250 Hz Resample | Infomax ICA (12 components) | AutoReject | MAD-based Outlier (2.5×robust_scale)',
            ha='center', fontsize=7.5, style='italic', color='#666')
    
    return fig

def main():
    """Main execution."""
    try:
        print("Creating comprehensive project overview...")
        fig = create_project_overview()
        
        # Ensure output directory exists
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        
        # Save figure
        fig.savefig(OUTPUT_PATH, dpi=160, bbox_inches='tight', facecolor='white')
        print(f"✓ Saved: {OUTPUT_PATH}")
        
        plt.close(fig)
        
    except Exception as e:
        print(f"Error: {e}")
        raise

if __name__ == "__main__":
    main()

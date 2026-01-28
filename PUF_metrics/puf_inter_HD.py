#!/usr/bin/env python3
"""
SRAM PUF Inter-Hamming Distance 

Measures uniqueness between Card 1 and Card 2
"""

import os
import numpy as np
import matplotlib.pyplot as plt


def load_sram_file(filepath):
    """Load SRAM hex dump and convert to binary array."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    hex_str = content.replace(' ', '').replace('\r', '').replace('\n', '').replace('.', '')
    
    bytes_list = []
    for i in range(0, len(hex_str) - 1, 2):
        try:
            byte = int(hex_str[i:i+2], 16)
            bytes_list.append(byte)
        except ValueError:
            continue
    
    bits = []
    for byte in bytes_list:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    
    return np.array(bits, dtype=np.uint8)


def load_all_samples(directory):
    """Load all SRAM samples from a directory."""
    samples = []
    for filename in sorted(os.listdir(directory), key=lambda x: int(x) if x.isdigit() else 0):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and not filename.endswith('.py'):
            try:
                bits = load_sram_file(filepath)
                if len(bits) > 0:
                    samples.append(bits)
            except:
                pass
    return samples


def hamming_distance(bits1, bits2):
    """Compute fractional Hamming Distance."""
    min_len = min(len(bits1), len(bits2))
    return np.sum(bits1[:min_len] != bits2[:min_len]) / min_len


def compute_inter_hd(samples1, samples2):
    """Compute Inter-HD: all pairwise distances between two devices."""
    distances = []
    for s1 in samples1:
        for s2 in samples2:
            distances.append(hamming_distance(s1, s2))
    return np.array(distances)


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(parent_dir, "SRAM_collected_data")
    card1_dir = os.path.join(data_dir, "card1")
    card2_dir = os.path.join(data_dir, "card2")
    
    print("=" * 50)
    print("Inter-Hamming Distance Analysis")
    print("=" * 50)
    
    # Load samples
    print("\nLoading samples...")
    card1_samples = load_all_samples(card1_dir)
    card2_samples = load_all_samples(card2_dir)
    print(f"  Card 1: {len(card1_samples)} samples")
    print(f"  Card 2: {len(card2_samples)} samples")
    
    # Normalize lengths
    min_len = min(min(len(s) for s in card1_samples), min(len(s) for s in card2_samples))
    card1_samples = [s[:min_len] for s in card1_samples]
    card2_samples = [s[:min_len] for s in card2_samples]
    
    # Compute Inter-HD
    print("\nComputing Inter-HD...")
    inter_hd = compute_inter_hd(card1_samples, card2_samples)
    
    print(f"\n  Mean Inter-HD: {np.mean(inter_hd):.4f}")
    print(f"  Std Dev:       {np.std(inter_hd):.4f}")
    print(f"  Min:           {np.min(inter_hd):.4f}")
    print(f"  Max:           {np.max(inter_hd):.4f}")
    print(f"  Ideal:         0.5")
    
    # Generate figure
    print("\nGenerating figure...")
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.hist(inter_hd, bins=25, alpha=0.8, color='green', edgecolor='darkgreen')
    ax.axvline(x=0.5, color='red', linestyle='--', linewidth=2, label='Ideal (0.5)')
    ax.axvline(x=np.mean(inter_hd), color='blue', linestyle='-', linewidth=2, 
               label=f'Mean ({np.mean(inter_hd):.4f})')
    
    ax.set_xlabel('Inter-Hamming Distance', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title(f'Inter-HD Distribution (Uniqueness)\nMean = {np.mean(inter_hd):.4f}, Ideal = 0.5', fontsize=14)
    ax.legend(loc='upper left')
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    output_path = os.path.join(script_dir, 'inter_hd_.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nSaved: {output_path}")
    plt.close()

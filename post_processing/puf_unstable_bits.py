#!/usr/bin/env python3
"""
SRAM PUF Analysis - Unstable Bits Method

Uses only bit positions that flip between samples (unstable bits)
This approach is the most useful for PUF as they have higher entropy
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from itertools import combinations


def load_sram_file(filepath):
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


def find_unstable_bits(samples, threshold=0.1):
    samples_array = np.array(samples)
    mean_per_bit = np.mean(samples_array, axis=0)
    unstable_mask = (mean_per_bit > threshold) & (mean_per_bit < (1 - threshold))
    unstable_indices = np.where(unstable_mask)[0]
    return unstable_indices, mean_per_bit


def extract_unstable_bits(samples, unstable_indices):
    return [s[unstable_indices] for s in samples]


def hamming_weight(bits):
    return np.sum(bits) / len(bits) if len(bits) > 0 else 0

def hamming_distance(bits1, bits2):
    min_len = min(len(bits1), len(bits2))
    if min_len == 0:
        return 0
    return np.sum(bits1[:min_len] != bits2[:min_len]) / min_len

def compute_intra_hd(samples):
    distances = []
    for i, j in combinations(range(len(samples)), 2):
        distances.append(hamming_distance(samples[i], samples[j]))
    return np.array(distances)


def create_comparison_figure(orig_samples, unstable_samples, card_name, 
                            num_unstable, total_bits, output_dir):
    hw_orig = [hamming_weight(s) for s in orig_samples]
    hw_unstable = [hamming_weight(s) for s in unstable_samples]
    intra_orig = compute_intra_hd(orig_samples)
    intra_unstable = compute_intra_hd(unstable_samples)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    x = np.arange(1, len(hw_orig) + 1)
    
    axes[0].bar(x, hw_orig, color='steelblue', alpha=0.8)
    axes[0].axhline(y=0.5, color='green', linestyle='--', linewidth=2, label='Ideal (0.5)')
    axes[0].axhline(y=np.mean(hw_orig), color='red', linestyle='-', linewidth=2, 
                    label=f'Mean ({np.mean(hw_orig):.4f})')
    axes[0].set_xlabel('Sample #')
    axes[0].set_ylabel('Hamming Weight')
    axes[0].set_title(f'{card_name} - ALL BITS ({total_bits} bits)\nMean HW = {np.mean(hw_orig):.4f}')
    axes[0].set_ylim(0, 0.7)
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    axes[1].bar(x, hw_unstable, color='coral', alpha=0.8)
    axes[1].axhline(y=0.5, color='green', linestyle='--', linewidth=2, label='Ideal (0.5)')
    axes[1].axhline(y=np.mean(hw_unstable), color='red', linestyle='-', linewidth=2,
                    label=f'Mean ({np.mean(hw_unstable):.4f})')
    axes[1].set_xlabel('Sample #')
    axes[1].set_ylabel('Hamming Weight')
    axes[1].set_title(f'{card_name} - UNSTABLE BITS ONLY ({num_unstable} bits)\nMean HW = {np.mean(hw_unstable):.4f}')
    axes[1].set_ylim(0, 0.7)
    axes[1].legend()
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    hw_path = os.path.join(output_dir, f'{card_name.lower().replace(" ", "_")}_unstable_hw.png')
    plt.savefig(hw_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {hw_path}")
    plt.close()
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    axes[0].hist(intra_orig, bins=25, color='steelblue', alpha=0.8)
    axes[0].axvline(x=np.mean(intra_orig), color='red', linestyle='-', linewidth=2,
                    label=f'Mean ({np.mean(intra_orig):.4f})')
    axes[0].set_xlabel('Intra-HD')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title(f'{card_name} - ALL BITS\nMean Intra-HD = {np.mean(intra_orig):.4f}')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    axes[1].hist(intra_unstable, bins=25, color='coral', alpha=0.8)
    axes[1].axvline(x=np.mean(intra_unstable), color='red', linestyle='-', linewidth=2,
                    label=f'Mean ({np.mean(intra_unstable):.4f})')
    axes[1].set_xlabel('Intra-HD')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title(f'{card_name} - UNSTABLE BITS ONLY\nMean Intra-HD = {np.mean(intra_unstable):.4f}')
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    intra_path = os.path.join(output_dir, f'{card_name.lower().replace(" ", "_")}_unstable_intra.png')
    plt.savefig(intra_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {intra_path}")
    plt.close()
    
    return {
        'hw_orig': np.mean(hw_orig),
        'hw_unstable': np.mean(hw_unstable),
        'intra_orig': np.mean(intra_orig),
        'intra_unstable': np.mean(intra_unstable)
    }


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(parent_dir, "SRAM_collected_data")
    card1_dir = os.path.join(data_dir, "card1")
    card2_dir = os.path.join(data_dir, "card2")
    
    print("=" * 60)
    print("SRAM PUF Analysis - Unstable Bits Method")
    print("=" * 60)
    
    print("\nLoading Card 1...")
    card1_samples = load_all_samples(card1_dir)
    print(f"  Loaded {len(card1_samples)} samples")
    
    print("Loading Card 2...")
    card2_samples = load_all_samples(card2_dir)
    print(f"  Loaded {len(card2_samples)} samples")
    
    min_len = min(min(len(s) for s in card1_samples), min(len(s) for s in card2_samples))
    card1_samples = [s[:min_len] for s in card1_samples]
    card2_samples = [s[:min_len] for s in card2_samples]
    print(f"\nTotal bits per sample: {min_len}")
    
    print("\nFinding unstable bits...")
    unstable1, means1 = find_unstable_bits(card1_samples, threshold=0.1)
    unstable2, means2 = find_unstable_bits(card2_samples, threshold=0.1)
    
    print(f"  Card 1: {len(unstable1)} unstable bits ({100*len(unstable1)/min_len:.1f}%)")
    print(f"  Card 2: {len(unstable2)} unstable bits ({100*len(unstable2)/min_len:.1f}%)")
    
    card1_unstable = extract_unstable_bits(card1_samples, unstable1)
    card2_unstable = extract_unstable_bits(card2_samples, unstable2)
    
    print("\nGenerating comparison figures...")
    results1 = create_comparison_figure(
        card1_samples, card1_unstable, "Card 1",
        len(unstable1), min_len, script_dir
    )
    results2 = create_comparison_figure(
        card2_samples, card2_unstable, "Card 2",
        len(unstable2), min_len, script_dir
    )
    
    print("\n" + "=" * 60)
    print("SUMMARY - All Bits vs Unstable Bits Only")
    print("=" * 60)
    
    print(f"""
Card 1 ({len(unstable1)} unstable bits out of {min_len}):
  Hamming Weight: {results1['hw_orig']:.4f} -> {results1['hw_unstable']:.4f}  (Target: 0.5)
  Intra-HD:       {results1['intra_orig']:.4f} -> {results1['intra_unstable']:.4f}  (Target: 0)

Card 2 ({len(unstable2)} unstable bits out of {min_len}):
  Hamming Weight: {results2['hw_orig']:.4f} -> {results2['hw_unstable']:.4f}  (Target: 0.5)
  Intra-HD:       {results2['intra_orig']:.4f} -> {results2['intra_unstable']:.4f}  (Target: 0)
""")
    
    print("4 comparison figures saved!")

#!/usr/bin/env python3
"""
SRAM PUF Bit Balance (Bit Weight) Analysis

Computes fraction of 1s overall and per bit position
Reports global 1 rate and per bit 1 rate distribution
"""

import os
import numpy as np
import matplotlib.pyplot as plt


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


def analyze_bit_balance(samples, card_name, output_dir):
    samples_array = np.array(samples)
    num_samples, num_bits = samples_array.shape
    
    global_1_rate = np.mean(samples_array)
    per_bit_1_rate = np.mean(samples_array, axis=0)
    
    print(f"\n{card_name}:")
    print(f"  Total samples: {num_samples}")
    print(f"  Total bits per sample: {num_bits}")
    print(f"  Global 1-rate: {global_1_rate:.4f} (Ideal: 0.5)")
    print(f"  Per-bit 1-rate - Mean: {np.mean(per_bit_1_rate):.4f}")
    print(f"  Per-bit 1-rate - Std:  {np.std(per_bit_1_rate):.4f}")
    print(f"  Per-bit 1-rate - Min:  {np.min(per_bit_1_rate):.4f}")
    print(f"  Per-bit 1-rate - Max:  {np.max(per_bit_1_rate):.4f}")
    
    bits_always_0 = np.sum(per_bit_1_rate == 0)
    bits_always_1 = np.sum(per_bit_1_rate == 1)
    bits_balanced = np.sum((per_bit_1_rate > 0.4) & (per_bit_1_rate < 0.6))
    
    print(f"  Bits always 0: {bits_always_0} ({100*bits_always_0/num_bits:.1f}%)")
    print(f"  Bits always 1: {bits_always_1} ({100*bits_always_1/num_bits:.1f}%)")
    print(f"  Bits balanced (0.4-0.6): {bits_balanced} ({100*bits_balanced/num_bits:.1f}%)")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    axes[0].hist(per_bit_1_rate, bins=50, color='steelblue', alpha=0.8, edgecolor='navy')
    axes[0].axvline(x=0.5, color='green', linestyle='--', linewidth=2, label='Ideal (0.5)')
    axes[0].axvline(x=global_1_rate, color='red', linestyle='-', linewidth=2, label=f'Global mean ({global_1_rate:.4f})')
    axes[0].set_xlabel('Per-bit 1-rate')
    axes[0].set_ylabel('Number of bits')
    axes[0].set_title(f'{card_name} - Per-bit 1-rate Distribution\n(How often each bit position is 1 across all boots)')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    sample_indices = np.linspace(0, num_bits-1, min(500, num_bits), dtype=int)
    axes[1].scatter(sample_indices, per_bit_1_rate[sample_indices], alpha=0.5, s=2, c='steelblue')
    axes[1].axhline(y=0.5, color='green', linestyle='--', linewidth=2, label='Ideal (0.5)')
    axes[1].axhline(y=global_1_rate, color='red', linestyle='-', linewidth=2, label=f'Global mean ({global_1_rate:.4f})')
    axes[1].set_xlabel('Bit position (sampled)')
    axes[1].set_ylabel('1-rate')
    axes[1].set_title(f'{card_name} - Per-bit 1-rate by Position\n(Spatial distribution of bit bias)')
    axes[1].set_ylim(-0.05, 1.05)
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, f'{card_name.lower().replace(" ", "_")}_bit_balance.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Saved: {output_path}")
    plt.close()
    
    return {
        'global_1_rate': global_1_rate,
        'per_bit_1_rate': per_bit_1_rate,
        'bits_always_0': bits_always_0,
        'bits_always_1': bits_always_1,
        'bits_balanced': bits_balanced
    }


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(parent_dir, "SRAM_collected_data")
    card1_dir = os.path.join(data_dir, "card1")
    card2_dir = os.path.join(data_dir, "card2")
    
    print("=" * 60)
    print("SRAM PUF Bit Balance (Bit Weight) Analysis")
    print("=" * 60)
    
    print("\nLoading samples...")
    card1_samples = load_all_samples(card1_dir)
    card2_samples = load_all_samples(card2_dir)
    
    min_len = min(min(len(s) for s in card1_samples), min(len(s) for s in card2_samples))
    card1_samples = [s[:min_len] for s in card1_samples]
    card2_samples = [s[:min_len] for s in card2_samples]
    
    results1 = analyze_bit_balance(card1_samples, "Card 1", script_dir)
    results2 = analyze_bit_balance(card2_samples, "Card 2", script_dir)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"""
                        Card 1      Card 2      Ideal
Global 1-rate:          {results1['global_1_rate']:.4f}      {results2['global_1_rate']:.4f}      0.5000
Bits always 0:          {results1['bits_always_0']:5d}       {results2['bits_always_0']:5d}       0
Bits always 1:          {results1['bits_always_1']:5d}       {results2['bits_always_1']:5d}       0
Bits balanced (0.4-0.6):{results1['bits_balanced']:5d}       {results2['bits_balanced']:5d}       All
""")

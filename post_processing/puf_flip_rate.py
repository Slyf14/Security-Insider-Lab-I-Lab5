#!/usr/bin/env python3
"""
SRAM PUF Per-bit Stability (Flip Rate) Analysis

For each bit position, computes fraction of boots that differ from that bit's majority value.
Creates a stable bit mask for reliable PUF response extraction
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


def analyze_flip_rate(samples, card_name, output_dir):
    samples_array = np.array(samples)
    num_samples, num_bits = samples_array.shape
    
    per_bit_mean = np.mean(samples_array, axis=0)
    majority_value = (per_bit_mean >= 0.5).astype(np.uint8)
    
    flip_count = np.zeros(num_bits)
    for sample in samples_array:
        flip_count += (sample != majority_value)
    
    flip_rate = flip_count / num_samples
    
    print(f"\n{card_name}:")
    print(f"  Total samples: {num_samples}")
    print(f"  Total bits: {num_bits}")
    print(f"  Flip rate - Mean: {np.mean(flip_rate):.4f}")
    print(f"  Flip rate - Std:  {np.std(flip_rate):.4f}")
    print(f"  Flip rate - Max:  {np.max(flip_rate):.4f}")
    
    perfectly_stable = np.sum(flip_rate == 0)
    very_stable = np.sum(flip_rate < 0.05)
    stable = np.sum(flip_rate < 0.1)
    unstable = np.sum(flip_rate >= 0.1)
    
    print(f"  Perfectly stable (0%):  {perfectly_stable} ({100*perfectly_stable/num_bits:.1f}%)")
    print(f"  Very stable (<5%):      {very_stable} ({100*very_stable/num_bits:.1f}%)")
    print(f"  Stable (<10%):          {stable} ({100*stable/num_bits:.1f}%)")
    print(f"  Unstable (>=10%):       {unstable} ({100*unstable/num_bits:.1f}%)")
    
    stable_mask = flip_rate < 0.1
    mask_path = os.path.join(output_dir, f'{card_name.lower().replace(" ", "_")}_stable_mask.npy')
    np.save(mask_path, stable_mask)
    print(f"  Stable mask saved: {mask_path}")
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    axes[0].hist(flip_rate, bins=50, color='coral', alpha=0.8, edgecolor='darkred')
    axes[0].axvline(x=0.1, color='green', linestyle='--', linewidth=2, label='Stability threshold (10%)')
    axes[0].axvline(x=np.mean(flip_rate), color='blue', linestyle='-', linewidth=2, label=f'Mean ({np.mean(flip_rate):.4f})')
    axes[0].set_xlabel('Flip rate')
    axes[0].set_ylabel('Number of bits')
    axes[0].set_title(f'{card_name} - Flip Rate Distribution\n(How often each bit differs from its majority value)')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    sample_indices = np.linspace(0, num_bits-1, min(500, num_bits), dtype=int)
    colors = ['green' if flip_rate[i] < 0.1 else 'red' for i in sample_indices]
    axes[1].scatter(sample_indices, flip_rate[sample_indices], alpha=0.5, s=3, c=colors)
    axes[1].axhline(y=0.1, color='orange', linestyle='--', linewidth=2, label='Threshold (10%)')
    axes[1].set_xlabel('Bit position (sampled)')
    axes[1].set_ylabel('Flip rate')
    axes[1].set_title(f'{card_name} - Per-bit Flip Rate\n(Green = stable, Red = unstable)')
    axes[1].set_ylim(-0.02, 0.55)
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, f'{card_name.lower().replace(" ", "_")}_flip_rate.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Saved: {output_path}")
    plt.close()
    
    return {
        'flip_rate': flip_rate,
        'stable_mask': stable_mask,
        'majority_value': majority_value,
        'perfectly_stable': perfectly_stable,
        'very_stable': very_stable,
        'stable': stable,
        'unstable': unstable
    }


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(parent_dir, "SRAM_collected_data")
    card1_dir = os.path.join(data_dir, "card1")
    card2_dir = os.path.join(data_dir, "card2")
    
    print("=" * 60)
    print("SRAM PUF Per-bit Stability (Flip Rate) Analysis")
    print("=" * 60)
    
    print("\nLoading samples...")
    card1_samples = load_all_samples(card1_dir)
    card2_samples = load_all_samples(card2_dir)
    
    min_len = min(min(len(s) for s in card1_samples), min(len(s) for s in card2_samples))
    card1_samples = [s[:min_len] for s in card1_samples]
    card2_samples = [s[:min_len] for s in card2_samples]
    
    results1 = analyze_flip_rate(card1_samples, "Card 1", script_dir)
    results2 = analyze_flip_rate(card2_samples, "Card 2", script_dir)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"""
                        Card 1      Card 2
Perfectly stable:       {results1['perfectly_stable']:5d}       {results2['perfectly_stable']:5d}
Very stable (<5%):      {results1['very_stable']:5d}       {results2['very_stable']:5d}
Stable (<10%):          {results1['stable']:5d}       {results2['stable']:5d}
Unstable (>=10%):       {results1['unstable']:5d}       {results2['unstable']:5d}

Use the stable_mask.npy files to extract only reliable bits for PUF operations.
""")

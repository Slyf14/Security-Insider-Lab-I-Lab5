#!/usr/bin/env python3
"""Generate Inter-HD comparison figure: Before vs After XOR."""

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
            bytes_list.append(int(hex_str[i:i+2], 16))
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

def create_xor_mask(samples):
    samples_array = np.array(samples)
    mean_per_bit = np.mean(samples_array, axis=0)
    current_hw = np.mean(mean_per_bit)
    target_flip_ratio = 0.5 - current_hw
    stable_zero_positions = mean_per_bit < 0.05
    mask = np.zeros(len(mean_per_bit), dtype=np.uint8)
    stable_indices = np.where(stable_zero_positions)[0]
    num_to_flip = int(target_flip_ratio * len(mean_per_bit))
    num_to_flip = min(num_to_flip, len(stable_indices))
    np.random.seed(42)
    flip_indices = np.random.choice(stable_indices, size=num_to_flip, replace=False)
    mask[flip_indices] = 1
    return mask

def apply_xor_mask(samples, mask):
    return [np.bitwise_xor(s, mask[:len(s)]) for s in samples]

def hamming_distance(bits1, bits2):
    min_len = min(len(bits1), len(bits2))
    return np.sum(bits1[:min_len] != bits2[:min_len]) / min_len

def compute_inter_hd(samples1, samples2):
    distances = []
    for s1 in samples1:
        for s2 in samples2:
            distances.append(hamming_distance(s1, s2))
    return np.array(distances)

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(parent_dir, "SRAM_collected_data")
    
    print("=" * 60)
    print("Inter-HD with XOR Debiasing Analysis")
    print("=" * 60)
    
    # Load samples
    print("\nLoading samples...")
    card1 = load_all_samples(os.path.join(data_dir, "card1"))
    card2 = load_all_samples(os.path.join(data_dir, "card2"))
    print(f"  Card 1: {len(card1)} samples")
    print(f"  Card 2: {len(card2)} samples")
    
    min_len = min(min(len(s) for s in card1), min(len(s) for s in card2))
    card1 = [s[:min_len] for s in card1]
    card2 = [s[:min_len] for s in card2]
    
    # Before XOR
    print("\nComputing Inter-HD BEFORE XOR...")
    inter_before = compute_inter_hd(card1, card2)
    
    # Apply XOR debiasing
    print("Applying XOR debiasing...")
    mask1 = create_xor_mask(card1)
    mask2 = create_xor_mask(card2)
    card1_xor = apply_xor_mask(card1, mask1)
    card2_xor = apply_xor_mask(card2, mask2)
    
    # After XOR
    print("Computing Inter-HD AFTER XOR...")
    inter_after = compute_inter_hd(card1_xor, card2_xor)
    
    # Print summary
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"\nInter-HD BEFORE XOR: {np.mean(inter_before):.4f}")
    print(f"Inter-HD AFTER XOR:  {np.mean(inter_after):.4f}")
    print(f"Ideal:               0.5")
    print(f"\nImprovement: {np.mean(inter_after) - np.mean(inter_before):.4f}")
    
    # Create figure
    print("\nGenerating comparison figure...")
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    # Before
    axes[0].hist(inter_before, bins=25, alpha=0.8, color='green', edgecolor='darkgreen')
    axes[0].axvline(x=0.5, color='red', linestyle='--', linewidth=2, label='Ideal (0.5)')
    axes[0].axvline(x=np.mean(inter_before), color='blue', linestyle='-', linewidth=2, 
                    label=f'Mean ({np.mean(inter_before):.4f})')
    axes[0].set_xlabel('Inter-Hamming Distance', fontsize=12)
    axes[0].set_ylabel('Frequency', fontsize=12)
    axes[0].set_title(f'BEFORE XOR Debiasing\nMean = {np.mean(inter_before):.4f}', fontsize=14)
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    axes[0].set_xlim(0.2, 0.6)
    
    # After
    axes[1].hist(inter_after, bins=25, alpha=0.8, color='green', edgecolor='darkgreen')
    axes[1].axvline(x=0.5, color='red', linestyle='--', linewidth=2, label='Ideal (0.5)')
    axes[1].axvline(x=np.mean(inter_after), color='blue', linestyle='-', linewidth=2,
                    label=f'Mean ({np.mean(inter_after):.4f})')
    axes[1].set_xlabel('Inter-Hamming Distance', fontsize=12)
    axes[1].set_ylabel('Frequency', fontsize=12)
    axes[1].set_title(f'AFTER XOR Debiasing\nMean = {np.mean(inter_after):.4f}', fontsize=14)
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    axes[1].set_xlim(0.2, 0.6)
    
    plt.tight_layout()
    output_path = os.path.join(script_dir, 'inter_hd_xor_comparison.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nSaved: {output_path}")
    plt.close()


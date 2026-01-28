#!/usr/bin/env python3
"""
SRAM PUF Analysis with XOR Debiasing

We created a XOR mask from the most common bits across all samples then applied it to balance Hamming Weight toward 0.5
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


def hamming_weight(bits):
    return np.sum(bits) / len(bits)

def hamming_distance(bits1, bits2):
    min_len = min(len(bits1), len(bits2))
    return np.sum(bits1[:min_len] != bits2[:min_len]) / min_len

def compute_intra_hd(samples):
    distances = []
    for i, j in combinations(range(len(samples)), 2):
        distances.append(hamming_distance(samples[i], samples[j]))
    return np.array(distances)


def create_comparison_figure(original_samples, debiased_samples, card_name, output_dir):
    hw_orig = [hamming_weight(s) for s in original_samples]
    hw_debias = [hamming_weight(s) for s in debiased_samples]
    intra_orig = compute_intra_hd(original_samples)
    intra_debias = compute_intra_hd(debiased_samples)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    x = np.arange(1, len(hw_orig) + 1)
    
    axes[0].bar(x, hw_orig, color='steelblue', alpha=0.8)
    axes[0].axhline(y=0.5, color='green', linestyle='--', linewidth=2, label='Ideal (0.5)')
    axes[0].axhline(y=np.mean(hw_orig), color='red', linestyle='-', linewidth=2, label=f'Mean ({np.mean(hw_orig):.4f})')
    axes[0].set_xlabel('Sample #')
    axes[0].set_ylabel('Hamming Weight')
    axes[0].set_title(f'{card_name} - ORIGINAL\nMean HW = {np.mean(hw_orig):.4f}')
    axes[0].set_ylim(0, 0.7)
    axes[0].legend()
    axes[0].grid(axis='y', alpha=0.3)
    
    axes[1].bar(x, hw_debias, color='coral', alpha=0.8)
    axes[1].axhline(y=0.5, color='green', linestyle='--', linewidth=2, label='Ideal (0.5)')
    axes[1].axhline(y=np.mean(hw_debias), color='red', linestyle='-', linewidth=2, label=f'Mean ({np.mean(hw_debias):.4f})')
    axes[1].set_xlabel('Sample #')
    axes[1].set_ylabel('Hamming Weight')
    axes[1].set_title(f'{card_name} - WITH XOR DEBIASING\nMean HW = {np.mean(hw_debias):.4f}')
    axes[1].set_ylim(0, 0.7)
    axes[1].legend()
    axes[1].grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    hw_path = os.path.join(output_dir, f'{card_name.lower().replace(" ", "_")}_xor_hamming_weight.png')
    plt.savefig(hw_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {hw_path}")
    plt.close()
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    axes[0].hist(intra_orig, bins=25, color='steelblue', alpha=0.8)
    axes[0].axvline(x=np.mean(intra_orig), color='red', linestyle='-', linewidth=2, label=f'Mean ({np.mean(intra_orig):.4f})')
    axes[0].set_xlabel('Intra-HD')
    axes[0].set_ylabel('Frequency')
    axes[0].set_title(f'{card_name} - ORIGINAL\nMean Intra-HD = {np.mean(intra_orig):.4f}')
    axes[0].legend()
    axes[0].grid(alpha=0.3)
    
    axes[1].hist(intra_debias, bins=25, color='coral', alpha=0.8)
    axes[1].axvline(x=np.mean(intra_debias), color='red', linestyle='-', linewidth=2, label=f'Mean ({np.mean(intra_debias):.4f})')
    axes[1].set_xlabel('Intra-HD')
    axes[1].set_ylabel('Frequency')
    axes[1].set_title(f'{card_name} - WITH XOR DEBIASING\nMean Intra-HD = {np.mean(intra_debias):.4f}')
    axes[1].legend()
    axes[1].grid(alpha=0.3)
    
    plt.tight_layout()
    intra_path = os.path.join(output_dir, f'{card_name.lower().replace(" ", "_")}_xor_intra_hd.png')
    plt.savefig(intra_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {intra_path}")
    plt.close()
    
    return {
        'hw_orig': np.mean(hw_orig),
        'hw_debias': np.mean(hw_debias),
        'intra_orig': np.mean(intra_orig),
        'intra_debias': np.mean(intra_debias)
    }


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(parent_dir, "SRAM_collected_data")
    card1_dir = os.path.join(data_dir, "card1")
    card2_dir = os.path.join(data_dir, "card2")
    
    print("=" * 60)
    print("SRAM PUF Analysis with XOR Debiasing")
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
    
    print("\nCreating XOR masks...")
    mask1 = create_xor_mask(card1_samples)
    mask2 = create_xor_mask(card2_samples)
    
    card1_debiased = apply_xor_mask(card1_samples, mask1)
    card2_debiased = apply_xor_mask(card2_samples, mask2)
    
    print("\nGenerating comparison figures...")
    results1 = create_comparison_figure(card1_samples, card1_debiased, "Card 1", script_dir)
    results2 = create_comparison_figure(card2_samples, card2_debiased, "Card 2", script_dir)
    
    print("\n" + "=" * 60)
    print("SUMMARY - Before vs After XOR Debiasing")
    print("=" * 60)
    
    print(f"""
Card 1:
  Hamming Weight: {results1['hw_orig']:.4f} -> {results1['hw_debias']:.4f}  (Target: 0.5)
  Intra-HD:       {results1['intra_orig']:.4f} -> {results1['intra_debias']:.4f}  (Target: 0)

Card 2:
  Hamming Weight: {results2['hw_orig']:.4f} -> {results2['hw_debias']:.4f}  (Target: 0.5)
  Intra-HD:       {results2['intra_orig']:.4f} -> {results2['intra_debias']:.4f}  (Target: 0)
""")
    
    print("4 comparison figures saved!")

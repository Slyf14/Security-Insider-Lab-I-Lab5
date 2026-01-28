"""
SRAM PUF Intra-Hamming Distance Analysis
Calculates and visualizes Intra-HD (reliability/stability) for each device
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
    filenames = []
    
    for filename in sorted(os.listdir(directory), key=lambda x: int(x) if x.isdigit() else 0):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and not filename.endswith('.py'):
            try:
                bits = load_sram_file(filepath)
                if len(bits) > 0:
                    samples.append(bits)
                    filenames.append(filename)
            except Exception as e:
                print(f"Warning: Could not load {filename}: {e}")
    
    return samples, filenames


def hamming_distance(bits1, bits2):
    min_len = min(len(bits1), len(bits2))
    return np.sum(bits1[:min_len] != bits2[:min_len]) / min_len


def compute_intra_hd(samples):
    distances = []
    for i, j in combinations(range(len(samples)), 2):
        hd = hamming_distance(samples[i], samples[j])
        distances.append(hd)
    return np.array(distances)


def create_intra_hd_figure(samples, card_name, output_path):
    intra_hd = compute_intra_hd(samples)
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.hist(intra_hd, bins=25, color='coral', alpha=0.8, edgecolor='darkred')
    ax.axvline(x=0, color='green', linestyle='--', linewidth=2, label='Ideal (0)')
    ax.axvline(x=np.mean(intra_hd), color='red', linestyle='-', linewidth=2, label=f'Mean ({np.mean(intra_hd):.4f})')
    
    ax.set_xlabel('Intra-Hamming Distance', fontsize=12)
    ax.set_ylabel('Frequency', fontsize=12)
    ax.set_title(f'{card_name} - Intra-HD Distribution (Stability)\n(Mean = {np.mean(intra_hd):.4f}, Ideal = 0)', fontsize=14)
    ax.legend(loc='upper right')
    ax.grid(alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()
    
    return intra_hd


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(parent_dir, "SRAM_collected_data")
    card1_dir = os.path.join(data_dir, "card1")
    card2_dir = os.path.join(data_dir, "card2")
    
    print("=" * 60)
    print("SRAM PUF Intra-Hamming Distance Analysis")
    print("=" * 60)
    
    print("\nLoading Card 1...")
    card1_samples, _ = load_all_samples(card1_dir)
    print(f"  Loaded {len(card1_samples)} samples")
    
    print("Loading Card 2...")
    card2_samples, _ = load_all_samples(card2_dir)
    print(f"  Loaded {len(card2_samples)} samples")
    
    min_len = min(min(len(s) for s in card1_samples), min(len(s) for s in card2_samples))
    card1_samples = [s[:min_len] for s in card1_samples]
    card2_samples = [s[:min_len] for s in card2_samples]
    print(f"\nUsing {min_len} bits per sample")
    
    print("\n" + "=" * 60)
    print("Generating Intra-HD Figures...")
    print("=" * 60)
    
    intra1 = create_intra_hd_figure(
        card1_samples, "Card 1",
        os.path.join(script_dir, "card1_intra_hd.png")
    )
    
    intra2 = create_intra_hd_figure(
        card2_samples, "Card 2",
        os.path.join(script_dir, "card2_intra_hd.png")
    )
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nCard 1 Intra-HD: {np.mean(intra1):.4f} (Ideal: 0)")
    print(f"Card 2 Intra-HD: {np.mean(intra2):.4f} (Ideal: 0)")
    print("\n2 figures saved!")

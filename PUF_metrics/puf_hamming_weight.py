"""
SRAM PUF Hamming Weight Analysis
Calculates and visualizes Hamming Weight (randomness) for each device
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


def hamming_weight(bits):
    return np.sum(bits) / len(bits)


def create_hamming_weight_figure(samples, card_name, output_path):
    hw_values = [hamming_weight(s) for s in samples]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    x = np.arange(1, len(hw_values) + 1)
    bars = ax.bar(x, hw_values, color='steelblue', alpha=0.8, edgecolor='navy')
    ax.axhline(y=0.5, color='green', linestyle='--', linewidth=2, label='Ideal (0.5)')
    ax.axhline(y=np.mean(hw_values), color='red', linestyle='-', linewidth=2, alpha=0.7, label=f'Mean ({np.mean(hw_values):.4f})')
    
    ax.set_xlabel('Sample Number', fontsize=12)
    ax.set_ylabel('Hamming Weight', fontsize=12)
    ax.set_title(f'{card_name} - Hamming Weight per Sample\n(Mean = {np.mean(hw_values):.4f}, Ideal = 0.5)', fontsize=14)
    ax.set_ylim(0, 0.6)
    ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()
    
    return hw_values


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(parent_dir, "SRAM_collected_data")
    card1_dir = os.path.join(data_dir, "card1")
    card2_dir = os.path.join(data_dir, "card2")
    
    print("=" * 60)
    print("SRAM PUF Hamming Weight Analysis")
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
    print("Generating Hamming Weight Figures...")
    print("=" * 60)
    
    hw1 = create_hamming_weight_figure(
        card1_samples, "Card 1",
        os.path.join(script_dir, "card1_hamming_weight.png")
    )
    
    hw2 = create_hamming_weight_figure(
        card2_samples, "Card 2",
        os.path.join(script_dir, "card2_hamming_weight.png")
    )
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"\nCard 1 Hamming Weight: {np.mean(hw1):.4f} (Ideal: 0.5)")
    print(f"Card 2 Hamming Weight: {np.mean(hw2):.4f} (Ideal: 0.5)")
    print("\n2 figures saved!")

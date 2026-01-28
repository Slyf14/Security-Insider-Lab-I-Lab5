
"""
SRAM PUF Representative Fingerprint Generator

Computes a canonical fingerprint from the SRAM PUF responses.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
import hashlib


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


def compute_fingerprint(samples):
    samples_array = np.array(samples)
    per_bit_mean = np.mean(samples_array, axis=0)
    fingerprint = (per_bit_mean >= 0.5).astype(np.uint8)
    return fingerprint


def fingerprint_to_hex(fingerprint, num_bytes=64):
    hex_str = ""
    for i in range(0, min(len(fingerprint), num_bytes * 8), 8):
        byte = 0
        for j in range(8):
            if i + j < len(fingerprint):
                byte = (byte << 1) | fingerprint[i + j]
        hex_str += f"{byte:02X} "
        if (i // 8 + 1) % 16 == 0:
            hex_str += "\n"
    return hex_str.strip()


def fingerprint_hash(fingerprint):
    byte_array = np.packbits(fingerprint)
    return hashlib.sha256(byte_array.tobytes()).hexdigest()


def create_fingerprint_image(fingerprint, card_name, output_dir):
    num_bits = len(fingerprint)
    width = 128
    height = (num_bits + width - 1) // width
    
    padded = np.zeros(width * height, dtype=np.uint8)
    padded[:num_bits] = fingerprint
    bitmap = padded.reshape(height, width)
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    ax.imshow(bitmap, cmap='binary', interpolation='nearest', aspect='auto')
    ax.set_title(f'{card_name} - PUF Fingerprint\n({num_bits} bits, {width}x{height} grid)', fontsize=14)
    ax.set_xlabel('Bit column')
    ax.set_ylabel('Bit row')
    
    plt.tight_layout()
    output_path = os.path.join(output_dir, f'{card_name.lower().replace(" ", "_")}_fingerprint.png')
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"  Fingerprint image saved: {output_path}")
    plt.close()


if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(script_dir)
    data_dir = os.path.join(parent_dir, "SRAM_collected_data")
    card1_dir = os.path.join(data_dir, "card1")
    card2_dir = os.path.join(data_dir, "card2")
    
    print("=" * 60)
    print("SRAM PUF Representative Fingerprint Generator")
    print("=" * 60)
    
    print("\nLoading samples...")
    card1_samples = load_all_samples(card1_dir)
    card2_samples = load_all_samples(card2_dir)
    
    min_len = min(min(len(s) for s in card1_samples), min(len(s) for s in card2_samples))
    card1_samples = [s[:min_len] for s in card1_samples]
    card2_samples = [s[:min_len] for s in card2_samples]
    
    print(f"  Card 1: {len(card1_samples)} samples, {min_len} bits each")
    print(f"  Card 2: {len(card2_samples)} samples, {min_len} bits each")
    
    print("\nComputing fingerprints (majority voting)...")
    fp1 = compute_fingerprint(card1_samples)
    fp2 = compute_fingerprint(card2_samples)
    
    np.save(os.path.join(script_dir, 'card_1_fingerprint.npy'), fp1)
    np.save(os.path.join(script_dir, 'card_2_fingerprint.npy'), fp2)
    print("  Fingerprints saved as .npy files")
    
    print("\nCard 1 Fingerprint:")
    print(f"  SHA-256: {fingerprint_hash(fp1)}")
    print(f"  First 64 bytes (hex):\n{fingerprint_to_hex(fp1)}")
    create_fingerprint_image(fp1, "Card 1", script_dir)
    
    print("\nCard 2 Fingerprint:")
    print(f"  SHA-256: {fingerprint_hash(fp2)}")
    print(f"  First 64 bytes (hex):\n{fingerprint_to_hex(fp2)}")
    create_fingerprint_image(fp2, "Card 2", script_dir)
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    hd = np.sum(fp1 != fp2) / len(fp1)
    print(f"""
Card 1 SHA-256: {fingerprint_hash(fp1)[:32]}...
Card 2 SHA-256: {fingerprint_hash(fp2)[:32]}...

Fingerprint Hamming Distance: {hd:.4f}

Files saved:
  - card_1_fingerprint.npy / card_2_fingerprint.npy
  - card_1_fingerprint.png / card_2_fingerprint.png
""")

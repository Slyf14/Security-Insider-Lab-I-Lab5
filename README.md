# Characterizing SRAM PUFs on Arduino Microcontrollers

Analysis of SRAM Physically Unclonable Functions (PUFs) in terms of **Randomness**, **Uniqueness** and **Robustness**.

## Project Structure

```
├── SRAM_collected_data/        # Raw SRAM startup values
│   ├── card1/                  # 112 samples from Arduino #1
│   └── card2/                  # 112 samples from Arduino #2
│
├── PUF_metrics/                # Core PUF quality metrics
│   ├── puf_hamming_weight.py   # Randomness (HW → target is 0.5)
│   ├── puf_intra_HD.py         # Robustness (Intra-HD → target is 0)
│   └── puf_inter_HD.py         # Uniqueness (Inter-HD → target is 0.5)
│
├── post_processing/             # Post-processing techniques
│   ├── puf_xor_debias_HW_and_intra.py  # XOR debiasing (HW + Intra-HD)
│   ├── puf_xor_debias_inter.py         # XOR debiasing (Inter-HD)
│   ├── puf_flip_rate.py                # Bit stability analysis
│   ├── puf_bit_balance.py              # Per bit 1 rate distribution
│   └── puf_unstable_bits.py            # Unstable bits extraction
│
├── Fingerprint_construction/   # Device fingerprint generation
│   └── puf_fingerprint_generation.py   # Majority voting + SHA 256 hash
│
├── SRAM_data_cleaning/         # Data preparation
│   └── clean_sram_files.py     # Remove garbage from captures
│
└── readSRAMstartupvalues.ino   # Arduino sketch for data collection
```


## Quick Start

### 1. Collect SRAM Data
Upload `readSRAMstartupvalues.ino` to Arduino, capture output via Serial Monitor.

### 2. Analyze PUF Metrics
```bash
python PUF_metrics/puf_hamming_weight.py   # Randomness
python PUF_metrics/puf_intra_HD.py         # Robustness
python PUF_metrics/puf_inter_HD.py         # Uniqueness
```

### 3. Apply Post-Processing
```bash
python post_processing/puf_xor_debias_HW_and_intra.py  # Improve HW
python post_processing/puf_xor_debias_inter.py         # Improve Inter-HD
python post_processing/puf_flip_rate.py                # Bit stability analysis
python post_processing/puf_bit_balance.py              # Per bit 1 rate distribution
python post_processing/puf_unstable_bits.py            # Unstable bits extraction
```

### 4. Generate Fingerprints
```bash
python Fingerprint_construction/puf_fingerprint_generation.py
```

## Key Results

| Metric | Card 1 | Card 2 | Ideal |
|--------|--------|--------|-------|
| Hamming Weight (raw) | 0.1887 | 0.1739 | 0.5 |
| Hamming Weight (XOR) | 0.4978 | 0.4990 | 0.5 |
| Intra-HD | 0.0429 | 0.0336 | 0 |
| Inter-HD (raw) | 0.2954 | - | 0.5 |
| Inter-HD (XOR) | 0.4970 | - | 0.5 |

## Authors
Sofian Yadir and Wassim Bejaoui  

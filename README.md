# LAMI-IRS-6G-Reproducibility

Reference reproducibility and reconstruction package for the manuscript:

**“Agentic Metasurface Intelligence for IRS in 6G Edge Networks.”**

This repository provides a transparent, runnable artifact package aligned with the revised manuscript. It contains prompt templates, semantic input/output schemas, closed-loop agentic IRS control pseudocode, trustworthiness validation logic, simulation configuration files, and Python scripts for reconstructing the reported evaluation trends on SNR recovery, distance-dependent adaptation, latency/energy accounting, and scalability.

> **Important scope statement**  
> This repository is a reference/reconstruction package for review and reproducibility. It is **not** an over-the-air IRS hardware implementation and does **not** claim real IRS or FPGA deployment. The FPGA actuation stage is represented as bounded discrete control actions, and the external knowledge/context module is simulated, consistent with the methodology described in the manuscript.

---

## 1. What this package contains

```text
LAMI-IRS-6G-Reproducibility/
│
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
├── environment.yml
│
├── configs/
│   ├── default_simulation.yaml
│   ├── channel_models.yaml
│   ├── irs_scalability.yaml
│   └── latency_energy_accounting.yaml
│
├── prompts/
│   ├── zero_shot_prompt.txt
│   ├── few_shot_prompt.txt
│   ├── structured_cot_prompt.txt
│   ├── validation_prompt.txt
│   └── fallback_prompt.txt
│
├── schemas/
│   ├── semantic_input_schema.json
│   ├── llm_output_schema.json
│   └── irs_control_vector_schema.json
│
├── algorithms/
│   ├── closed_loop_lami_pseudocode.md
│   ├── trustworthiness_pipeline.md
│   └── fallback_control.md
│
├── scripts/
│   ├── common.py
│   ├── generate_channel_realizations.py
│   ├── generate_semantic_inputs.py
│   ├── lami_reference_controller.py
│   ├── validate_irs_action.py
│   ├── run_latency_energy_accounting.py
│   ├── reproduce_snr_recovery.py
│   ├── reproduce_distance_adaptation.py
│   ├── reproduce_scalability_analysis.py
│   └── run_all.py
│
├── sample_data/
├── results/
├── figures/
└── supplementary/
    └── supplementary_material.tex
```

---

## 2. Paper-aligned system assumptions

The scripts use the following default assumptions from the manuscript and revision plan:

| Item | Default value |
|---|---:|
| Carrier frequency | 6 GHz |
| Transmit power | 30 dBm |
| Noise floor | -90 dBm |
| Path-loss exponent | 2.4 |
| IRS elements in main evaluation | 64 |
| IRS element spacing | 2.5 cm |
| Channel model | Rician fading |
| Rician K-factor | 6 dB |
| IRS element failure rate | 10–15% |
| Interference burst | 5 dB |
| Interference burst duration | 100 ms |
| Distance range | 10–200 m |
| Main LLM | GPT-J-6B reference setting |
| Edge SLM | DistilBERT-style compact SLM reference setting |
| Edge SLM device | Jetson Orin NX-style edge accelerator |
| Profiling device | NVIDIA A100-style profiling device |
| Decision output | bounded JSON; quantized IRS phase updates |

The default number of channel realizations is set to `100` to support confidence intervals in the revised analysis. This can be changed in `configs/default_simulation.yaml`.

---

## 3. How to run

### 3.1 Create a Python environment

Using `venv`:

```bash
python -m venv .venv
```

Activate it:

- Windows PowerShell:

```bash
.venv\Scripts\Activate.ps1
```

- Windows Command Prompt:

```bash
.venv\Scripts\activate.bat
```

- Linux/macOS:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

### 3.2 Run the full reconstruction workflow

```bash
python scripts/run_all.py
```

This command generates:

```text
sample_data/channel_realizations.csv
sample_data/sample_semantic_inputs.jsonl
sample_data/sample_irs_outputs.jsonl
results/latency_energy_results.csv
results/snr_recovery_results.csv
results/distance_adaptation_results.csv
results/scalability_results.csv
figures/latency_energy_comparison.png
figures/snr_recovery.png
figures/distance_adaptation.png
figures/scalability_latency.png
figures/scalability_memory.png
```

### 3.3 Run scripts individually

```bash
python scripts/generate_channel_realizations.py --config configs/default_simulation.yaml
python scripts/generate_semantic_inputs.py --config configs/default_simulation.yaml
python scripts/lami_reference_controller.py --config configs/default_simulation.yaml
python scripts/validate_irs_action.py --config configs/default_simulation.yaml
python scripts/reproduce_snr_recovery.py --config configs/default_simulation.yaml
python scripts/reproduce_distance_adaptation.py --config configs/default_simulation.yaml
python scripts/run_latency_energy_accounting.py --config configs/latency_energy_accounting.yaml
python scripts/reproduce_scalability_analysis.py --config configs/irs_scalability.yaml
```

---

## 4. Prompt templates

The prompt files in `prompts/` describe four bounded prompting modes used in the revised LAMI description:

1. `zero_shot_prompt.txt` — direct compact control decision without examples.
2. `few_shot_prompt.txt` — representative IRS control examples for recurring states.
3. `structured_cot_prompt.txt` — structured reasoning fields without free-form chain-of-thought exposure.
4. `validation_prompt.txt` — validator prompt for physical consistency checks.
5. `fallback_prompt.txt` — fallback/control-hold instruction when uncertainty is high or output is unsafe.

The prompts enforce JSON-only outputs and phase-quantization constraints so that the LLM cannot directly issue arbitrary natural-language actuation commands.

---

## 5. Trustworthiness controls

The reference pipeline uses the following safety checks:

1. **SLM confidence filtering:** descriptors with confidence below `slm_confidence_threshold` are down-weighted.
2. **Priority-confidence aggregation:** conflicting semantic descriptors are fused using normalized confidence-priority weights.
3. **LLM confidence gate:** LLM actions below `llm_confidence_threshold` are rejected.
4. **Physical validity validation:** phase updates must belong to the quantized phase set, update sparsity must be bounded, and output format must match the schema.
5. **Fallback control:** invalid or uncertain decisions are replaced by hold-state or cached-safe control.

---

## 6. Reproducibility note for manuscript/rebuttal

Suggested wording for the revised manuscript:

> To support reproducibility within the IEEE Communications Magazine page limit, we provide a supplementary artifact package containing prompt templates, semantic input-output schemas, closed-loop pseudocode, trustworthiness validation logic, latency/energy accounting scripts, and reference simulation code. The package reconstructs the controller-side evaluation trends under the assumptions described in the manuscript and does not claim an OTA IRS hardware implementation.

Suggested wording for the response letter:

> We prepared a dedicated supplementary reproducibility package. The package includes prompt templates, semantic JSON schemas, IRS control-vector definitions, closed-loop pseudocode, trustworthiness validation logic, simulation configuration files, latency/energy accounting scripts, and reference code for reconstructing the reported evaluation trends. We explicitly label the artifact as a reference/reconstruction package rather than a real IRS hardware or OTA implementation.

---

## 7. Citation

If this package is archived on Zenodo, please cite the DOI generated by Zenodo. A draft `CITATION.cff` file is included and should be updated with the final DOI after archival.

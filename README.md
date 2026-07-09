# LAMI-IRS-6G

Implementation and reproducibility codebase for the article:

**Agentic Metasurface Intelligence for IRS in 6G Edge Networks**

This repository contains the implementation artifacts used to generate and reproduce the controller-side evaluation of the proposed **LAMI** framework. LAMI is an LLM-agent assisted metasurface intelligence architecture for IRS-assisted 6G edge networks. It combines edge-side SLM-based semantic abstraction, IRS-side bounded LLM reasoning, deterministic action validation, and fallback control before metasurface actuation.

The codebase includes simulation configurations, semantic input/output schemas, prompt templates, bounded LLM-agent control logic, IRS action-validation scripts, latency/energy accounting, result-generation scripts, and deployment notes.

---

## Repository scope

LAMI is evaluated as a **controller-side IRS reasoning and validation framework**. The repository models FPGA-assisted IRS actuation as a bounded discrete command interface and uses simulated contextual metadata for external network context. It does not claim over-the-air IRS hardware deployment, physical FPGA timing validation, or measured-channel testbed execution.

This scope is consistent with the article, where the reported latency is defined as controller-side decision latency from compact descriptor availability to validated IRS control output.

---

## Architecture summary

The LAMI workflow follows a semantic-control loop:

1. **Edge-side SLM abstraction**  
   Edge clients use compact SLMs to summarize local link and device observations into semantic descriptors with confidence scores.

2. **Semantic descriptor fusion**  
   The IRS-side coordination layer aggregates descriptors from multiple edge nodes using confidence-aware fusion.

3. **Bounded LLM-agent reasoning**  
   The IRS-side LLM agent reasons over compact descriptors and recent-state memory to generate a structured IRS control directive.

4. **Deterministic validation**  
   The candidate directive is checked for schema validity, confidence, target-region feasibility, supported phase states, update bounds, and fallback requirements.

5. **IRS command preparation**  
   Validated directives are translated into bounded IRS control commands. Unsafe, incomplete, contradictory, or low-confidence outputs trigger fallback control.

---

## Repository structure

```text
LAMI-IRS-6G/
├── README.md
├── LICENSE
├── CITATION.cff
├── requirements.txt
├── environment.yml
├── configs/
│   ├── default_simulation.yaml
│   ├── channel_models.yaml
│   ├── irs_scalability.yaml
│   └── latency_energy_accounting.yaml
├── prompts/
│   ├── zero_shot_prompt.txt
│   ├── few_shot_prompt.txt
│   ├── structured_cot_prompt.txt
│   ├── validation_prompt.txt
│   └── fallback_prompt.txt
├── schemas/
│   ├── semantic_input_schema.json
│   ├── llm_output_schema.json
│   └── irs_control_vector_schema.json
├── algorithms/
│   ├── closed_loop_lami_pseudocode.md
│   ├── trustworthiness_pipeline.md
│   └── fallback_control.md
├── scripts/
│   ├── run_all.py
│   ├── generate_channel_realizations.py
│   ├── generate_semantic_inputs.py
│   ├── lami_reference_controller.py
│   ├── validate_irs_action.py
│   ├── run_latency_energy_accounting.py
│   ├── reproduce_snr_recovery.py
│   ├── reproduce_distance_adaptation.py
│   └── reproduce_scalability_analysis.py
├── sample_data/
│   ├── sample_semantic_inputs.jsonl
│   ├── sample_irs_outputs.jsonl
│   └── sample_results.csv
└── results/
    └── generated CSV result files
```

---

## Installation

### Option 1: Conda

```bash
conda env create -f environment.yml
conda activate lami-irs-6g
```

### Option 2: pip

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
```

---

## Result generation workflow

Run the complete LAMI evaluation pipeline using:

```bash
python scripts/run_all.py
```

This executes the following steps:

1. Generate randomized channel and IRS-failure realizations.
2. Generate compact edge-side semantic descriptors.
3. Run the bounded LAMI reference controller.
4. Validate IRS control actions using schema, confidence, phase-feasibility, update-bound, and fallback checks.
5. Generate SNR recovery results under induced IRS faults and interference bursts.
6. Generate distance-adaptation results under increasing transmitter–receiver separation.
7. Generate controller-side latency and energy accounting.
8. Generate scalability estimates for larger IRS panels.
9. Save output CSV files in `results/`.

The generated outputs reproduce the controller-side numerical trends reported in the article.

---

## Main controller-side results

| Controller | Energy per decision | Decision latency | Interpretation |
|---|---:|---:|---|
| Conventional IRS | 14.0 mJ | 0.31 ms | Lowest overhead, limited adaptivity |
| DRL-based IRS | 22.0 mJ | 0.85 ms | Adaptive, but training-distribution dependent |
| Standalone LLM-IRS | 36.34 mJ | 1.28 ms | Semantic flexibility with high open-loop reasoning overhead |
| LAMI | 27.0 mJ | 1.02 ms | Bounded SLM–LLM reasoning with validation and fallback |

Relative to the standalone LLM-IRS baseline, LAMI reduces energy per decision by **25.7%** and controller-side decision latency by **20.3%** under the evaluated simulation setup.

The reported latency is controller-side decision latency. Hardware-specific sensing delay, fronthaul/side-link transmission, FPGA transfer, IRS bias settling, and over-the-air feedback delay must be added separately for a field implementation.

---

## Generated result files

After running the workflow, the following CSV result files are generated in `results/`:

| Result file | Purpose |
|---|---|
| `results/latency_energy_results.csv` | Reproduces the controller-side energy/latency comparison |
| `results/snr_recovery_results.csv` | Stores transient recovery trends under IRS faults and interference bursts |
| `results/distance_adaptation_results.csv` | Stores SNR behavior under increasing transmitter–receiver distance |
| `results/scalability_results.csv` | Stores scalability estimates for larger IRS panels |
| `results/validation_summary.csv` | Stores trustworthiness validation and fallback statistics |

Plots used in the article are generated from these CSV files and may be exported locally by the user if needed.

---

## Simulation setting

The default configuration represents the controller-side IRS simulation used in the article.

| Parameter | Default value |
|---|---:|
| Carrier frequency | 6 GHz |
| Transmit power | 30 dBm |
| Path-loss exponent | 2.4 |
| Receiver noise floor | -90 dBm |
| IRS elements | 64 |
| IRS element spacing | 2.5 cm |
| Channel model | Rician fading |
| Rician K-factor | 6 dB |
| IRS element failures | 10–15% randomized failures |
| Interference burst | 5 dB |
| Burst duration | 100 ms |
| Distance range | 10 m to 200 m |
| Distance step | 10 m |
| Randomized realizations | 100 |

---

## Model and control configuration

| Component | Configuration |
|---|---|
| IRS-side LLM | GPT-J-6B reference model |
| Edge-side SLM | DistilBERT-style compact SLM |
| SLM size | approximately 82M parameters |
| SLM profiling device | NVIDIA Jetson Orin NX profile |
| LLM profiling device | NVIDIA A100 profile |
| LLM execution | FP16 with 4-bit attention-layer quantization during profiling |
| Training source | synthetic state–action pairs generated from DRL-style IRS optimization trajectories |
| State–action pairs | approximately 14,000 |
| Descriptor size | below 128 bytes |
| Output format | bounded structured control object |
| Online retraining | not required per control interval |
| Slow adaptation | offline recalibration under persistent distribution shift |

Short-term adaptation is handled through descriptor confidence, recent-state memory, post-actuation feedback, and fallback control. Offline recalibration may be required when deployment topology, IRS size, mobility regime, or channel statistics change substantially.

---

## Trustworthiness and validation

The LAMI validation path prevents free-form or physically invalid LLM outputs from directly reaching the IRS command interface.

The validation script checks:

- semantic descriptor confidence,
- required output schema fields,
- target-region validity,
- phase-state feasibility,
- update-bound constraints,
- fallback requirements,
- contradictory or incomplete control directives.

Example validation logic:

```python
max_changed = int(region_count * max_changed_fraction)

if len(phase_delta_code) != region_count:
    reject()

if any(x not in [-1, 0, 1] for x in phase_delta_code):
    reject()

if count_nonzero(phase_delta_code) > max_changed:
    reject()

if confidence < llm_threshold and not fallback_required:
    reject()

if fallback_required and count_nonzero(phase_delta_code) > 0:
    reject()

if any(region_id outside valid_region_range):
    reject()

apply_or_hold_valid_state()
```

If validation fails, the controller retains the previous valid IRS state or invokes a cached-safe IRS control profile.

---

## Prompting modes

The repository includes prompt templates for three LAMI operating modes:

| Prompting mode | Use case |
|---|---|
| Zero-shot prompting | Rapid response when no site-specific examples are available |
| Few-shot prompting | Improved consistency under recurring channel or service patterns |
| Structured CoT prompting | Joint reasoning over SNR degradation, interference, latency pressure, and energy imbalance |

Prompting affects the candidate action proposed by the LLM agent. It does not bypass validation. All outputs are normalized into the same bounded control schema before actuation.

---

## Deployment pathway

The codebase supports the controller-side implementation of LAMI. A practical deployment pathway is:

1. **Controlled deployment first**  
   Begin with factories, campuses, indoor private networks, and controlled industrial IoT environments.

2. **Edge-side semantic abstraction**  
   SLMs summarize local sensing and link-state information into compact descriptors.

3. **IRS-side supervisory reasoning**  
   The LLM agent reasons over compact descriptors and proposes bounded IRS actions.

4. **Validation before actuation**  
   Schema checks, confidence gates, phase-feasibility checks, update bounds, and fallback control are applied before any IRS command is accepted.

5. **O-RAN integration path**  
   The IRS-side reasoning logic may be implemented as a supervisory xApp or near-real-time control function within the RAN Intelligent Controller.

6. **Future hardware validation**  
   Full deployment requires hardware-in-the-loop IRS testing, FPGA timing validation, measured-channel traces, multi-panel coordination, and secure semantic descriptor exchange.

---

## Reproducibility notes

The repository is intended to reproduce the controller-side trends reported in the article. Because the workflow uses randomized channel/failure realizations, exact values may vary slightly unless the random seed is fixed in the configuration file.

Recommended reproducibility command:

```bash
python scripts/run_all.py --seed 42
```

Expected outputs:

```text
results/
├── latency_energy_results.csv
├── snr_recovery_results.csv
├── distance_adaptation_results.csv
├── scalability_results.csv
└── validation_summary.csv
```

---

## Code availability

Public repository:

```text
https://github.com/pranay1986/LAMI-IRS-6G
```

---

## Citation

If you use this repository, please cite the associated article:

```bibtex
@article{lami_irs_6g,
  title   = {Agentic Metasurface Intelligence for IRS in 6G Edge Networks},
  author  = {Khan, Nishat Mahdiya and Bhattacharya, Pronaya and Zhang, Qiyang and Donta, Praveen Kumar and Gadekallu, Thippa Reddy},
  journal = {IEEE Communications Magazine},
  year    = {2026},
  note    = {Under revision}
}
```

---

## License

This repository is released for academic research and reproducibility purposes. See `LICENSE` for details.

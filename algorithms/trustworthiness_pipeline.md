# Trustworthiness pipeline

The LAMI trustworthiness path is designed to prevent hallucinated, unsafe, or physically invalid LLM outputs from being applied to the IRS hardware abstraction.

## Stage 1: SLM confidence filtering

Each edge SLM emits a confidence score. Descriptors with confidence below `tau_SLM` are either ignored or down-weighted during semantic aggregation.

## Stage 2: Conflict-aware aggregation

When multiple SLMs report conflicting conditions, descriptors are aggregated using confidence-priority weights. High-priority users with high-confidence reports contribute more strongly to the global semantic state.

## Stage 3: Bounded LLM output

The LLM must return compact JSON and cannot produce arbitrary text commands. Allowed control modes are fixed, and phase changes are represented using a discrete phase-delta code.

## Stage 4: Physical validation

The validator checks phase quantization, dimensionality, sparsity, confidence threshold, fallback consistency, and passivity constraints. Invalid actions are rejected.

## Stage 5: Fallback controller

If the LLM output is invalid, uncertain, or contradictory, the system applies a safe fallback action: hold previous state, cached-safe profile, or conventional codebook control.

## Non-claim

The pipeline improves operational trustworthiness in simulation and controller-side reconstruction. It is not a formal proof of safety for all real IRS deployments, and OTA validation remains future work.

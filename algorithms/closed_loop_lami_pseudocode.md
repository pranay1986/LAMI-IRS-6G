# Closed-loop LAMI reasoning and IRS actuation pseudocode

```text
Input:
  U edge clients with SLM-generated descriptors
  IRS with N reflecting elements and R regions
  Quantized phase set Q_B
  Confidence thresholds tau_SLM and tau_LLM
  Bounded memory window K

Initialize:
  theta_0: valid IRS phase vector
  M_0: empty bounded memory buffer
  cached_safe_profiles: valid IRS codebook/fallback profiles

For each control interval t:
  1. Edge observation:
     Each client u observes local link state z_{u,t}, including SNR,
     interference, energy state, mobility state, queue/load, and priority.

  2. SLM semantic abstraction:
     Each edge SLM converts z_{u,t} into a compact semantic descriptor s_{u,t}
     and confidence score c_{u,t}.

  3. Confidence-priority aggregation:
     The edge aggregator computes normalized weights:
       alpha_{u,t} = c_{u,t} p_{u,t} / sum_v c_{v,t} p_{v,t}
     and forms the global semantic descriptor S_t.

  4. Memory retrieval:
     The IRS-side agent retrieves the last K state-action-outcome records:
       M_{t-K:t-1} = {(S_tau, theta_tau, gamma_tau, L_tau, E_tau, eta_tau)}.

  5. Candidate action generation:
     The bounded LLM agent maps (S_t, theta_{t-1}, M_{t-K:t-1}) to a
     candidate action a_hat_t represented as JSON.

  6. Trustworthiness validation:
     Validate a_hat_t using:
       - JSON schema check
       - quantized phase check
       - confidence threshold check
       - sparsity/update-bound check
       - power/passivity check
       - fallback consistency check

  7. Actuation or fallback:
     If validation passes and LLM confidence >= tau_LLM:
       apply candidate IRS update
     Else:
       apply fallback controller: hold_state or cached_safe profile

  8. Feedback and memory update:
     Observe post-actuation SNR, latency, energy, and validation status.
     Store (S_t, theta_t, gamma_t, L_t, E_t, eta_t) in bounded memory M_t.

Output:
  Physically valid IRS control action theta_t for each interval.
```

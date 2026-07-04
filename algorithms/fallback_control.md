# Fallback control logic

Fallback control is triggered when any of the following conditions occur:

1. SLM confidence is below threshold.
2. LLM confidence is below threshold.
3. JSON output fails schema validation.
4. Phase update is outside quantized phase set.
5. Too many IRS regions/elements are updated in one interval.
6. The action requests fallback but also contains nonzero phase changes.
7. Input descriptors are contradictory or incomplete.

The fallback action is selected in this order:

```text
if previous IRS state is valid and SNR is not in severe outage:
    hold previous IRS state
elif cached safe profile exists for nearest semantic state:
    apply cached safe profile
else:
    apply conventional codebook profile with best recent measured SNR
```

This ensures that a hallucinated or unsafe LLM action cannot directly actuate the IRS.

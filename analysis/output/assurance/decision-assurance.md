# Decision assurance: floodcheck

Fund contextual follow-up rather than a duplicate-text enforcement rule. Report what the sampling design can and cannot detect at the available audit budget.

**Evidence:** The frozen signal-separation fixtures are synthetic. Duplicate text is not proof of coordination, and the detection ceiling assumes a specific uniform sample and two-member detector.

**Uncertainty:** No real-docket performance is established. Harm from false accusation is a hard gate, not monetized as a routine operating expense.

## Robustness of the assumed business case

| Alternative | Feasible grid cases / 27 | Worst regret when feasible | Maximum volume at fixed review capacity |
|---|---:|---:|---:|
| Uniform sample and contextual review | 6 | $23,348.00 | 100 |
| Metadata triage plus contextual follow-up | 9 | $1,663.00 | 166 |
| Duplicate-text flags without context | 0 | No feasible case | 1000 |

**Robust minimax choice:** None. No option is feasible across the entire stress grid.

Finite assumed grid, not a probability distribution or protection outside the grid. Conditional regret never overrides feasibility. Null robust option means no unconditional recommendation. Cost regret is relative to the cheapest feasible option in that same scenario. Failure counts can overlap.

## Missing-outcome sensitivity

| Outcomes masked per arm | Primary effect bounds | Incident effect bounds | Every completion clears margins? |
|---|---:|---:|---|
| 0% | [6.8%, 6.8%] | [1.0%, 1.0%] | False |
| 5% | [1.9%, 11.9%] | [-4.0%, 6.0%] | False |
| 10% | [-3.3%, 16.7%] | [-9.0%, 11.0%] | False |
| 20% | [-13.4%, 26.6%] | [-19.1%, 20.9%] | False |

These are identification bounds on deliberately masked synthetic outcomes, not confidence intervals or measured missingness. Failures and non-starters remain in the assigned denominator. Passing this sensitivity check would still require statistical and domain-quality gates.

## Domain measurement contract

**Decision:** Allocate a limited review budget to suspicious comment patterns without accusing legitimate participants.

**Primary outcome:** Adjudicated coordinated clusters discovered at a fixed review budget, alongside false flags on legitimate clusters.

**Denominator:** All eligible docket comments for coverage, all reviewed clusters for precision; unsampled cases are not negatives.

**Independent unit:** Coordination cluster or docket; repeated messages from one cluster are dependent.

**Quality guardrail:** False accusations, protected legitimate participation and reviewer-hour budget.

**Minimum required data:** Docket/comment IDs, sampling probabilities, cluster mapping, flag reason, independent adjudication and review effort.

**Missingness and failure handling:** Unreviewed comments retain unknown labels. Sampling-weighted population estimates require known inclusion probabilities and appropriate uncertainty.

**Release rule:** Use the detection ceiling only under its uniform-sampling and two-member-detection assumptions. Synthetic fixtures cannot authorize real enforcement.

**Reversal trigger:** Context review shows duplicates are legitimate, or the sampling design no longer matches the stated detection assumptions.

## Interview defense

**Are duplicate comments coordinated fraud?**

No. Duplication is a review signal and can reflect legitimate participation. The decision needs context and adjudication.

**Why not report recall from reviewed comments?**

The reviewed set is selected. Without labels or a defensible sampling design for the rest, population recall is unidentified.

## Implementation handoff

1. Freeze the eligible population, denominator, outcome horizon and proposed decision owner before comparison.
2. Reconcile assignment and outcome records at the independence unit; classify missingness without deleting cases.
3. Estimate the domain outcome and its uncertainty separately from activation. Apply risk and capacity vetoes before comparing costs.
4. Record approve, hold, or reverse with the evidence version and violated gate. An unmeasured required domain gate means HOLD.

The supplied cluster-budget grid is a planning sensitivity check with assumed ICC. It is not an estimate from real clusters and does not guarantee joint power. No stakeholder approval or real experiment is asserted.

"""
What a sample can establish about a docket, before any detector is written.

The question everyone skips
---------------------------
Work on coordinated commenting asks how to detect a campaign given the text.
That presumes you have the text. On Regulations.gov you do not: 1,000 requests
an hour, one request per comment body, no bulk download. A million-comment
docket is forty days of continuous polling.

So every claim about a docket's integrity rests on a sample, and the first
question is not "how good is my detector" but:

    with a budget of n comments, what could ANY detector find?

That has an answer that does not depend on the detector at all, and it is
unflattering.

Seeing a cluster requires seeing two of it
------------------------------------------
A campaign is identifiable as a campaign because its members resemble each
other. One member in a sample is just a comment. Detection needs **at least
two** members of the same campaign to land in the sample.

For a campaign that is a fraction p of a docket, sampling n comments without
replacement from N:

    P(detect) = 1 − P(0 members) − P(exactly 1 member)

which under the binomial approximation valid for n ≪ N is

    P(detect) ≈ 1 − (1−p)ⁿ − n·p·(1−p)ⁿ⁻¹

**This is a ceiling.** A perfect detector that recognises coordination from any
two members achieves exactly this and no more. Every real detector does worse.

What falls out
--------------
Large campaigns are trivially visible; the FCC's 7.5-million-comment bloc would
appear in any sample of twenty. Small ones are invisible at any budget an
auditor can afford, and "small" here still means tens of thousands of
comments on a large docket.

That matters because the campaigns worth hiding are the ones sized to pass.
A flood that swamps a docket announces itself. A campaign calibrated to be the
largest bloc without being conspicuous is both more effective and, on these
numbers, essentially undetectable by sampling.

On the independence approximation
---------------------------------
The binomial form treats draws as independent. Sampling without replacement
makes them slightly dependent, and the exact hypergeometric is used below
wherever N is small enough for the difference to matter. The approximation is
noted rather than hidden because it moves the answer at small N, which is
precisely the regime a constrained auditor works in.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def _log_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("-inf")
    return (math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1))


def detect_probability(prevalence: float, sample: int,
                       population: int | None = None,
                       min_members: int = 2) -> float:
    """
    Chance that at least `min_members` of a campaign land in the sample.

    Exact hypergeometric when `population` is given, binomial otherwise. The
    exact form matters at small populations, where sampling a meaningful
    fraction makes draws visibly dependent.
    """
    if prevalence <= 0 or sample <= 0:
        return 0.0
    if prevalence >= 1:
        return 1.0 if sample >= min_members else 0.0

    if population and population > 0:
        K = max(1, round(prevalence * population))
        n = min(sample, population)
        # P(X < min_members) summed exactly
        below = 0.0
        for k in range(min_members):
            lp = (_log_choose(K, k) + _log_choose(population - K, n - k)
                  - _log_choose(population, n))
            if lp > float("-inf"):
                below += math.exp(lp)
        return max(0.0, min(1.0, 1.0 - below))

    q = 1.0 - prevalence
    below = 0.0
    for k in range(min_members):
        below += math.exp(_log_choose(sample, k) + k * math.log(prevalence)
                          + (sample - k) * math.log(q))
    return max(0.0, min(1.0, 1.0 - below))


def sample_needed(prevalence: float, confidence: float = 0.95,
                  population: int | None = None,
                  min_members: int = 2, cap: int = 5_000_000) -> int:
    """
    Smallest sample giving `confidence` chance of seeing the campaign.

    Returns `cap` when the target is unreachable within it, which for small
    campaigns on large dockets is the honest answer rather than an
    extrapolation.
    """
    lo, hi = min_members, min(cap, population or cap)
    if detect_probability(prevalence, hi, population, min_members) < confidence:
        return cap
    while lo < hi:
        mid = (lo + hi) // 2
        if detect_probability(prevalence, mid, population, min_members) >= confidence:
            hi = mid
        else:
            lo = mid + 1
    return lo


@dataclass
class Budget:
    """
    What a given number of requests actually buys.

    Requests, not comments: the index costs one request per 250 records and
    text costs one per comment, so a budget converts to very different sample
    sizes depending on what is being bought.
    """

    requests_per_hour: int = 1000
    hours: float = 1.0
    index_page_size: int = 250

    @property
    def requests(self) -> int:
        return int(self.requests_per_hour * self.hours)

    def metadata_records(self) -> int:
        return self.requests * self.index_page_size

    def text_records(self) -> int:
        return self.requests

    def as_dict(self) -> dict:
        return {"requests": self.requests,
                "metadata_records": self.metadata_records(),
                "text_records": self.text_records()}


def detection_floor(population: int, budget: Budget,
                    confidence: float = 0.95) -> dict:
    """
    The smallest campaign a budget can be expected to find, in both channels.

    Metadata is 250x cheaper per record, so it reaches far smaller campaigns —
    but only for signals visible in metadata (duplicate titles, submission
    timing, organisation concentration). Near-duplicate TEXT detection is
    limited to the text sample, which is the expensive channel and the one
    every published approach assumes it has.
    """
    out = {"population": population, "budget": budget.as_dict(),
           "confidence": confidence}

    for channel, n in (("metadata", min(budget.metadata_records(), population)),
                       ("text", min(budget.text_records(), population))):
        lo, hi = 1, population
        best = None
        while lo <= hi:
            mid = (lo + hi) // 2
            p = mid / population
            if detect_probability(p, n, population) >= confidence:
                best = mid
                hi = mid - 1
            else:
                lo = mid + 1
        out[channel] = {
            "sample": n,
            "smallest_detectable_campaign": best,
            "as_share_of_docket": (best / population) if best else None,
        }
    return out


def table(populations: list[int], prevalences: list[float],
          sample: int) -> list[dict]:
    """Detection probability across docket sizes and campaign shares."""
    rows = []
    for N in populations:
        for p in prevalences:
            rows.append({
                "population": N, "prevalence": p,
                "campaign_size": round(p * N),
                "sample": sample,
                "detect_probability": detect_probability(p, sample, N),
            })
    return rows

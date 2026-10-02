"""
Signals visible in metadata, and the distinction duplicate-counting misses.

Why duplicate detection answers the wrong question
--------------------------------------------------
Every published analysis of flooded dockets reports duplicate rates. The FCC's
net neutrality docket was 17.4% unique; the Pew analysis found 94% of comments
submitted more than once. Those numbers are real and they are routinely read as
evidence of fraud.

They are not. **Coordination is legal and often legitimate.** When an advocacy
organisation sends an action alert and fifty thousand members submit the same
template, that is fifty thousand real people exercising a real right, and the
duplicate rate is 100%. Agencies have said repeatedly that comments are not
votes and that identical submissions are not improper.

What was wrong at the FCC was different: the New York Attorney General found
roughly 18 million comments **filed under the names of people who had not
submitted them**, including the dead. The offence is misattribution, not
repetition.

So the question a detector should answer is not "are these comments identical"
— that is cheap and already known — but:

    does this bloc look like real people who agreed, or like records
    manufactured to look like people?

Those two produce the same duplicate rate and different metadata.

What separates them
-------------------
A genuine campaign inherits its shape from a membership list and an email
send. A fabricated one inherits its shape from whatever generated it.

    timing       Real people respond to an alert over hours and days, with a
                 diurnal cycle and a long tail. A script submits at a rate it
                 chooses, which tends to be too regular or too fast.

    geography    Real members are distributed like an organisation's
                 membership — clustered, uneven, correlated with where it
                 organises. Fabricated records tend to be distributed like a
                 population list, or not at all.

    names        Real names have the frequency distribution of real names.
                 Generated ones are drawn from a list, which shows up as an
                 unusual rate of repeats or an unusual absence of them.

Each of these is visible in metadata, which costs 1/250th of what comment text
costs. That is the practical payoff of the sampling result: the channel that
reaches small campaigns is also the channel that carries the signal that
matters.

On what this cannot do
----------------------
None of these proves fabrication. They are consistent with it and inconsistent
with an ordinary membership campaign, which is a weaker claim and the only one
the data supports. A docket flagged here warrants someone asking the
organisation for its send logs; it does not warrant a conclusion.
"""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------

def _parse(ts: str) -> datetime | None:
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S%z",
                "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d"):
        try:
            return datetime.strptime(ts, fmt)
        except (ValueError, TypeError):
            continue
    return None


def interarrival_regularity(timestamps: list[str]) -> dict:
    """
    How regular are the gaps between submissions?

    Human arrivals are roughly Poisson: gaps are exponentially distributed, so
    their coefficient of variation sits near 1. A script submitting on a timer
    produces near-constant gaps and a CV near 0. A burst followed by silence
    pushes CV above 1.

    CV is used rather than a goodness-of-fit test because the sample here is
    whatever the budget bought, often a few hundred, where a formal test has
    little power and a shape statistic still carries information.
    """
    ts = sorted(t for t in (_parse(x) for x in timestamps) if t)
    if len(ts) < 3:
        return {"n": len(ts), "cv": None, "verdict": "too few"}

    gaps = [(ts[i + 1] - ts[i]).total_seconds() for i in range(len(ts) - 1)]
    gaps = [g for g in gaps if g >= 0]
    if not gaps:
        return {"n": len(ts), "cv": None, "verdict": "no spread"}

    mean = sum(gaps) / len(gaps)
    if mean == 0:
        return {"n": len(ts), "cv": 0.0, "verdict": "simultaneous"}
    var = sum((g - mean) ** 2 for g in gaps) / len(gaps)
    cv = math.sqrt(var) / mean

    if cv < 0.35:
        verdict = "machine-regular"
    elif cv > 2.5:
        verdict = "bursty"
    else:
        verdict = "human-like"
    return {"n": len(ts), "mean_gap_s": mean, "cv": cv, "verdict": verdict,
            "span_hours": (ts[-1] - ts[0]).total_seconds() / 3600}


def hour_of_day_profile(timestamps: list[str]) -> dict:
    """
    Do submissions follow a daily cycle?

    People sleep. A campaign driven by an email send shows a diurnal pattern;
    a script running on a schedule does not. Reported as the share falling in
    the quietest six hours, which is near zero for human activity and near a
    quarter for uniform.
    """
    parsed = sorted(t for t in (_parse(x) for x in timestamps) if t)
    if len(parsed) < 12:
        return {"n": len(parsed), "night_share": None, "verdict": "too few"}

    # A bloc that never spans a day has no diurnal cycle to be missing.
    # Without this guard a burst lasting thirteen minutes reads as "diurnal"
    # simply because it happened during the day — scoring the fastest, most
    # obviously scripted blocs as the most human.
    span_h = (parsed[-1] - parsed[0]).total_seconds() / 3600
    if span_h < 24:
        return {"n": len(parsed), "span_hours": span_h, "night_share": None,
                "verdict": "span under a day: no cycle to test"}

    hours = [t.hour for t in parsed]
    counts = Counter(hours)
    quietest = sorted(range(24), key=lambda h: counts.get(h, 0))[:6]
    night = sum(counts.get(h, 0) for h in quietest) / len(hours)
    return {"n": len(hours), "night_share": night,
            "verdict": "flat (no diurnal cycle)" if night > 0.18 else "diurnal"}


# ---------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------

def name_distribution(names: list[str]) -> dict:
    """
    Do these look like real names drawn from a population?

    Real name frequencies are heavy-tailed: a few Smiths, a long tail of
    singletons. Names drawn from a generator list repeat at a rate set by the
    list size, which is usually either far too high or suspiciously uniform.

    Reported as the share of names appearing exactly once. Real samples of a
    few hundred US names run high; a small generator list runs much lower.
    """
    clean = [n.strip().lower() for n in names if n and n.strip()]
    if len(clean) < 20:
        return {"n": len(clean), "singleton_share": None, "verdict": "too few"}
    c = Counter(clean)
    singles = sum(1 for v in c.values() if v == 1)
    share = singles / len(c)
    top = c.most_common(1)[0]
    return {"n": len(clean), "distinct": len(c), "singleton_share": share,
            "most_common": {"name": top[0][:40], "count": top[1]},
            "verdict": "repetitive" if share < 0.75 else "varied"}


# ---------------------------------------------------------------------------
# Geography
# ---------------------------------------------------------------------------

# 2020 census shares, rounded. Used only as a reference distribution: a bloc
# matching national population more closely than any real membership does is
# the signature of records generated from a population list.
US_POPULATION_SHARE = {
    "CA": 0.1191, "TX": 0.0874, "FL": 0.0647, "NY": 0.0602, "PA": 0.0386,
    "IL": 0.0382, "OH": 0.0352, "GA": 0.0320, "NC": 0.0314, "MI": 0.0300,
}


def geographic_profile(states: list[str]) -> dict:
    """
    Is this bloc shaped like a membership, or like a population?

    An organisation's members cluster where it organises. Records generated
    from a population list match census shares closely, which no real
    membership does.

    Reported as chi-square-style divergence from census shares across the ten
    largest states. LOW divergence is the suspicious direction, which inverts
    the usual reading and is why it is stated explicitly.
    """
    clean = [s.strip().upper() for s in states if s and s.strip()]
    if len(clean) < 30:
        return {"n": len(clean), "divergence": None, "verdict": "too few"}

    c = Counter(clean)
    # Normalise over the reference states only.
    #
    # Dividing by the full count compared a bloc spread across fifty states
    # against shares summing to 0.46, so every bloc looked divergent and the
    # signal never fired. The comparison has to be like for like: of the
    # records that fall in these ten states, are they split as the census
    # splits them?
    in_ref = sum(c.get(st, 0) for st in US_POPULATION_SHARE)
    if in_ref < 20:
        return {"n": len(clean), "divergence": None,
                "verdict": "too few in reference states"}

    ref_total = sum(US_POPULATION_SHARE.values())
    div = 0.0
    for st, share in US_POPULATION_SHARE.items():
        exp_share = share / ref_total
        obs = c.get(st, 0) / in_ref
        div += (obs - exp_share) ** 2 / exp_share

    # Compare against the SAMPLING NOISE FLOOR, not a fixed number.
    #
    # Even a bloc drawn exactly from census shares shows divergence, because
    # a finite sample does not reproduce a distribution perfectly. That floor
    # is about (k-1)/n for k categories. A fixed threshold of 0.02 was below
    # the floor at realistic sample sizes, so the signal could never fire:
    # a perfectly census-matched bloc of 280 records scores around 0.03 by
    # noise alone.
    k = len(US_POPULATION_SHARE)
    noise_floor = (k - 1) / in_ref
    ratio = div / noise_floor if noise_floor > 0 else float("inf")

    total = len(clean)
    return {"n": total, "in_reference_states": in_ref,
            "distinct_states": len(c), "divergence": div,
            "noise_floor": noise_floor, "ratio_to_noise": ratio,
            "verdict": ("matches population too closely" if ratio < 2.5
                        else "clustered like a membership")}


# ---------------------------------------------------------------------------
# Combining
# ---------------------------------------------------------------------------

@dataclass
class Assessment:
    """
    What the metadata supports, stated at the strength it supports it.

    Never "fabricated". The signals are consistent with fabrication and
    inconsistent with an ordinary membership campaign; establishing more
    requires the organisation's send logs, which is a request this can
    justify and not a conclusion it can reach.
    """

    flags: list[str] = field(default_factory=list)
    detail: dict = field(default_factory=dict)

    @property
    def score(self) -> int:
        return len(self.flags)

    def as_dict(self) -> dict:
        return {"flags": self.flags, "n_flags": self.score,
                "reading": self.reading(), "detail": self.detail}

    def reading(self) -> str:
        if not self.flags:
            return ("Nothing in the metadata distinguishes this bloc from an "
                    "ordinary coordinated campaign, which is lawful.")
        if self.score == 1:
            return ("One signal is unusual. Weak on its own — ordinary "
                    "campaigns produce odd-looking metadata often enough.")
        return ("Several independent signals are inconsistent with an ordinary "
                "membership campaign. This warrants asking the organisation "
                "for its send logs. It does not establish fabrication.")


def assess(timestamps: list[str], names: list[str],
           states: list[str]) -> Assessment:
    """Run every metadata signal and report what they jointly support."""
    a = Assessment()

    t = interarrival_regularity(timestamps)
    a.detail["timing"] = t
    if t.get("verdict") == "machine-regular":
        a.flags.append("submission gaps are too regular for human arrivals")

    h = hour_of_day_profile(timestamps)
    a.detail["hours"] = h
    if h.get("verdict", "").startswith("flat"):
        a.flags.append("no diurnal cycle: submissions continue overnight")

    n = name_distribution(names)
    a.detail["names"] = n
    if n.get("verdict") == "repetitive":
        a.flags.append("names repeat more than a real population would")

    g = geographic_profile(states)
    a.detail["geography"] = g
    if g.get("verdict", "").startswith("matches"):
        a.flags.append("state distribution tracks census shares, not membership")

    return a

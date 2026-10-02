"""
What it costs to flood a docket, against what it costs to check one.

Why this is the number that matters
-----------------------------------
`sampling.py` shows a budget cannot reach small campaigns. `signals.py` shows
metadata catches only careless ones. Both are capability statements, and a
capability gap can in principle be closed by trying harder.

This one cannot, because it is an economic gap and it runs the wrong way.

The two sides
-------------
**Writing a comment** is a token purchase. A few hundred words from a current
model costs a fraction of a cent, and a campaign is that cost times its size.
The work is embarrassingly parallel and needs no human.

**Checking a comment** is a request against a rate-limited API. One request per
comment body, a thousand an hour, with no bulk download and — GSA has told
researchers — no prospect of a higher limit. The auditor's constraint is wall
clock, and wall clock does not parallelise: ten auditors with ten keys still
face the same hourly ceiling per key, and the agency has no privileged channel
of its own.

So the attacker buys comments with money, which scales, and the auditor buys
scrutiny with time, which does not.

What the asymmetry is NOT
-------------------------
It is not an argument that flooding is cheap in absolute terms — a
multi-million comment campaign costs real money. It is that the *ratio* moves
against the auditor as the campaign grows, and the point where auditing a
docket costs more than flooding it arrives at a size well inside what has
already happened.

Costs below are per-comment token prices at published list rates and the
documented API limit. They are inputs, exposed rather than buried, and the
conclusion survives any plausible value because the two sides differ by orders
of magnitude rather than by a factor.
"""

from __future__ import annotations

from dataclasses import dataclass

from .sampling import sample_needed


@dataclass(frozen=True)
class Prices:
    """
    Published inputs, stated so they can be disputed.

    `tokens_per_comment` covers a few hundred words of plausible public
    comment plus the prompt. `usd_per_million_tokens` is a mid-tier list
    price; a cheaper model roughly halves it and a frontier one roughly
    triples it, neither of which changes the sign of anything below.
    """

    tokens_per_comment: int = 600
    usd_per_million_tokens: float = 3.0

    requests_per_hour: int = 1000
    """The documented Regulations.gov limit."""

    auditor_usd_per_hour: float = 75.0
    """Fully loaded cost of someone qualified to interpret the result. An
    estimate, and the weakest number here."""

    submission_usd_per_comment: float = 0.0
    """Cost of actually filing. Zero today: there is no fee, no rate limit
    published for submission, and no proof-of-personhood. This being zero is
    the policy lever, and it is why it appears as a parameter."""

    def cost_to_write(self, n: int) -> float:
        tok = n * self.tokens_per_comment
        return tok / 1e6 * self.usd_per_million_tokens + n * self.submission_usd_per_comment

    def cost_to_read(self, n: int) -> float:
        hours = n / self.requests_per_hour
        return hours * self.auditor_usd_per_hour


@dataclass
class Asymmetry:
    campaign_size: int
    docket_size: int
    attacker_usd: float
    auditor_usd: float
    auditor_hours: float
    sample_needed: int
    detectable: bool

    @property
    def ratio(self) -> float:
        """How many dollars of audit per dollar of attack."""
        return self.auditor_usd / self.attacker_usd if self.attacker_usd else float("inf")

    def as_dict(self) -> dict:
        return {
            "campaign_size": self.campaign_size,
            "docket_size": self.docket_size,
            "attacker_usd": round(self.attacker_usd, 2),
            "auditor_usd": round(self.auditor_usd, 2),
            "auditor_hours": round(self.auditor_hours, 1),
            "sample_needed": self.sample_needed,
            "detectable_within_a_week": self.detectable,
            "audit_dollars_per_attack_dollar": round(self.ratio, 1),
        }


def asymmetry(campaign_size: int, docket_size: int,
              prices: Prices | None = None,
              confidence: float = 0.95,
              week_hours: float = 40.0) -> Asymmetry:
    """
    What each side spends for one campaign on one docket.

    The auditor's figure is the cost of sampling enough to have a 95% chance
    of seeing the campaign at all — not of confirming it, not of
    investigating it, and not of auditing the rest of the docket. It is a
    floor on the auditor's side and a ceiling on nothing.
    """
    p = prices or Prices()
    need = sample_needed(campaign_size / docket_size, confidence, docket_size)
    hours = need / p.requests_per_hour

    return Asymmetry(
        campaign_size=campaign_size, docket_size=docket_size,
        attacker_usd=p.cost_to_write(campaign_size),
        auditor_usd=p.cost_to_read(need),
        auditor_hours=hours,
        sample_needed=need,
        detectable=(hours <= week_hours),
    )


def crossover(docket_size: int, prices: Prices | None = None,
              lo: int = 10, hi: int | None = None) -> dict:
    """
    The campaign size at which auditing costs more than attacking.

    Below it the defender is ahead; above it every additional comment widens
    the gap. Found by bisection on the ratio, which is monotone in campaign
    size because the attacker's cost is linear while the auditor's falls as
    the campaign becomes easier to find.
    """
    p = prices or Prices()
    hi = hi or docket_size

    if asymmetry(hi, docket_size, p).ratio > 1:
        return {"docket_size": docket_size, "crossover": None,
                "note": "auditing costs more than attacking at every size tested"}

    best = None
    a, b = lo, hi
    while a <= b:
        mid = (a + b) // 2
        if asymmetry(mid, docket_size, p).ratio <= 1:
            best = mid
            b = mid - 1
        else:
            a = mid + 1

    return {"docket_size": docket_size, "crossover": best,
            "note": ("campaigns below this size cost more to find than to "
                     "create" if best else "no crossover in range")}


def submission_fee_effect(campaign_size: int, docket_size: int,
                          fees: list[float]) -> list[dict]:
    """
    What a nominal submission cost would do.

    The attacker's advantage comes from writing being nearly free. A fee
    changes the slope on the side that scales, and it is the only lever in
    this model that does — a faster API helps the auditor linearly while the
    attacker's cost stays linear too, so the ratio is unchanged.

    This is a model of an economic effect, not a policy recommendation. A fee
    on public comment has obvious and serious costs to the people the process
    exists to serve, and nothing here weighs those.
    """
    out = []
    for fee in fees:
        p = Prices(submission_usd_per_comment=fee)
        a = asymmetry(campaign_size, docket_size, p)
        out.append({"fee_usd": fee, **a.as_dict()})
    return out

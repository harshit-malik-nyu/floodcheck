"""
Blocs with known provenance, to characterise the signals.

The point is not to claim anything about real dockets. It is to answer a
narrower question first: **if a bloc were fabricated, would these metadata
signals see it?** A detector that cannot separate constructed cases has no
business being pointed at real ones.

Three generators, differing only in how the records were produced:

    membership     a real advocacy campaign. An email goes out, members
                   respond over days, they sleep, and they cluster where the
                   organisation organises.
    scripted       records submitted on a timer from a generated identity
                   list. The duplicate rate is identical to the above.
    careful        a fabrication that has read this file: paced irregularly,
                   paused overnight, drawn from a large name list.

The third exists because a detector evaluated only against a naive adversary
measures the adversary.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta

FIRST = ["James","Mary","Robert","Patricia","John","Jennifer","Michael","Linda",
         "David","Elizabeth","William","Barbara","Richard","Susan","Joseph",
         "Jessica","Thomas","Sarah","Charles","Karen","Daniel","Nancy","Matthew",
         "Lisa","Anthony","Betty","Mark","Margaret","Donald","Sandra"]
LAST = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
        "Rodriguez","Martinez","Hernandez","Lopez","Gonzalez","Wilson","Anderson",
        "Thomas","Taylor","Moore","Jackson","Martin","Lee","Perez","Thompson",
        "White","Harris","Sanchez","Clark","Ramirez","Lewis","Robinson"]

# Where an organisation actually has members: concentrated, uneven.
MEMBERSHIP_STATES = {"CA":0.21,"NY":0.14,"MA":0.09,"WA":0.08,"OR":0.07,
                     "VT":0.06,"MN":0.06,"CO":0.05,"IL":0.05,"TX":0.04,
                     "FL":0.04,"PA":0.04,"MI":0.03,"OH":0.02,"GA":0.02}
CENSUS_STATES = {"CA":0.1191,"TX":0.0874,"FL":0.0647,"NY":0.0602,"PA":0.0386,
                 "IL":0.0382,"OH":0.0352,"GA":0.0320,"NC":0.0314,"MI":0.0300,
                 "NJ":0.0266,"VA":0.0259,"WA":0.0232,"AZ":0.0216,"MA":0.0209}


def _pick(dist: dict, rng: random.Random) -> str:
    r, acc = rng.random() * sum(dist.values()), 0.0
    for k, v in dist.items():
        acc += v
        if r <= acc:
            return k
    return list(dist)[-1]


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def membership_campaign(n: int, seed: int = 0, days: float = 4.0) -> dict:
    """
    A lawful advocacy campaign: identical text, real people.

    Arrivals follow the email send — a spike, then decay — and stop overnight,
    because people sleep. The duplicate rate is 100%, exactly as in a
    fabricated bloc.
    """
    rng = random.Random(seed)
    start = datetime(2026, 3, 2, 9, 0, 0)
    ts, names, states = [], [], []
    for _ in range(n):
        # exponential decay after the send, rejected into waking hours
        for _ in range(40):
            offset = rng.expovariate(1.0 / (days * 24 * 3600 / 3))
            when = start + timedelta(seconds=offset)
            if 7 <= when.hour <= 23:
                break
        ts.append(_iso(when))
        names.append(f"{rng.choice(FIRST)} {rng.choice(LAST)}")
        states.append(_pick(MEMBERSHIP_STATES, rng))
    return {"timestamps": ts, "names": names, "states": states,
            "provenance": "membership"}


def scripted_campaign(n: int, seed: int = 0, rate_per_s: float = 0.5) -> dict:
    """
    Records submitted on a timer from a generated identity list.

    Same duplicate rate as the lawful campaign, different everything else:
    near-constant gaps, no night, names from a small pool, geography drawn
    from census shares.
    """
    rng = random.Random(seed)
    t = datetime(2026, 3, 2, 2, 0, 0)
    pool = [f"{rng.choice(FIRST)} {rng.choice(LAST)}" for _ in range(max(8, n // 12))]
    ts, names, states = [], [], []
    for _ in range(n):
        t += timedelta(seconds=1.0 / rate_per_s * rng.uniform(0.92, 1.08))
        ts.append(_iso(t))
        names.append(rng.choice(pool))
        states.append(_pick(CENSUS_STATES, rng))
    return {"timestamps": ts, "names": names, "states": states,
            "provenance": "scripted"}


def careful_campaign(n: int, seed: int = 0, days: float = 4.0) -> dict:
    """
    A fabrication built by someone who knows what is being measured.

    Irregular pacing, overnight pause, a name pool large enough to look like a
    population, geography drawn from a plausible membership rather than the
    census. Included because evaluating only against the naive version
    measures the adversary rather than the detector.
    """
    rng = random.Random(seed)
    start = datetime(2026, 3, 2, 9, 0, 0)
    # Names are drawn fresh from the full space, exactly as the membership
    # generator does.
    #
    # The first version sampled from a pre-generated pool of 3n names, which
    # was itself drawn from the same space — so the pool contained duplicates
    # and its effective diversity was LOWER than drawing fresh. The "careful"
    # adversary was less careful than the lawful campaign on the one axis it
    # was supposed to be careful about, and the name flag it earned was a
    # defect in this generator rather than a signal.
    ts, names, states = [], [], []
    for _ in range(n):
        for _ in range(40):
            offset = rng.expovariate(1.0 / (days * 24 * 3600 / 3))
            when = start + timedelta(seconds=offset)
            if 7 <= when.hour <= 23:
                break
        ts.append(_iso(when))
        names.append(f"{rng.choice(FIRST)} {rng.choice(LAST)}")
        states.append(_pick(MEMBERSHIP_STATES, rng))
    return {"timestamps": ts, "names": names, "states": states,
            "provenance": "careful"}


GENERATORS = {"membership": membership_campaign,
              "scripted": scripted_campaign,
              "careful": careful_campaign}

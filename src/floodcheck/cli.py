"""
Command line interface.

Three questions, answerable without touching a docket:

    ceiling    what can a budget of this size find at all?
    cost       what does a campaign of this size cost each side?
    signals    what do the metadata signals do on blocs of known provenance?
"""

from __future__ import annotations

import argparse
import json
import sys

from .economics import Prices, asymmetry, crossover
from .sampling import Budget, detect_probability, detection_floor, sample_needed
from .signals import assess
from .synthetic import GENERATORS


def cmd_ceiling(args) -> int:
    f = detection_floor(args.docket, Budget(hours=args.hours))
    if args.json:
        print(json.dumps(f, indent=2))
        return 0
    print(f"docket of {args.docket:,}, {args.hours} hour(s) of budget\n")
    for ch in ("metadata", "text"):
        d = f[ch]
        print(f"  {ch:9s} sample {d['sample']:>9,}  finds campaigns down to "
              f"{d['smallest_detectable_campaign']:>9,} "
              f"({d['as_share_of_docket']:.4%})")
    print("\n  A perfect detector needs two members of a campaign in its sample.")
    print("  These are ceilings; every real detector does worse.")
    return 0


def cmd_cost(args) -> int:
    a = asymmetry(args.campaign, args.docket)
    c = crossover(args.docket)
    if args.json:
        print(json.dumps({**a.as_dict(), "crossover": c["crossover"]}, indent=2))
        return 0
    d = a.as_dict()
    print(f"campaign of {args.campaign:,} on a docket of {args.docket:,}\n")
    print(f"  costs to create        ${d['attacker_usd']:>12,.2f}")
    print(f"  costs to find          ${d['auditor_usd']:>12,.2f}"
          f"   ({d['auditor_hours']:.1f} hours of polling)")
    print(f"  audit $ per attack $    {d['audit_dollars_per_attack_dollar']:>12,.1f}")
    if c["crossover"]:
        print(f"\n  Below {c['crossover']:,} comments, finding costs more than creating.")
    return 0


def cmd_signals(args) -> int:
    rows = []
    for name, gen in GENERATORS.items():
        scores = []
        for seed in range(1, args.seeds + 1):
            b = gen(args.size, seed=seed)
            a = assess(b["timestamps"], b["names"], b["states"])
            scores.append(a.score)
            rows.append({"provenance": name, "seed": seed, **a.as_dict()})
        print(f"  {name:12s} flags across {args.seeds} seeds: {scores}")
    if args.json:
        print(json.dumps(rows, indent=2))
        return 0
    print("\n  All three blocs submit identical text, so duplicate counting")
    print("  reports 100% for each and cannot tell them apart.")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="floodcheck",
        description="What a comment docket can be shown to be, from a sample "
                    "you can afford.")
    ap.add_argument("--json", action="store_true")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("ceiling", help="what a budget can find at all")
    p.add_argument("--docket", type=int, default=1_000_000)
    p.add_argument("--hours", type=float, default=1.0)
    p.set_defaults(func=cmd_ceiling)

    p = sub.add_parser("cost", help="what a campaign costs each side")
    p.add_argument("--campaign", type=int, default=1000)
    p.add_argument("--docket", type=int, default=1_000_000)
    p.set_defaults(func=cmd_cost)

    p = sub.add_parser("signals", help="metadata signals on known provenance")
    p.add_argument("--size", type=int, default=400)
    p.add_argument("--seeds", type=int, default=5)
    p.set_defaults(func=cmd_signals)

    args = ap.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

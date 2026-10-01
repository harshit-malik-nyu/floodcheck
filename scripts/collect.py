#!/usr/bin/env python3
"""
Collect public comments within the budget an auditor actually has.

The constraint IS the problem
-----------------------------
Regulations.gov allows 1,000 requests an hour. Comment metadata comes 250 to a
page, so a docket's index is cheap. Comment **text** comes one request at a
time, so reading a million-comment docket would take forty days of continuous
polling, and GSA has told researchers there is no bulk download and no rate
limit increase.

That means nobody — including the agency — reads these dockets in full. Any
claim about a docket's integrity is therefore a claim from a sample, whether
or not whoever makes it says so.

So this collector does not try to beat the limit. It spends it deliberately
and records exactly what it bought, because the sampling design is the thing
the rest of the project reasons about.

What it pulls, and why in this order
------------------------------------
    1. the docket index        cheap, and it establishes the population size
    2. comment metadata        250 per request: submitter, date, organisation,
                               whether there are attachments
    3. comment text            one request each, and the expensive part

Metadata alone supports a surprising amount: submission timing, duplicate
titles, organisation concentration. Text is needed for near-duplicate
detection, which is where the budget goes.

Every run writes its own cost
-----------------------------
Requests spent, records obtained, and what was skipped. A sample whose cost is
not recorded cannot be reasoned about later, and this project's whole argument
is about what a given budget can establish.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

API = "https://api.regulations.gov/v4"
ROOT = Path(__file__).resolve().parents[1]


@dataclass
class Budget:
    """
    Requests are the scarce resource, so they are counted like money.

    `limit` is deliberately below the documented 1,000/hour. A collector that
    runs to exactly the ceiling gets throttled mid-run and leaves a partial
    file with no record of where it stopped.
    """

    limit: int = 850
    spent: int = 0
    started: float = field(default_factory=time.time)

    def spend(self, n: int = 1) -> bool:
        if self.spent + n > self.limit:
            return False
        self.spent += n
        return True

    def left(self) -> int:
        return max(0, self.limit - self.spent)

    def as_dict(self) -> dict:
        return {"limit": self.limit, "spent": self.spent,
                "elapsed_s": round(time.time() - self.started, 1)}


class Client:
    """Thin wrapper that respects the limit and records every failure."""

    def __init__(self, api_key: str, budget: Budget, pause: float = 0.4):
        self.key = api_key
        self.budget = budget
        self.pause = pause
        self.errors: list[dict] = []

    def get(self, path: str, params: dict) -> dict | None:
        if not self.budget.spend():
            return None
        q = dict(params)
        q["api_key"] = self.key
        url = f"{API}/{path}?" + urllib.parse.urlencode(q, doseq=True)
        try:
            with urllib.request.urlopen(url, timeout=45) as r:
                time.sleep(self.pause)
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            # 429 means the shared hourly window is gone; stop rather than
            # hammer it, and say so in the manifest.
            self.errors.append({"path": path, "status": e.code,
                                "body": e.read()[:200].decode("utf-8", "replace")})
            if e.code == 429:
                self.budget.spent = self.budget.limit
            return None
        except Exception as exc:                       # noqa: BLE001
            self.errors.append({"path": path, "error": type(exc).__name__})
            return None


def find_dockets(client: Client, n: int = 10) -> list[dict]:
    """
    Dockets with the most comments, which is where flooding would show.

    Sorted by comment count rather than recency: a docket nobody commented on
    cannot tell you anything about mass commenting.
    """
    out = []
    page = client.get("dockets", {
        "sort": "-lastModifiedDate", "page[size]": 100,
    })
    if not page:
        return out
    for d in page.get("data", []):
        a = d.get("attributes", {})
        out.append({"id": d.get("id"), "title": (a.get("title") or "")[:160],
                    "agency": a.get("agencyId"),
                    "modified": a.get("lastModifiedDate")})
    return out[:n]


def comment_index(client: Client, docket_id: str, cap: int = 2000) -> list[dict]:
    """
    Metadata for a docket's comments: 250 per request, so the whole index of
    a mid-sized docket costs a handful of calls.
    """
    rows, page_no = [], 1
    while len(rows) < cap:
        page = client.get("comments", {
            "filter[docketId]": docket_id,
            "page[size]": 250, "page[number]": page_no,
            "sort": "postedDate",
        })
        if not page or not page.get("data"):
            break
        for c in page["data"]:
            a = c.get("attributes", {})
            rows.append({
                "id": c.get("id"),
                "title": a.get("title"),
                "posted": a.get("postedDate"),
                "agency": a.get("agencyId"),
                "withdrawn": a.get("withdrawn"),
            })
        meta = page.get("meta", {})
        if page_no >= meta.get("totalPages", 1) or page_no >= 20:
            break
        page_no += 1
    return rows


def comment_text(client: Client, ids: list[str]) -> list[dict]:
    """
    The expensive part: one request per comment.

    Takes ids in the order given. Sampling is the caller's decision and is
    recorded in the manifest, because a convenience sample presented as a
    random one is the single easiest way to make this kind of analysis wrong.
    """
    out = []
    for cid in ids:
        if client.budget.left() <= 5:
            break
        d = client.get(f"comments/{cid}", {})
        if not d:
            continue
        a = d.get("data", {}).get("attributes", {})
        out.append({
            "id": cid,
            "comment": a.get("comment"),
            "posted": a.get("postedDate"),
            "received": a.get("receiveDate"),
            "submitter": a.get("submitterName"),
            "organization": a.get("organization"),
            "city": a.get("city"), "state": a.get("stateProvinceRegion"),
            "country": a.get("country"),
            "duplicate_comments": a.get("duplicateComments"),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--docket", default="", help="docket id; blank to discover")
    ap.add_argument("--index-cap", type=int, default=2000)
    ap.add_argument("--text-sample", type=int, default=300)
    ap.add_argument("--budget", type=int, default=850)
    ap.add_argument("--out", default=str(ROOT / "evidence"))
    args = ap.parse_args()

    key = os.environ.get("REGULATIONS_API_KEY", "").strip()
    if not key:
        print("REGULATIONS_API_KEY is not set. This collector calls a real "
              "API; it does not fabricate records.", file=sys.stderr)
        return 1

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    budget = Budget(limit=args.budget)
    client = Client(key, budget)

    manifest: dict = {"collected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ",
                                                    time.gmtime())}

    docket = args.docket
    if not docket:
        found = find_dockets(client)
        manifest["discovered_dockets"] = found
        (out / "dockets.json").write_text(json.dumps(found, indent=2))
        if not found:
            manifest["budget"] = budget.as_dict()
            manifest["errors"] = client.errors[:10]
            (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
            print("no dockets returned; see manifest", file=sys.stderr)
            return 1
        docket = found[0]["id"]

    print(f"docket: {docket}", flush=True)
    index = comment_index(client, docket, cap=args.index_cap)
    print(f"  index: {len(index):,} comments ({budget.spent} requests)", flush=True)
    (out / "index.json").write_text(json.dumps(index, indent=2))

    # Sample for text in posting order, which is a CONVENIENCE sample and is
    # labelled as one. Random sampling would cost no more and is the right
    # default; posting order is kept here only because timing-cluster
    # detection needs contiguous runs.
    ids = [r["id"] for r in index][:args.text_sample]
    texts = comment_text(client, ids)
    print(f"  text: {len(texts):,} comments ({budget.spent} requests total)",
          flush=True)
    (out / "comments.json").write_text(json.dumps(texts, indent=2))

    manifest.update({
        "docket": docket,
        "index_records": len(index),
        "text_records": len(texts),
        "text_sampling": "first N in posting order (CONVENIENCE SAMPLE)",
        "budget": budget.as_dict(),
        "errors": client.errors[:10],
        "note": ("Comment text costs one request each; the index costs one per "
                 "250. Any claim about this docket is a claim from this "
                 "sample, and its cost is recorded so that can be checked."),
    })
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps(manifest["budget"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

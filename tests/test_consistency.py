"""
Every headline figure in the README must regenerate from the code.

Four modules were built in sequence, each producing numbers that went straight
into the document. Nothing stops a later change from silently invalidating an
earlier claim — a parameter moves, the README keeps the old figure, and the
repository quietly starts lying.

These recompute the load-bearing figures and assert the document still matches.
Tolerant on the last digit, strict on the claim: if a finding reverses, a test
fails.

One of them exists because the claim it checks was already wrong once. The
README said metadata was 250x cheaper and let that stand for every non-text
signal, when name and geography cost the same as a comment body.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from floodcheck.attribution import break_even_response_rate, compare
from floodcheck.economics import asymmetry, crossover
from floodcheck.sampling import Budget, detect_probability, detection_floor

ROOT = Path(__file__).resolve().parents[1]


def readme() -> str:
    return (ROOT / "README.md").read_text()


def cites(text: str, value: float, tol: float = 0.02) -> bool:
    """Does the document quote a percentage within tolerance of this?"""
    for m in re.finditer(r"([0-9]+\.?[0-9]*)%", text):
        if abs(float(m.group(1)) / 100 - value) <= tol:
            return True
    return False


def cites_int(text: str, value: int, tol: float = 0.02) -> bool:
    """Does the document quote this integer, with or without separators?"""
    for m in re.finditer(r"([0-9][0-9,]*)", text):
        try:
            v = int(m.group(1).replace(",", ""))
        except ValueError:
            continue
        if v and abs(v - value) / max(v, value) <= tol:
            return True
    return False


class TestSamplingFigures:

    def test_the_index_floor_on_the_fcc_docket(self):
        f = detection_floor(22_152_242, Budget(hours=1.0))
        assert cites_int(readme(), f["index"]["smallest_detectable_campaign"])

    def test_the_detail_and_text_floor(self):
        f = detection_floor(22_152_242, Budget(hours=1.0))
        assert cites_int(readme(), f["text"]["smallest_detectable_campaign"])

    def test_the_cheap_channel_is_not_claimed_to_carry_names(self):
        """
        REGRESSION on a claim. The README once said metadata was 250x cheaper
        and let that cover every non-text signal; submitter name and
        geography come from the per-comment endpoint at one request each.
        """
        text = readme()
        assert "cheap and thin" in text or "cheap channel is cheap" in text
        assert "per-comment endpoint" in text

    def test_a_small_campaign_remains_unreachable(self):
        p = detect_probability(1000 / 1_000_000, 1000, 1_000_000)
        assert p < 0.4
        assert cites(readme(), p, tol=0.05)


class TestEconomicsFigures:

    def test_the_crossover_on_a_million_comment_docket(self):
        c = crossover(1_000_000)["crossover"]
        assert cites_int(readme(), c)

    def test_the_crossover_on_the_fcc_docket(self):
        c = crossover(22_152_242)["crossover"]
        assert cites_int(readme(), c)

    def test_the_extreme_ratio_is_current(self):
        a = asymmetry(200, 1_000_000)
        assert a.ratio > 1000
        assert cites_int(readme(), round(a.ratio))

    def test_the_direction_still_holds(self):
        """
        Large campaigns favour the auditor, small ones favour the attacker.
        If that ever reverses the whole argument changes.
        """
        assert asymmetry(500_000, 1_000_000).ratio < 1
        assert asymmetry(200, 1_000_000).ratio > 100


class TestAttributionFigures:

    def test_notification_beats_sampling_on_small_campaigns(self):
        c = compare(200, 1_000_000)
        assert cites(readme(), c.sampling_detect, tol=0.03)
        assert cites(readme(), c.notification_detect, tol=0.03)

    def test_the_fifty_comment_case(self):
        c = compare(50, 1_000_000)
        assert c.sampling_detect < 0.1
        assert c.notification_detect > 0.4

    def test_the_break_even_rates_are_current(self):
        r = break_even_response_rate(1000, 1_000_000)
        assert cites(readme(), r, tol=0.005)

    def test_the_required_rate_still_falls_with_campaign_size(self):
        rates = [break_even_response_rate(k, 1_000_000)
                 for k in (100_000, 10_000, 1_000, 200)]
        assert rates == sorted(rates)


class TestDocumentIntegrity:

    def test_internal_links_resolve(self):
        for name in ("README.md", "docs/against.md"):
            p = ROOT / name
            for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", p.read_text()):
                target = m.group(2).split("#")[0]
                if target.startswith(("http", "mailto:")) or not target:
                    continue
                assert (p.parent / target).resolve().exists(), \
                    f"{name} links to missing {target}"

    def test_the_case_against_leads_with_the_unanswerable_objection(self):
        """
        No real docket has been touched. That has to be first, not buried.
        """
        t = (ROOT / "docs" / "against.md").read_text()
        head = t[:t.index("## 2.")]
        assert "No real docket has been touched" in head
        assert "not fixable from here" in head

    def test_the_fee_result_is_marked_as_not_a_recommendation(self):
        """
        A fee on public comment has serious access costs that nothing here
        weighs, and presenting it beside detection results invites a reading
        the analysis cannot support.
        """
        t = readme()
        assert "not a policy recommendation" in t

    def test_notification_is_marked_as_not_a_proposal(self):
        import floodcheck.attribution as a
        doc = " ".join(a.__doc__.split())
        assert "is not a proposal" in doc

    def test_the_collector_still_refuses_to_fabricate(self):
        src = (ROOT / "scripts" / "collect.py").read_text()
        assert "does not fabricate records" in src

    @pytest.mark.parametrize("claim", [
        "Coordination is legal",
        "misattribution, not repetition",
        "did not need detecting",
    ])
    def test_the_load_bearing_sentences_survive(self, claim):
        """
        Each of these carries an argument the figures only support. If one is
        edited away, the numbers around it stop meaning what they mean.
        """
        assert claim in readme()

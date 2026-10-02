"""
Tests for the cost asymmetry.

A capability gap can be closed by trying harder. An economic gap cannot, and
these pin which one this is.
"""

from __future__ import annotations

from floodcheck.economics import (
    Prices, asymmetry, crossover, submission_fee_effect,
)


class TestPrices:

    def test_writing_scales_with_tokens(self):
        p = Prices()
        assert p.cost_to_write(2000) == 2 * p.cost_to_write(1000)

    def test_reading_scales_with_the_rate_limit(self):
        p = Prices()
        assert p.cost_to_read(2000) == 2 * p.cost_to_read(1000)

    def test_submission_is_free_today(self):
        """
        Zero because there is no fee, no published submission rate limit, and
        no proof of personhood. It is a parameter because that is the lever.
        """
        assert Prices().submission_usd_per_comment == 0.0


class TestAsymmetry:

    def test_small_campaigns_are_wildly_asymmetric(self):
        """
        A 200-comment campaign costs cents to create and thousands of dollars
        of audit time to find — and it is the same size range sampling cannot
        reach. The two findings compound rather than overlap.
        """
        a = asymmetry(200, 1_000_000)
        assert a.ratio > 1000

    def test_large_campaigns_favour_the_auditor(self):
        """A flood that swamps a docket announces itself and is cheap to find."""
        assert asymmetry(500_000, 1_000_000).ratio < 1

    def test_the_ratio_falls_as_the_campaign_grows(self):
        ratios = [asymmetry(k, 1_000_000).ratio
                  for k in (200, 1_000, 5_000, 20_000, 100_000)]
        assert ratios == sorted(ratios, reverse=True)

    def test_the_auditor_figure_is_a_floor_not_an_estimate(self):
        """
        It covers sampling enough to SEE the campaign — not confirming it,
        not investigating it, not auditing the rest of the docket.
        """
        import inspect

        from floodcheck import economics
        doc = " ".join(inspect.getdoc(economics.asymmetry).split())
        assert "floor on the auditor's side" in doc

    def test_it_serialises(self):
        d = asymmetry(1000, 1_000_000).as_dict()
        assert {"attacker_usd", "auditor_usd", "sample_needed",
                "audit_dollars_per_attack_dollar"} <= set(d)


class TestCrossover:

    def test_bigger_dockets_hide_bigger_campaigns(self):
        """
        The size below which finding costs more than creating rises with the
        docket: 14,039 on a million, 66,138 on the FCC's 22 million.
        """
        small = crossover(100_000)["crossover"]
        large = crossover(22_152_242)["crossover"]
        assert large > small

    def test_the_crossover_is_a_real_boundary(self):
        c = crossover(1_000_000)["crossover"]
        assert asymmetry(c, 1_000_000).ratio <= 1
        assert asymmetry(max(10, c // 2), 1_000_000).ratio > 1

    def test_an_absent_crossover_is_reported_not_invented(self):
        out = crossover(1_000_000, lo=10, hi=50)
        assert out["crossover"] is None
        assert "every size tested" in out["note"]


class TestSubmissionFee:

    def test_a_cent_moves_the_ratio_by_an_order_of_magnitude(self):
        """
        The attacker's advantage comes from writing being nearly free, so the
        only lever that changes the slope is one on the side that scales. A
        faster API helps the auditor linearly and leaves the ratio alone.
        """
        rows = {r["fee_usd"]: r for r in
                submission_fee_effect(20_000, 1_000_000, [0.0, 0.01])}
        free = rows[0.0]["audit_dollars_per_attack_dollar"]
        cent = rows[0.01]["audit_dollars_per_attack_dollar"]
        assert cent < free / 4

    def test_the_fee_is_modelled_not_recommended(self):
        """
        A fee on public comment has obvious and serious costs to the people
        the process exists to serve, and nothing here weighs those.
        """
        import inspect

        from floodcheck import economics
        doc = " ".join(inspect.getdoc(economics.submission_fee_effect).split())
        assert "not a policy recommendation" in doc
        assert "nothing here weighs those" in doc

"""
Tests for the sampling ceiling.

These pin a limit that holds for any detector, so they are assertions about
arithmetic rather than about an implementation. Several pin the comparison
that matters: metadata reaches campaigns two orders of magnitude smaller than
text, which inverts what published approaches do.
"""

from __future__ import annotations

import pytest

from floodcheck.sampling import (
    Budget, detect_probability, detection_floor, sample_needed, table,
)


class TestDetectProbability:

    def test_seeing_one_member_is_not_detection(self):
        """
        A campaign is identifiable because its members resemble each other.
        One member in a sample is just a comment.
        """
        one = detect_probability(0.001, 100, min_members=1)
        two = detect_probability(0.001, 100, min_members=2)
        assert two < one

    def test_a_dominant_campaign_is_trivially_visible(self):
        """The FCC's 7.5m bloc would appear in any sample of twenty."""
        assert detect_probability(0.34, 20, 22_152_242) > 0.99

    def test_a_small_campaign_is_invisible_at_an_affordable_sample(self):
        assert detect_probability(0.0002, 1000, 1_000_000) < 0.10

    def test_probability_rises_with_sample_size(self):
        p = [detect_probability(0.005, n, 1_000_000) for n in (100, 500, 2000)]
        assert p == sorted(p)

    def test_probability_rises_with_campaign_size(self):
        p = [detect_probability(x, 1000, 1_000_000) for x in (1e-4, 1e-3, 1e-2)]
        assert p == sorted(p)

    def test_the_exact_form_is_used_when_the_population_is_small(self):
        """
        Sampling without replacement makes draws dependent, and the
        difference shows exactly where a constrained auditor works — small
        populations sampled heavily.
        """
        exact = detect_probability(0.05, 90, population=100)
        approx = detect_probability(0.05, 90)
        assert exact != approx
        assert exact > approx

    def test_boundaries_are_safe(self):
        assert detect_probability(0.0, 1000) == 0.0
        assert detect_probability(0.5, 0) == 0.0
        assert detect_probability(1.0, 5) == 1.0
        assert detect_probability(1.0, 1) == 0.0


class TestSampleNeeded:

    def test_larger_campaigns_need_smaller_samples(self):
        a = sample_needed(0.10, 0.95, 1_000_000)
        b = sample_needed(0.001, 0.95, 1_000_000)
        assert a < b

    def test_the_answer_is_the_cap_when_unreachable(self):
        """
        Honest rather than extrapolated. For a small campaign on a large
        docket, 'more than you can afford' is the answer.
        """
        assert sample_needed(1e-9, 0.99, cap=1000) == 1000

    def test_the_returned_sample_actually_achieves_the_target(self):
        for p in (0.5, 0.05, 0.005):
            n = sample_needed(p, 0.95, 1_000_000)
            assert detect_probability(p, n, 1_000_000) >= 0.95

    def test_it_returns_the_smallest_such_sample(self):
        n = sample_needed(0.01, 0.95, 1_000_000)
        assert detect_probability(0.01, n - 1, 1_000_000) < 0.95


class TestBudget:

    def test_metadata_is_far_cheaper_per_record(self):
        b = Budget(hours=1.0)
        assert b.metadata_records() == 250 * b.text_records()

    def test_hours_scale_the_budget(self):
        assert Budget(hours=2.0).requests == 2 * Budget(hours=1.0).requests


class TestDetectionFloor:

    @pytest.fixture(scope="class")
    def fcc(self):
        return detection_floor(22_152_242, Budget(hours=1.0))

    def test_metadata_reaches_far_smaller_campaigns_than_text(self, fcc):
        """
        THE FINDING. Text near-duplicate detection — what every published
        approach uses — is the worse channel by two orders of magnitude,
        because comment bodies cost 250 times more per record.
        """
        m = fcc["metadata"]["smallest_detectable_campaign"]
        t = fcc["text"]["smallest_detectable_campaign"]
        assert t > 100 * m

    def test_text_sampling_cannot_see_a_campaign_under_half_a_percent(self, fcc):
        assert fcc["text"]["as_share_of_docket"] > 0.004

    def test_the_floor_is_a_ceiling_on_any_detector(self):
        """
        The number is derived from sampling alone. A perfect detector that
        recognises coordination from any two members achieves exactly this
        and no more; every real detector does worse.
        """
        f = detection_floor(1_000_000, Budget(hours=1.0))
        k = f["text"]["smallest_detectable_campaign"]
        assert detect_probability(k / 1_000_000, 1000, 1_000_000) >= 0.95

    def test_a_longer_audit_lowers_the_floor(self):
        one = detection_floor(1_000_000, Budget(hours=1))
        ten = detection_floor(1_000_000, Budget(hours=10))
        assert (ten["text"]["smallest_detectable_campaign"]
                < one["text"]["smallest_detectable_campaign"])


class TestTable:

    def test_it_covers_the_grid(self):
        rows = table([10_000, 1_000_000], [0.01, 0.1], 1000)
        assert len(rows) == 4
        assert all("detect_probability" in r for r in rows)

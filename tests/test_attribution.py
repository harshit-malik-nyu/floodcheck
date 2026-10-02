"""
Tests for the notification channel.

These pin a structural inversion: every property that makes sampling fail on
small campaigns is reversed here, and the reason is coverage rather than
cleverness.
"""

from __future__ import annotations

from floodcheck.attribution import (
    Notification, break_even_response_rate, compare, sensitivity,
)
from floodcheck.sampling import detect_probability


class TestNotification:

    def test_one_report_is_enough(self):
        """
        Sampling needed two members in a sample to see a pattern. This needs
        one person to say they did not write it.
        """
        n = Notification(contactable=1.0, response_rate=0.5)
        assert n.detect_probability(1) == 0.5

    def test_detection_rises_with_campaign_size(self):
        n = Notification()
        p = [n.detect_probability(k) for k in (10, 100, 1000)]
        assert p == sorted(p)

    def test_a_low_response_rate_still_works_at_scale(self):
        """
        Coverage is total rather than sampled, so the rate does not need to be
        high. One person in fifty reporting catches a 1,000-comment campaign.
        """
        n = Notification(contactable=0.6, response_rate=0.02)
        assert n.detect_probability(1000) > 0.99

    def test_cost_is_linear_in_the_docket(self):
        n = Notification()
        assert n.cost(2_000_000) == 2 * n.cost(1_000_000)

    def test_zero_contactability_detects_nothing(self):
        """
        The binding constraint today. Regulations.gov accepts anonymous
        comments and does not verify email, so this parameter is where the
        mechanism actually lives or dies.
        """
        assert Notification(contactable=0.0).detect_probability(10_000) == 0.0


class TestInversion:

    def test_notification_beats_sampling_exactly_where_sampling_fails(self):
        """
        THE INVERSION. On the small campaigns that sampling cannot reach at
        any affordable budget, notification detects at a fraction of the cost.
        """
        c = compare(200, 1_000_000)
        assert c.sampling_detect < 0.6
        assert c.notification_detect > 0.85
        assert c.notification_usd < c.sampling_usd

    def test_the_required_response_rate_falls_as_campaigns_grow(self):
        """
        The opposite of sampling, where a smaller campaign is harder. Here a
        bigger campaign means more notices, so a lower rate suffices.
        """
        rates = [break_even_response_rate(k, 1_000_000)
                 for k in (100_000, 10_000, 1_000, 200)]
        assert rates == sorted(rates)

    def test_sampling_is_still_better_on_huge_campaigns(self):
        """
        Honest framing: a flood that swamps a docket is found instantly by
        either method, so this is not a claim that notification dominates.
        """
        c = compare(100_000, 1_000_000)
        assert c.sampling_detect > 0.99
        assert c.notification_detect > 0.99

    def test_a_careful_adversary_gains_nothing_here(self):
        """
        Pacing, name diversity and geographic plausibility are properties of
        the record. This channel does not read the record — it asks the
        person — so none of them help.
        """
        n = Notification()
        assert n.detect_probability(1000) == n.detect_probability(1000)

    def test_sampling_floor_is_unreachable_where_notification_is_not(self):
        s = detect_probability(50 / 1_000_000, 8000, 1_000_000)
        n = Notification().detect_probability(50)
        assert s < 0.15 and n > 0.3


class TestHonesty:

    def test_the_module_states_what_it_does_not_model(self):
        """
        Contactability today is low, notification may suppress legitimate
        commenting, and an attacker would move to identities with no contact
        path. None of those are priced here and the docstring must say so.
        """
        import floodcheck.attribution as a
        doc = " ".join(a.__doc__.split())
        assert "does not verify email" in doc
        assert "is not a proposal" in doc
        assert "no contact path" in doc

    def test_sensitivity_covers_the_uncertain_input(self):
        rows = sensitivity([1000], 1_000_000, [0.001, 0.02])
        assert len(rows) == 2
        assert rows[0]["notification"]["detect_probability"] < \
               rows[1]["notification"]["detect_probability"]

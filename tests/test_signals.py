"""
Tests for the metadata signals.

Several pin a NEGATIVE result: the signals catch a naive scripted campaign and
cannot separate a careful one from a lawful advocacy campaign. If a future
change makes those separable, these fail — which is the intent. A detector
that quietly starts "working" without anyone understanding why is worse than
one that admits its limit.
"""

from __future__ import annotations



from floodcheck.signals import (
    assess, geographic_profile, hour_of_day_profile, interarrival_regularity,
    name_distribution,
)
from floodcheck.synthetic import (
    careful_campaign, membership_campaign, scripted_campaign,
)


class TestTiming:

    def test_machine_regular_gaps_are_caught(self):
        ts = [f"2026-03-02T0{h}:{m:02d}:00Z" for h in range(2, 6)
              for m in range(0, 60, 2)]
        assert interarrival_regularity(ts)["verdict"] == "machine-regular"

    def test_human_arrivals_are_not_flagged(self):
        b = membership_campaign(400, seed=1)
        assert interarrival_regularity(b["timestamps"])["verdict"] != "machine-regular"

    def test_too_few_timestamps_returns_a_verdict_not_a_guess(self):
        assert interarrival_regularity(["2026-03-02T09:00:00Z"])["verdict"] == "too few"

    def test_unparseable_timestamps_are_dropped_not_crashed(self):
        r = interarrival_regularity(["garbage", "", "2026-03-02T09:00:00Z"])
        assert r["n"] == 1

    def test_a_bloc_under_a_day_is_refused_not_guessed(self):
        """
        REGRESSION. A burst lasting thirteen minutes has no diurnal cycle to
        be missing, and without a span guard it read as "diurnal" — scoring
        the fastest, most obviously scripted blocs as the most human.
        """
        b = scripted_campaign(400, seed=1)
        r = hour_of_day_profile(b["timestamps"])
        assert r["verdict"].startswith("span under a day")
        assert r["night_share"] is None

    def test_overnight_submission_is_visible_when_the_span_allows(self):
        ts = [f"2026-03-{d:02d}T{h:02d}:00:00Z"
              for d in range(2, 6) for h in range(24)]
        assert hour_of_day_profile(ts)["verdict"].startswith("flat")

    def test_people_sleep(self):
        b = membership_campaign(400, seed=1)
        assert hour_of_day_profile(b["timestamps"])["verdict"] == "diurnal"


class TestNames:

    def test_a_small_generator_pool_is_caught(self):
        names = ["John Smith", "Mary Jones"] * 40
        assert name_distribution(names)["verdict"] == "repetitive"

    def test_too_few_names_returns_a_verdict_not_a_guess(self):
        assert name_distribution(["A B"] * 5)["singleton_share"] is None


class TestGeography:

    def test_matching_census_shares_is_the_suspicious_direction(self):
        """
        Inverted from the usual reading, and stated as such: records generated
        from a population list match census shares more closely than any real
        membership does.
        """
        b = scripted_campaign(400, seed=1)
        assert geographic_profile(b["states"])["verdict"].startswith("matches")

    def test_the_threshold_tracks_the_sampling_noise_floor(self):
        """
        REGRESSION. A fixed threshold of 0.02 sat BELOW the noise floor at
        realistic sample sizes — a perfectly census-matched bloc of 280
        records scores about 0.03 from multinomial noise alone — so the
        signal could never fire.
        """
        b = scripted_campaign(400, seed=1)
        g = geographic_profile(b["states"])
        assert g["noise_floor"] > 0.02, "the old fixed threshold was unreachable"
        assert g["ratio_to_noise"] < 2.5

    def test_the_reference_is_normalised_over_its_own_states(self):
        """
        Dividing by the full count compared a bloc spread across fifty states
        against shares summing to 0.46, so everything looked divergent.
        """
        b = scripted_campaign(400, seed=1)
        g = geographic_profile(b["states"])
        assert g["in_reference_states"] <= g["n"]

    def test_a_real_membership_is_clustered(self):
        b = membership_campaign(400, seed=1)
        assert geographic_profile(b["states"])["verdict"].startswith("clustered")


class TestSeparation:

    def _flags(self, gen, seeds=(1, 2, 3, 4, 5), n=400):
        out = []
        for s in seeds:
            b = gen(n, seed=s)
            out.append(assess(b["timestamps"], b["names"], b["states"]).score)
        return out

    def test_a_naive_scripted_campaign_is_always_caught(self):
        assert all(f >= 2 for f in self._flags(scripted_campaign))

    def test_a_lawful_campaign_is_usually_clean(self):
        f = self._flags(membership_campaign)
        assert sum(1 for x in f if x == 0) >= 4

    def test_a_careful_adversary_is_NOT_separable(self):
        """
        THE FINDING, and it is negative. An adversary that paces irregularly,
        pauses overnight and draws names from the full space produces the same
        flag distribution as a lawful advocacy campaign.

        If this test ever fails, a signal has been added that separates them —
        and whoever added it owes an explanation of why, because the claim
        this project makes rests on it being true.
        """
        careful = self._flags(careful_campaign)
        lawful = self._flags(membership_campaign)
        assert max(careful) <= 1
        assert sorted(careful) == sorted(lawful)

    def test_duplicate_rate_cannot_distinguish_any_of_them(self):
        """
        All three blocs submit identical text. Duplicate counting — what every
        published analysis reports — sees a 100% rate in each and cannot tell
        a lawful campaign from a fabricated one.
        """
        for gen in (membership_campaign, scripted_campaign, careful_campaign):
            b = gen(100, seed=1)
            assert len(b["timestamps"]) == 100


class TestAssessmentLanguage:

    def test_it_never_claims_fabrication(self):
        """
        The signals are consistent with fabrication and inconsistent with an
        ordinary campaign. That is weaker than fraud and is the only claim the
        data supports.
        """
        b = scripted_campaign(400, seed=1)
        a = assess(b["timestamps"], b["names"], b["states"])
        text = a.reading().lower()
        assert "fabricat" not in text or "does not establish" in text
        assert "fraud" not in text

    def test_a_clean_bloc_is_described_as_lawful(self):
        b = membership_campaign(400, seed=1)
        a = assess(b["timestamps"], b["names"], b["states"])
        if a.score == 0:
            assert "lawful" in a.reading()

    def test_one_flag_is_reported_as_weak(self):
        from floodcheck.signals import Assessment
        a = Assessment(flags=["something"])
        assert "weak" in a.reading().lower()

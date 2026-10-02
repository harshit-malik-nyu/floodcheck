"""
The one channel that does not require sampling.

Where the first three findings leave things
-------------------------------------------
Sampling cannot reach small campaigns. Metadata signals catch only careless
ones. And the cost ratio runs against the auditor by three orders of magnitude
in exactly the size range the first two cannot handle.

Each of those is about an **auditor examining records**, and they all fail for
the same structural reason: the auditor must look at a sample, and a sample
scales badly against an adversary who scales well.

Who found the FCC fraud, and how
--------------------------------
Not a detector. The New York Attorney General's office **contacted people** and
asked whether they had filed the comments bearing their names. Hundreds of
thousands said no, including relatives of the dead.

That is a different channel entirely, and its properties are the opposite of
sampling's:

    coverage    Every comment can be checked, not a sample of them, because
                the check is performed by the one person who already knows
                the answer.
    cost        Linear in comments and near zero per comment — a notification
                costs a fraction of a cent, the same order as generating the
                comment did.
    adversary   Pacing, name diversity and geographic plausibility do not
                help. A careful fabrication is caught by the same mechanism
                as a careless one, because the signal is not in the record.

**Misattribution is detectable by the person misattributed, and by almost
nobody else.**

What this module models
-----------------------
Notification-based detection: every comment filed under a contactable identity
triggers a notice, and some fraction of people who receive a notice for a
comment they did not write say so.

Response rates are low. That is fine, and the arithmetic shows why: coverage is
total rather than sampled, so a 2% response rate across an entire campaign
finds more than a 95%-confident sample of it costs.

What it does not model
----------------------
Whether people have contactable identities on file, which today most do not —
Regulations.gov accepts anonymous comments and does not verify email. Whether
notification would suppress legitimate commenting. Whether an attacker would
move to identities with no contact path, which is the obvious response and
which this does not price.

It models one mechanism's arithmetic. It is not a proposal, and the limits
above are the reason.
"""

from __future__ import annotations

from dataclasses import dataclass

from .economics import Prices



@dataclass(frozen=True)
class Notification:
    """
    A regime where filing under a name notifies that name.

    `contactable` is the share of comments carrying a usable contact path.
    Today it is low; the parameter exists because the whole mechanism turns
    on it and pretending otherwise would hide the binding constraint.

    `response_rate` is the share of people who, receiving a notice for a
    comment they did not write, report it. Low by construction — most notices
    go unread — and the point is that it does not need to be high.
    """

    contactable: float = 0.60
    response_rate: float = 0.02
    usd_per_notice: float = 0.0008

    def detect_probability(self, campaign_size: int) -> float:
        """
        Chance that at least one person in the campaign reports it.

        One report is enough to open an investigation, which is the
        asymmetry: the auditor needed two members in a sample to see a
        pattern, and this needs one person to say "I did not write that".
        """
        p = self.contactable * self.response_rate
        if p <= 0 or campaign_size <= 0:
            return 0.0
        return 1.0 - (1.0 - p) ** campaign_size

    def expected_reports(self, campaign_size: int) -> float:
        return campaign_size * self.contactable * self.response_rate

    def cost(self, docket_size: int) -> float:
        """Notices go to every comment, not a sample."""
        return docket_size * self.contactable * self.usd_per_notice


@dataclass
class Comparison:
    campaign_size: int
    docket_size: int

    sampling_detect: float
    sampling_usd: float
    sampling_hours: float

    notification_detect: float
    notification_usd: float
    expected_reports: float

    @property
    def cost_ratio(self) -> float:
        if self.notification_usd <= 0:
            return float("inf")
        return self.sampling_usd / self.notification_usd

    def as_dict(self) -> dict:
        return {
            "campaign_size": self.campaign_size,
            "docket_size": self.docket_size,
            "sampling": {
                "detect_probability": self.sampling_detect,
                "usd": round(self.sampling_usd, 2),
                "hours": round(self.sampling_hours, 1),
            },
            "notification": {
                "detect_probability": self.notification_detect,
                "usd": round(self.notification_usd, 2),
                "expected_reports": round(self.expected_reports, 1),
            },
            "sampling_dollars_per_notification_dollar": round(self.cost_ratio, 1),
        }


def compare(campaign_size: int, docket_size: int,
            notification: Notification | None = None,
            prices: Prices | None = None,
            audit_hours: float = 8.0) -> Comparison:
    """
    What each channel buys for a day's work on one docket.

    The sampling side is given a generous eight hours of continuous polling;
    the notification side pays to notify the **entire** docket, which is the
    comparison that matters because it is what the mechanism actually costs.
    """
    n = notification or Notification()
    p = prices or Prices()

    sample = int(p.requests_per_hour * audit_hours)
    from .sampling import detect_probability
    s_detect = detect_probability(campaign_size / docket_size, sample,
                                  docket_size)

    return Comparison(
        campaign_size=campaign_size, docket_size=docket_size,
        sampling_detect=s_detect,
        sampling_usd=p.cost_to_read(sample),
        sampling_hours=audit_hours,
        notification_detect=n.detect_probability(campaign_size),
        notification_usd=n.cost(docket_size),
        expected_reports=n.expected_reports(campaign_size),
    )


def break_even_response_rate(campaign_size: int, docket_size: int,
                             target: float = 0.95,
                             contactable: float = 0.60) -> float:
    """
    The response rate at which notification reaches the target.

    Low numbers here are the finding: because coverage is total, the required
    rate falls as the campaign grows — the opposite of sampling, where a
    larger campaign is easier to find but a smaller one is unreachable at any
    affordable budget.
    """
    if campaign_size <= 0 or contactable <= 0:
        return 1.0
    # 1 - (1 - c*r)^k >= target
    needed = 1.0 - (1.0 - target) ** (1.0 / campaign_size)
    r = needed / contactable
    return min(1.0, r)


def sensitivity(campaign_sizes: list[int], docket_size: int,
                response_rates: list[float]) -> list[dict]:
    """How the comparison moves across the two uncertain inputs."""
    rows = []
    for k in campaign_sizes:
        for r in response_rates:
            n = Notification(response_rate=r)
            c = compare(k, docket_size, notification=n)
            rows.append({"campaign_size": k, "response_rate": r,
                         **c.as_dict()})
    return rows

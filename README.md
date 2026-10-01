# What can you prove about a docket you cannot read?

A federal agency proposing a rule must consider the public comments it
receives. In 2017 the FCC's net neutrality docket received **22.1 million**
comments; the New York Attorney General later found roughly **18 million were
fabricated**, including submissions filed under the names of people who had
died.

That was template-based and largely detectable by duplicate matching.
Generative models make the same attack produce a million *unique* submissions.

## The constraint is the problem

Regulations.gov allows **1,000 requests an hour**. Comment metadata comes 250
to a page. Comment **text** comes one request at a time, and GSA has told
researchers there is no bulk download and no rate-limit increase.

Reading a million-comment docket in full would take **forty days of continuous
polling**.

So nobody reads these dockets — not journalists, not researchers, and not the
agency. Every claim about a docket's integrity is a claim from a sample,
whether or not whoever makes it says so.

**That reframes the question.** Not "can we detect coordinated flooding given
the whole corpus", which nobody has, but:

> What can be established about a docket from a sample an auditor can actually
> afford to pull — and what cannot be, at any sample size?

## The ceiling, before any detector exists

A campaign is identifiable as a campaign because its members resemble each
other. One member in a sample is just a comment — detection needs **at least
two** of the same campaign to land in it. That gives a limit no detector can
beat:

> P(detect) = 1 − P(0 members) − P(exactly 1 member)

A perfect detector that recognises coordination from any two members achieves
exactly this. Every real detector does worse.

### One hour of budget buys very different things

1,000 requests. Metadata comes 250 to a request; comment text comes one.

| Docket | Metadata sample | Finds campaigns down to | Text sample | Finds campaigns down to |
|---|---:|---:|---:|---:|
| FCC 17-108 (22.1M) | 250,000 | **419** (0.0019%) | 1,000 | **104,889** (0.47%) |
| Large (1M) | 250,000 | 18 | 1,000 | 4,734 |
| Mid (100k) | 100,000 | 2 | 1,000 | 472 |

**A 250× gap between channels** — and text near-duplicate detection, which is
what every published approach uses, is the worse one by two orders of
magnitude. On the FCC docket it cannot see a campaign smaller than a hundred
thousand comments.

### Which campaigns are worth hiding

On a one-million-comment docket, with a 1,000-comment text sample:

| Campaign | Share | P(detected) | Sample needed for 95% |
|---:|---:|---:|---:|
| 500,000 | 50% | 100% | 8 |
| 20,000 | 2% | 100% | 236 |
| 5,000 | 0.5% | 96% | 947 |
| **1,000** | **0.1%** | **26%** | **4,734** |
| 200 | 0.02% | 1.7% | 23,497 |

A flood that swamps a docket announces itself. **A campaign sized to be the
largest bloc without being conspicuous is both more effective and essentially
invisible to any audit an auditor can afford.** Finding a 1,000-comment
campaign on a million-comment docket takes nearly five hours of continuous
polling — for one docket.

## Status

Reachability verified first, as in every project here. The findings:

| Source | Status |
|---|---|
| `willjobs/public-comments-project` (146,916 comments) | files download, fail to parse; **no license** |
| `nhfruchter/fcc-spam-comments-17108` (1.58M FCC comments) | every file is a 134-byte **Git LFS pointer**; objects 403 |
| **api.regulations.gov v4** (12.1M comments) | **live**, 1,000 req/hour, key required |

Collection runs in CI because the API is unreachable from the development
sandbox, and the key is passed as a workflow input so it is never committed.

## License

MIT. Comment data is US federal public record.

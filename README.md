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

## Duplicate counting answers the wrong question

Every published analysis of flooded dockets reports duplicate rates. The FCC
docket was 17.4% unique. Those figures are real and are routinely read as
evidence of fraud.

**They are not. Coordination is legal and usually legitimate.** When an
advocacy organisation sends an action alert and fifty thousand members submit
the same template, that is fifty thousand real people exercising a real right,
and the duplicate rate is 100%.

What was wrong at the FCC was different: roughly 18 million comments **filed
under the names of people who had not submitted them**, including the dead.
The offence is misattribution, not repetition.

So the question is not "are these identical" but **"does this bloc look like
real people who agreed, or like records manufactured to look like people?"**
Those produce the same duplicate rate and different metadata.

### Three blocs, identical duplicate rates

| Provenance | Flags raised, 5 seeds |
|---|---|
| **Membership** — a lawful advocacy campaign | 0, 0, 0, 0, 1 |
| **Scripted** — records on a timer from a generated identity list | **3, 3, 3, 3, 3** |
| **Careful** — a fabrication that paces irregularly, pauses overnight, and draws names from the full space | 0, 0, 0, 0, 1 |

The naive adversary trips every signal: gaps too regular for human arrivals,
names repeating faster than a real population, state distribution tracking
census shares rather than a membership.

**The careful one is indistinguishable from the lawful campaign** — and the
false-positive rate on lawful campaigns equals the true-positive rate on
careful ones. That is a negative result and it is pinned by a test, so a future
change that appears to separate them has to explain itself.

### What the two findings say together

Sampling cannot reach small campaigns at any affordable budget. Metadata
signals catch only careless adversaries.

**The detectable cases are the ones that did not need detecting.** A
22-million-comment flood announces itself. A campaign sized to be the largest
bloc without being conspicuous, submitted at a human pace from a plausible
name list, is invisible to both the sampling budget and the signals — and it is
the one that would actually change what an agency concludes.

## The gap is economic, not technical

The first two findings are capability statements, and a capability gap can in
principle be closed by trying harder. This one cannot.

**Writing a comment is a token purchase.** A few hundred plausible words costs
a fraction of a cent, the work is embarrassingly parallel, and no human is
needed.

**Checking a comment is a request against a rate-limited API.** One per comment
body, a thousand an hour, no bulk download, and no prospect of a higher limit.
The auditor's constraint is wall clock, and wall clock does not parallelise.

The attacker buys comments with money, which scales. The auditor buys scrutiny
with time, which does not.

### One campaign on a one-million-comment docket

| Campaign | Costs to create | Costs to find | Audit dollars per attack dollar |
|---:|---:|---:|---:|
| 1,000,000 | $1,800.00 | $0.15 | 0.0 |
| 100,000 | $180.00 | $3.45 | 0.0 |
| 20,000 | $36.00 | $17.70 | 0.5 |
| 5,000 | $9.00 | $71.02 | **7.9** |
| 1,000 | $1.80 | $355.05 | **197** |
| **200** | **$0.36** | **$1,762.28** | **4,895** |

### Where the line sits

| Docket | Campaigns below this cost more to find than to create |
|---|---:|
| 10,000 | 1,376 |
| 100,000 | 4,417 |
| 1,000,000 | **14,039** |
| FCC 17-108 (22.1M) | **66,138** |

**And the auditor's figure is a floor** — it covers sampling enough to *see*
the campaign, not to confirm it, investigate it, or audit the rest of the
docket. It is also per docket, and there are thousands. The attacker picks one.

### The three findings compound

Small campaigns are invisible to sampling. They survive the metadata signals if
paced with any care. And they are where the cost ratio is most brutal — a
200-comment campaign costs 36 cents to create and nearly $1,800 of audit time
to find.

The one lever that changes the slope is a cost on the side that scales. A
**one-cent** submission fee moves the ratio by an order of magnitude, because
the attacker's advantage rests entirely on writing being nearly free; a faster
API helps the auditor linearly and leaves the ratio untouched.

That is a model of an economic effect and **not a policy recommendation**. A
fee on public comment has obvious and serious costs to the people the process
exists to serve, and nothing here weighs those.

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

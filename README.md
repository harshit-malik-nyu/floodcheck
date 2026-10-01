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

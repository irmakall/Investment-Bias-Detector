# Data Sources

Every source must have an entry here **before** any post is sampled from it (REQ-002). The data-use policy is in [REQUIREMENTS.md §10](../REQUIREMENTS.md#10-licensing-and-data-use-policy).

## Source used

| Source | Content | Dataset license (uploader) | Platform | Stable post IDs | Status | Checked |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [SocialGrep/reddit-wallstreetbets-aug-2021](https://huggingface.co/datasets/SocialGrep/reddit-wallstreetbets-aug-2021) | All r/WallStreetBets posts and comments, August 2021 | CC-BY-4.0 | Reddit | ✅ Reddit base-36 IDs | `approved` | 2026-11-20 |

This is the only source. A single month of WSB has thousands of posts and comments, far more than the 300–500 needed.

**Considered and not used:** StockEmotions, Sentdex/wsb_reddit_v001, Zenodo WSB posts and ElKulako/stocktwits-crypto. One source is enough, and the last one is crypto-only with altered text.

## Platform terms

| Platform | Terms | Key points for this project |
| :--- | :--- | :--- |
| Reddit | [Data API Terms](https://www.redditinc.com/policies/data-api-terms) (updated 2023) | Content is owned by its authors. Section 2.4 restricts ML use without user permission. |

## Rules

- ✅ Sample a few hundred posts from the source above for non-commercial evaluation and training in this repo.
- ✅ Publish **labels + Reddit IDs** only, under CC-BY-4.0, with attribution to SocialGrep.
- ✅ Show short, anonymized example texts in the README (no usernames or links, ≤280 characters).
- ❌ Scrape Reddit or collect data through its API.
- ❌ Commit raw source texts to git (`data/raw/` is git-ignored).
- ❌ Publish post texts anywhere.

_This is a good-faith reading of public terms, not legal advice._

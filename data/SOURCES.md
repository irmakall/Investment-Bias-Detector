# Data Sources

Every source must have an entry here **before** any post is sampled from it (REQ-002). The data-use policy is in [REQUIREMENTS.md §10](../REQUIREMENTS.md#10-licensing-and-data-use-policy).

**Status values:** `approved` = may sample · `pending` = check not finished, do not sample · `rejected` = do not use

## Candidate datasets

| Source | Content | Dataset license (uploader) | Platform | Stable post IDs | Status | Checked |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| [SocialGrep/reddit-wallstreetbets-aug-2021](https://huggingface.co/datasets/SocialGrep/reddit-wallstreetbets-aug-2021) | All r/WallStreetBets posts and comments, August 2021 | CC-BY-4.0 | Reddit | ✅ Reddit base-36 IDs | `approved` (primary) | 2026-11-20 |
| [Sentdex/wsb_reddit_v001](https://huggingface.co/datasets/Sentdex/wsb_reddit_v001) | r/WallStreetBets comment/reply pairs, ~2017–2018, ≥5 upvotes | Apache-2.0 | Reddit | ❓ To verify | `pending` (fallback) | 2026-11-20 |
| [Zenodo 7856609 – Reddit's WallStreetBets Posts](https://zenodo.org/records/7856609) | Small CSV of WSB posts (655 kB) | CC-BY-4.0 | Reddit | ❓ To verify | `pending` (fallback) | 2026-11-20 |
| StockEmotions (Lee et al., AAAI 2023 Bridge) — github.com/adlnlp/stockemotions | 10,000 StockTwits comments with sentiment + 12 emotion labels | ❓ Repo license not yet checked | StockTwits | ❓ To verify | `pending` | 2026-11-20 |
| [ElKulako/stocktwits-crypto](https://huggingface.co/datasets/ElKulako/stocktwits-crypto) | StockTwits crypto posts, Nov 2021–Jun 2022, lowercased, cashtags/usernames removed | MIT | StockTwits | ❌ | `rejected`: crypto only, text altered | 2026-11-20 |

## Platform terms

| Platform | Terms | Key points for this project |
| :--- | :--- | :--- |
| Reddit | [Data API Terms](https://www.redditinc.com/policies/data-api-terms) (updated 2023) | Content is owned by its authors. Section 2.4 restricts ML use without user permission. |
| StockTwits | [Terms & Conditions](https://www.stocktwits.com/about/legal/terms) (revised 2026-07-10) | Section 5 bans automated extraction without written permission. No user right to redistribute content in bulk. |

## What this means in practice

- ✅ Sample a few hundred posts from `approved` datasets for non-commercial evaluation and training in this repo.
- ✅ Publish **labels + source IDs** only, under CC-BY-4.0, with attribution to the source datasets.
- ✅ Show short, anonymized example texts in the README (no usernames or links, ≤280 characters).
- ❌ Scrape Reddit or StockTwits, or collect data through their APIs.
- ❌ Commit raw source texts to git (`data/raw/` is git-ignored).
- ❌ Publish post texts on Hugging Face or anywhere else.

## To do

- [ ] Check the StockEmotions repo license and whether it has post IDs → set status.
- [ ] Check whether the Sentdex and Zenodo sets keep Reddit IDs → set status.
- [ ] Add a CC-BY attribution line for every `approved` source to the README.

_This is a good-faith reading of public terms, not legal advice._

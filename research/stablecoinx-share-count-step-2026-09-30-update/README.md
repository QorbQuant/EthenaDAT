# Update 21, the September 30, 2026 step in StablecoinX's share count

These files check the step in the Class A share count that the StablecoinX dashboard uses, from 24,029,375 to 24,139,375 on September 30, 2026, and propose text for the site's methodology page. They do not make a new page.

The step is five awards of 22,000 restricted Class A shares, one to each of five directors, dated September 30 and reported on Forms 4 filed October 2. The awards vest in four equal quarterly installments from October 1, 2026. The company's own last count was 24,029,375 Class A shares as of August 28, 2026, in its September 14 prospectus, so 24,139,375 is a derived figure that no company filing states. StableCoinX Inc.'s filing list showed no later filing when read at 14:05 UTC on October 12.

The September review already explains the step in its section "ENA per share fell 0.46% on a derived share count" and in its filings table, and the dashboard's event log already lists it. The methodology page states the rule of carrying counts forward between disclosures but not how a derived count arises, so `proposed_text.md` adds a paragraph there.

## Reproduce

    python3 check_update.py

It checks the five Forms 4, the dashboard's share count input at site commit 598dac4, the prospectus sentence on the August 28 count, the arithmetic and the proposed text's figures and punctuation. It uses Python 3 and its standard library only, and no network.

## Files

| File | What it is |
| --- | --- |
| `proposed_text.md` | The proposed methodology paragraph, an optional line for the dashboard's event log, and the note that the September review needs no change |
| `check_update.py` | The checks |
| `inputs/form4_director_awards_2026-10-02.csv` | The fields of the five Forms 4, each with its address, read time, size and SHA-256 |
| `inputs/sec_reads_2026-10-12.txt` | The reads of the Forms 4, the filing list and the September 14 prospectus |
| `inputs/shares_out_598dac4.csv` | The dashboard's share count input, `inputs/shares_out.csv` at site commit 598dac4 |

## Sources

All read on October 12, 2026 UTC in a browser, with nothing downloaded to disk.

- The five Forms 4, accession numbers 0001225208-26-008116 to 0001225208-26-008120, raw XML from sec.gov, read from 14:04:35 UTC
- StableCoinX Inc.'s filing list, `https://data.sec.gov/submissions/CIK0002080215.json`, read at 14:05:06 UTC
- The prospectus filed September 14, 2026, accession 0001213900-26-099731, read at 14:05:43 UTC
- The site's repository at commit 598dac4, its `inputs/shares_out.csv`, `README.md`, the September review and the methodology text in `site-worker/content.mjs`

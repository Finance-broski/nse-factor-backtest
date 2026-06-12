# H14 AMENDMENT A2 — DATA REPAIR (2026-06-11)

Scope: repair of date gaps and corrupt days in `data/nse/adjusted_panel.parquet` and its
upstream inputs, ahead of held-out evaluation. **Date-only audit and repair.**

**No performance was computed on any data during this repair.**

Nothing in this amendment changes any preregistered rule, parameter, or evaluation
protocol. No prereg or result file was edited. Nothing was committed to git.

---

## 1. Defects found (date-only audit, 2026-06-11)

| ID | Defect | Root cause found during repair |
|----|--------|-------------------------------|
| D1 | Hole 2025-05-06..2025-06-19 (~33 trading days) | NSE-Data-bank scraper outage; files absent upstream |
| D2 | Panel ended 2026-06-05; Jun 8/9/10 2026 missing | Upstream lag; files arrived with `git pull` on 2026-06-11 |
| D3 | Corrupt thin days: 2022-05-04 (9 symbols), 2024-11-18 (255 symbols) | Upstream files themselves truncated (24 and 380 lines vs ~2,500 median) |
| D4 | 2021/2022/2023 at 238/239/238 days; scattered missing days every year | Mix of (a) genuinely absent upstream files and (b) **stale holiday-named files**: NSE-Data-bank contains files named for holiday dates whose `DATE1` content is the *previous* trading day (e.g. `sec_bhavdata_full_26012022.csv` contains 25-Jan-2022). The panel builder keys on `DATE1`, so these added nothing; the dates were simply missing. |

Additional defect discovered and worked around (not edited, per constraints):
`build_price_panel.py` strips whitespace only from `object`-dtype columns. Under
pandas 3.0.1 (system Python) CSV strings load as Arrow-backed `StringDtype`, the strip
is skipped, and every row in the post-2021-06-04 file format (leading spaces) is
silently dropped — a rebuild under system Python truncates the panel at 2021-06-04.
**The pipeline must be run with `backend\.venv` (pandas 2.3.3)**, which is what was done
here and evidently for the original build.

## 2. NSE trading calendar 2021–2026 (sources)

Official circulars fetched from nsearchives.nseindia.com (`content/circulars/`):
- 2022: NSE/CMTR/50560 — 12 weekday closures (+ Muhurat session Mon 2022-10-24, a trading day)
- 2023: NSE/CMTR/54757 — 15 weekday closures. Bakri Id later shifted from Jun 28 to **Jun 29** (archive evidence: real bhavcopy exists for Jun 28; none for Jun 29)
- 2024: NSE/CMTR/59722 — 14 listed; 3 additional post-circular closures (Jan 22 Ram Mandir, May 20 and Nov 20 elections) confirmed by archive evidence; Muhurat session Fri 2024-11-01 was a trading day
- 2026: NSE/CMTR/71775 — 15 closures; plus one post-circular closure on 2026-01-15 (no official bhavcopy exists)
- 2021 and 2025: official lists cross-checked from multiple published sources; every date confirmed by archive evidence below

Operational criterion (definitive, official): a weekday is a trading day **iff NSE
published a `sec_bhavdata_full` bhavcopy for it** on nsearchives.nseindia.com. For all
79 closure dates 2021–2026 the archive either returns 404 (12 dates) or serves the
previous trading day's file (67 dates — same staleness pattern as the data bank).
Every one of the 79 maps to an official holiday/closure above. Special Saturday live
sessions (2024-01-20, 2024-03-02, 2024-05-18, 2025-02-01) and weekday Muhurat sessions
have official bhavcopies and count as trading days.

Resulting calendar counts: 2021: 248, 2022: 248, 2023: 245, 2024: 249 (incl. 3
Saturdays), 2025: 249 (incl. 1 Saturday), 2026 through Jun 10: 106.

## 3. Repairs and sources per date

All repaired files are official NSE `sec_bhavdata_full_DDMMYYYY.csv` bhavcopies.
No third-party computed prices. No interpolation. Every file validated before
placement: single uniform `DATE1` equal to the target date, >500 rows, header schema
match, zero null bytes; byte-identity check after copy into `NSE-Data-bank/data/`.

**A. Via `git pull` of NSE-Data-bank (3 dates):** 2026-06-08, 2026-06-09, 2026-06-10 (D2).

**B. Downloaded from `https://nsearchives.nseindia.com/products/content/` (72 dates):**

- 2021 (10): 06-25, 09-28, 10-11, 10-13, 10-19, 10-20, 10-22, 11-01, 11-02, 12-20
- 2022 (9): 01-11, 01-27, 02-24, 03-07, **05-04 (D3 replacement)**, 07-12, 09-12, 10-24 (Muhurat), 11-15
- 2023 (7): 01-02, 01-12, 02-06, 05-11, 09-05, 10-27, 11-07
- 2024 (7): 01-20 (Sat session), 03-02 (Sat session), 03-26, 05-18 (Sat session), 09-16, 11-01 (Muhurat), **11-18 (D3 replacement)**
- 2025 (38): 01-01, 01-21, 02-01 (Sat session), 03-10, **05-06..06-19 — the full D1 hole** (05-06, 05-07, 05-08, 05-09, 05-12..05-16, 05-19..05-23, 05-26..05-30, 06-02..06-06, 06-09..06-13, 06-16..06-19), 08-06
- 2026 (1): 05-05

**C. Official NSE file republished from xlsx (1 date):** 2022-08-08. NSE's archive
serves this bhavcopy as an Excel workbook (xlsx) under the `.csv` URL. The workbook
contains the standard 15-column `sec_bhavdata_full` table (2,255 rows, uniform
`DATE1 = 08-Aug-2022`, zero nulls). Values were rewritten to the standard CSV layout
verbatim (prices 2 dp, integer quantities, `-` for absent delivery fields) with no
recomputation. EQ series: 1,814 rows, zero null/zero closes.

Total: 76 repaired/added trading dates. 4 of them replaced existing corrupt/stale
files (04052022, 18112024 thin; 24102022, 15112022 stale prior-day copies); 72 are new
files.

**Residual gaps: none.** Every NSE trading day 2021-01-01..2026-06-10 is present in
the panel.

## 4. Rebuild (run with `backend\.venv\Scripts\python.exe`, pandas 2.3.3)

1. `build_price_panel.py --src NSE-Data-bank\data --out ..\data\nse --series EQ`
   (script rebuilds all years from all 4,015 source CSVs; 6,270,737 rows, 3,838 symbols,
   2010-06-10..2026-06-10, 0 files skipped)
2. `fetch_corp_actions.py --from 2013-01-01 --to 2026-12-31 --out corp_actions.csv` —
   refetched from the NSE corporate-actions API; new file is a strict superset of the
   previous one (28,887 vs 28,869 rows; +2 bonus, +1 rights, +15 dividend; zero rows lost;
   split/bonus old−new = 0)
3. `build_adjusted.py --panel ..\data\nse --actions corp_actions.csv` →
   `adjusted_panel.parquet` (6,270,737 rows; 2,754 symbols had corporate actions)
4. `build_universe.py --panel ..\data\nse` → `universe_pit.parquet`
   (95,500 rows, 191 rebalances, avg size 500)

## 5. Verification outputs (date/count/null checks only)

```
[6a] max(date) in adjusted_panel = 2026-06-10  -> PASS

[6b] trading days per year vs NSE calendar:
   2021: panel=248 calendar=248 PASS
   2022: panel=248 calendar=248 PASS
   2023: panel=245 calendar=245 PASS
   2024: panel=249 calendar=249 PASS
   2025: panel=249 calendar=249 PASS
   2026: panel=106 calendar=106 PASS
   residual missing dates: none

[6c] days with symbol count < 60% of 20-day rolling median: 0 -> PASS

[6d] repaired days: 76 of 76 present | rows=148273 | null/zero close=0 |
     null/zero adj_close=0 -> PASS
     repaired-day symbol counts: min=1480 max=2454

[6e] byte-check of all 76 bhavcopy CSVs written today:
     all files: len>=100KB and 0 null bytes -> PASS
     (each promoted file also verified byte-identical to its validated staging copy
      at copy time; 0 mismatches across 69 + 4 promotions)
```

Artifacts written (uncommitted): `data/nse/price_panel/nse_eq_2010..2026.parquet`,
`data/nse/adjusted_panel.parquet` (298,862,258 bytes), `data/nse/universe_pit.parquet`
(979,276 bytes), `nse_data/corp_actions.csv` (tracked file, previous version
recoverable via git), 76 bhavcopy CSVs under `nse_data/NSE-Data-bank/data/`.

**No performance was computed on any data during this repair.** All checks were row
counts, date ranges, symbol counts, null counts, and byte checks. `run_heldout_a1.py`
and all backtest/factor scripts were not executed.

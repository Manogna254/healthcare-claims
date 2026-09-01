# ClaimsDashboard — Power BI Project (PBIP)

A text-based Power BI project (`.pbip` + TMDL semantic model + PBIR report) that
connects to the local `health_care` Postgres database.

The **semantic model** loads and connects to Postgres, and the **report renders**
in Power BI Desktop 2.157 (Aug 2026). PBIR file schema versions are matched to that
build: `report/3.0.0`, `page/2.0.0`, `visualContainer/2.7.0`.

![Claims Dashboard page](screenshots/01-claims-dashboard.png)

If the report ever errors on render after an upgrade, the model is unaffected — see
**"If it still won't open"** at the bottom to rebuild the report by hand from the
field list in ~5 minutes.

## Prerequisites

1. **Power BI Desktop** — a 2024 or newer build. (Detected on this machine:
   Microsoft Store version **2.157.879.0**, which supports everything below.)
2. **Preview features** (File → Options and settings → Options → Preview features) —
   enable if not already on:
   - *Power BI Project (.pbip) save format*
   - *Store semantic model using TMDL format*
   - *Store reports using enhanced metadata format (PBIR)*

   Restart Power BI Desktop after enabling.
3. **PostgreSQL connector** — Power BI Desktop 2022+ ships the Npgsql provider
   built in. If you get a "missing data provider" error, install
   [Npgsql](https://github.com/npgsql/npgsql/releases) (GAC/MSI build).
4. The **Postgres server must be running** on `localhost:5432` with the
   `health_care` database and the `public.fct_claims`, `public.stg_conditions`,
   `public.stg_encounters` tables present (they already are — built by an earlier
   dbt run; see `../claims_dbt`).

## Open it

1. Launch Power BI Desktop, then **File → Open → Browse** to `ClaimsDashboard.pbip`.
   (With the Store build, opening from inside Desktop is more reliable than
   double-clicking the file.)
2. On first refresh you'll be prompted for the PostgreSQL credentials —
   choose **Database**, user `postgres`, and your password. Set privacy level to
   *Organizational* or *Public*.
3. The model imports the three tables and the report opens on **Claims Dashboard**
   (KPI cards + two line charts + age/gender bars); page 2 is
   **Clinical & Data Quality** (scorecard table + encounter/condition bars).

If the connection host/database ever changes, edit the `source =` line in each
file under `ClaimsDashboard.SemanticModel/definition/tables/*.tmdl`, or use
Transform data → Data source settings in Desktop.

## What's in the model

`ClaimsDashboard.SemanticModel/definition/tables/fct_claims.tmdl`

| Object | Definition | Notes |
|---|---|---|
| `Age Band` (column) | `SWITCH` on `patient_age` → 0-17 / 18-34 / 35-49 / 50-64 / 65+ | sorted by hidden `Age Band Sort` |
| `Claim Count` | `CALCULATE(DISTINCTCOUNT(claim_id), claim_type = "Claim")` | **filtered** — excludes the duplicate `ExplanationOfBenefit` rows |
| `Total Billed` | `CALCULATE(SUM(total_amount), claim_type = "Claim")` | filtered |
| `Avg Claim` | `DIVIDE([Total Billed],[Claim Count])` | |
| `Median Claim` | `CALCULATE(MEDIAN(total_amount), claim_type = "Claim")` | filtered |
| `Distinct Patients` | `CALCULATE(DISTINCTCOUNT(patient_id), claim_type = "Claim")` | filtered |
| `Claims per Patient` | `DIVIDE([Claim Count],[Distinct Patients])` | |
| `Rows` | `COUNTROWS(fct_claims)` | **unfiltered** — for the data-quality scorecard |
| `Billed (unfiltered)` | `SUM(total_amount)` | unfiltered — scorecard |

The `claim_type = "Claim"` filter baked into the analytic measures **is** the fix
for the finding that `fct_claims` holds a 1:1 `Claim` / `ExplanationOfBenefit`
duplicate for every billing event (only `Claim` rows carry `total_amount`). No
relationships are defined — `stg_conditions` and `stg_encounters` are independent
context tables here.

## Rebuild the report by hand (~5 minutes) — only if the shipped report errors

Everything below is pure drag-and-drop from the **Data** pane — every measure and
column already exists.

### Page 1 — Claims Dashboard

| Visual | Icon | Field wells |
|---|---|---|
| Card ×4 | *Card* | one measure each: `Claim Count` · `Total Billed` · `Distinct Patients` · `Avg Claim` |
| Line chart | *Line chart* | X-axis `claim_date` → click its dropdown, keep **Year** only; Y-axis `Claim Count` |
| Line chart | *Line chart* | X-axis `claim_date` (Year); Y-axis `Total Billed` |
| Bar chart | *Stacked/Clustered bar* | Y-axis `Age Band`; X-axis `Claim Count` |
| Clustered bar | *Clustered bar* | Y-axis `patient_gender`; X-axis `Claim Count` **and** `Total Billed` |

### Page 2 — Clinical & Data Quality

| Visual | Icon | Field wells |
|---|---|---|
| Table | *Table* | `claim_type`, `Rows`, `Billed (unfiltered)` — shows the 68,962 / 68,962 split, $88.95M vs blank |
| Bar chart | *Stacked bar* | Y-axis `encounter_class` (from `stg_encounters`); X-axis `Encounter Count` |
| Bar chart | *Stacked bar* | Y-axis `description` (from `stg_conditions`); X-axis `Condition Records` → Filters pane → `description` → **Top N** = 10 by `Condition Records` |

Do **not** put a page-level `claim_type = "Claim"` filter on page 2 — the table is
meant to show both types. Page 1 needs no filter either; the measures already
exclude the EOB rows.

## Expected numbers (sanity check)

| Metric | Value |
|---|---|
| Claim Count | 68,962 |
| Total Billed | $88,954,081 |
| Distinct Patients | 581 |
| Avg Claim | $1,289.90 |
| Scorecard — Claim | 68,962 rows · $88,954,081 |
| Scorecard — ExplanationOfBenefit | 68,962 rows · (blank) |
| Gender | Male 41,664 / $39.4M · Female 27,298 / $49.6M |
| Age bands | 0-17: 2,687 · 18-34: 6,762 · 35-49: 4,992 · 50-64: 14,296 · 65+: 40,225 |

## If it still won't open

The error names the offending file.

- **"An error occurred while rendering the report" / `visualContainers` undefined** —
  a visual or page file isn't what this Desktop build expects. Fastest fix: delete
  the two `visuals` folders
  (`ClaimsDashboard.Report/definition/pages/*/visuals`), reopen — you get the two
  empty pages and the working model — then build per the recipe above.
- **`.pbip` / `.pbir` / `.pbism` schema error on open** — your build wants a
  different `$schema` version string. Create a throwaway blank PBIP from your own
  Desktop (`File → Save as → .pbip`), then copy its `.pbip`, `definition.pbism`,
  and `definition.pbir` over these three, keeping the `artifacts` /
  `datasetReference` paths pointed at these folders.
- **Model won't even load** — check Postgres is running and the tables exist:
  `psql -U postgres -d health_care -c "\dt public.*"`.

## TMDL compatibility

`database.tmdl` declares `compatibilityLevel: 1567`. If Desktop complains, lower it
to `1550`.

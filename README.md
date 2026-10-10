# Image Denoising with PDEs

This reproducible M2 course project compares linear heat diffusion with two
four-neighbour directional discretisations of Perona-Malik diffusion:
exponential and rational conduction. The scientific question is:

> Under what conditions does gradient-dependent diffusion change the trade-off
> between noise reduction and edge preservation compared with linear heat
> diffusion?

Code author: Mhamed Halhoul.

Report and presentation — Réalisé par : Halhoul Mhamed et Khalil Amraoui.
The two document authors have equal standing; software authorship is unchanged.

University: Université Abdelmalek Essaâdi.
Institution: Faculté Polydisciplinaire de Larache.

Master: Modélisation mathématique et applications et apprentissages.
Status: M2 en cours (degree not yet obtained).
Academic year: 2026–2027.

Module: Modélisation déterministe et applications.

Project supervisor: Prof. Hatim Tayeq.
Supervision does not imply coauthorship or endorsement of the scientific
results. Software attribution and the MIT licence are unchanged.

## Status

Documentary sources prepared on 9 October 2026 add document authorship,
figure provenance and a single named contact section. Their scientific
reference is [ae03109cdb2150b760e5a4b8bcffb56bba1b98e0](https://github.com/halhoulmhamed-droid/pde-image-denoising/commit/ae03109cdb2150b760e5a4b8bcffb56bba1b98e0),
the sealed code/data archive, not the unknown future PDF-edition commit.
See the [figure provenance registry](docs/figure_provenance.md) for file hashes,
data/code permalinks, individual versus aggregate figures and inspection limits.
No experiment, metric computation or statistical aggregation was rerun.

The report and slides were rebuilt and reviewed in an external LaTeX
environment on 10 October 2026: **52 report pages and 33 slides**. The two
authors have equal cover typography and identical PDF-author metadata.
The report groups contacts in its final annex; the presentation preserves
the 25 main and seven backup frames and adds one unnumbered “Sources et contact”
frame. Figure references are clickable. All pages were inspected, and text,
metadata, decoded streams and PDF links were checked. The 11 archived
scientific figure PDFs remain byte-identical. No scientific execution was
performed. The original Windows compiler restriction was not bypassed.
These files are prepared for a documentary commit; publication is a separate
step. The new registry URL on main must be checked after that publication.

### Previously published editions and retained evidence

Phases 1--4 are implemented: initial documentation, numerical solvers, tests,
the audited quick experiment, and a reproducible extended parameter study.
The study is conditional on two synthetic images; this is not a general image
benchmark. Phase 5 now supplies the complete French report sources,
a 16:9 Beamer presentation and oral notes. The phase-5 v2 sources correct
report composition and split dense graphs into separate PSNR/SSIM views.
That earlier report and Beamer were compiled and visually inspected in an
external Linux environment: 49 report pages and 32 slides (25 main frames
plus seven backup frames). Their compiled PDFs are retained as the preceding
edition. Layout corrections addressed slide legends and the report contents
page; the archived scientific figures and values are unchanged.
The original Windows compilation attempt remains blocked by Application
Control, and its historical evidence is retained without alteration.
See docs/phase5_v2_external_compilation.json for actual commands, versions,
PDF checks and the limited scope of that historical archive.

The preceding report and presentation credit Mhamed Halhoul and Khalil Amraoui and
state the complete academic affiliation, current Master status, module and
project supervisor. The corresponding PDFs have been rebuilt and reviewed:
49 report pages and 32 slides, with the two names also in PDF author metadata.
This documentary revision reuses the archived scientific figures and values;
no new experiment or scientific test accompanies it.

The preceding edition is presented as a scientific Master's project. The
report cover, 16:9 slide theme and oral notes use the same academic identity.
The report contains 49 pages and the presentation 32 slides; their numerical
content, archived figures and documented limitations are preserved.

The preceding published TeX sources, institutional logos and PDFs belonged to
the same revision. This working edition supplies its matching rebuilt PDFs.
See the [official logo sources and provenance](assets/logos/SOURCES.md).
The software's MIT licence is unchanged; these institutional identities are
not assigned a new licence by this project.

The preceding documents were reintegrated into the complete local project.
This README has since evolved, including the academic identity revision.
Consequently, it no longer matches its historical entry in
docs/phase5_v2_external_bundle_inventory.json. That inventory describes
the externally compiled edition and is preserved without rewriting.
The numerical results and historical evidence are unchanged. The two PDF
entry points now use the equal document authorship and contacts of this edition.

The extended run contains 60 shared noisy observations, 540 solver trajectories,
4,380 metric rows and 438 summary groups. It took 44.4073 seconds for the whole
pipeline on the recorded CPU environment. All 165 tests passed in phase 4
and the independent audit; they were not rerun for writing. Archived local
strict verification reproduces arrays, metrics and output hashes exactly
in the recorded Windows environment. Separately, the independent audit
reports successful cross-environment numerical
verification (rtol=1e-10, atol=1e-12), not bitwise equality.
All quick/extended results, frozen configurations, scientific code and
tests are protected by the phase-5 SHA-256 inventory.

The clean images are normalised to [0, 1]. Gaussian noise and solver outputs
are not clipped for numerical evaluation; clipping is used only by image
display functions. The quick protocol uses two deterministic synthetic images.
A natural-image comparison remains future work.

## Windows PowerShell reproduction

Run from the repository root with Python >=3.11. Installation and test
commands below are instructions for a fresh environment, not steps executed
during this local preparation. Recorded versions are in
results/extended/environment.json.

    py -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
    .\.venv\Scripts\python.exe -B -m pytest -q

To verify existing results without replacing any archived report:

    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/quick --report .audit-local/verification/quick_strict.json
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/quick --mode numerical --report .audit-local/verification/quick_numerical.json
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/extended_probe --report .audit-local/verification/extended_probe_strict.json
    .\.venv\Scripts\python.exe -B -m pde_image_denoising.verify --results results/extended --report .audit-local/verification/extended_strict.json

Verification recalculates deterministic solver states and metrics, but does
not measure new solver durations or rewrite archived arrays/CSV/figures.
The explicit --report paths are outside every archived results directory;
the verifier creates their parent directories. Existing local scratch
reports may be replaced, but the archived reports remain intact.
Strict is the default and requires exact reproduction in the recorded
environment. For a different environment, explicitly select --mode numerical
and a separate scratch report name (rtol=1e-10, atol=1e-12); numerical mode
retains structural/integrity checks but never claims exact reproduction.

### New experiments without overwriting the archives

The runner accepts --config, not --output-dir. It reads output_dir from the
JSON configuration. Never run the frozen configs directly in this populated
repository: quick can overwrite existing artifacts. Extended refuses a
non-empty output directory, but both protocols should use new destinations.

For a future reproduction, create configuration copies under a unique
ignored scratch directory, outside protected configs/. Change only output_dir;
keep experiment_name and every numerical parameter unchanged. In particular,
extended_probe keeps experiment_name = extended. The following preparation
example writes UTF-8 without a BOM, compatible with the JSON loader even
under Windows PowerShell 5.1:

~~~powershell
$reproductionRoot = ".audit-local/reproductions/" + [guid]::NewGuid().ToString("N")
if (Test-Path -LiteralPath $reproductionRoot) {
    throw "Choose a new reproduction directory."
}
New-Item -ItemType Directory -Path "$reproductionRoot/configs" -ErrorAction Stop | Out-Null

foreach ($protocolName in @("quick", "extended_probe", "extended")) {
    $configuration = Get-Content -LiteralPath "configs/$protocolName.json" -Raw -Encoding UTF8 | ConvertFrom-Json
    $configuration.output_dir = "$reproductionRoot/results/$protocolName"
    $configurationPath = Join-Path (Get-Location).Path "$reproductionRoot/configs/$protocolName.json"
    $configurationJson = $configuration | ConvertTo-Json -Depth 20
    [IO.File]::WriteAllText(
        $configurationPath,
        $configurationJson + [Environment]::NewLine,
        [Text.UTF8Encoding]::new($false)
    )
}

.\.venv\Scripts\python.exe -B -m pde_image_denoising.run --config "$reproductionRoot/configs/quick.json"
.\.venv\Scripts\python.exe -B -m pde_image_denoising.run --config "$reproductionRoot/configs/extended_probe.json"
~~~

Check the pilot estimate before the full run: the predefined rule is 60 times
the new pilot whole-pipeline duration from its run.log, with a 1,200-second
limit. Do not start the full run if the estimate exceeds that limit. The
archived pilot took 6.8015 seconds, giving an estimate of 408.0909 seconds
in its original environment, not a guarantee for another computer.
Only after inspecting the new pilot and its cost:

~~~powershell
.\.venv\Scripts\python.exe -B -m pde_image_denoising.run --config "$reproductionRoot/configs/extended.json"
~~~

Choose a new reproductionRoot for every repetition; do not reuse a quick
destination. These examples leave configs/ and results/ unchanged, and
generated configuration copies record the distinct output locations.
The older instructions in docs/reproducibility.md describe earlier phases;
use these current examples rather than commands targeting archived outputs.

The implementation uses NumPy float64 on CPU. PSNR and SSIM are computed by
documented NumPy implementations with an explicit unit data range; SSIM uses
uniform valid 7x7 windows and sample covariances. Both configurations fix
dx = dy = 1 pixel and dt = 0.20. Diffusion time n*dt is a numerical scale, not
wall-clock time.

## Repository map

- src/pde_image_denoising: solvers, metrics, experiment runner, plotting, checks
- tests: deterministic scientific and functional tests
- configs/quick.json: unchanged exploratory phase-3 protocol
- configs/extended.json and extended_probe.json: frozen phase-4 study and pilot
- results/quick: generated CSV, arrays, figures, tables, logs, and provenance
- results/extended: 17 PNG/PDF figure pairs, CSV/LaTeX tables, NPZ arrays,
  configuration, environment, SHA-256 manifest, analysis and strict verification
- results/extended_probe: independently recorded pilot
- results/phase4_checks: quick regression reports, outside the protected quick run
- docs: mathematical model, protocol, limitations, and resumable phase status
- report: six scientific chapters, bilingual summaries, notation,
  bibliography, reproducible annexes and CSV-derived tables
- slides: 25 main Beamer frames, seven backup frames with retained oral notes,
  and one unnumbered sources/contact frame
- scripts: standard-library documentary exports and static checks only
- references: source-verification ledger

## Reading the extended study

docs/extended_protocol.md records the plan fixed before computing;
docs/extended_findings.md reports measured observations, including unfavourable
settings. Curves show means and sample standard deviations over ten noise seeds,
not confidence intervals. All predefined K/checkpoint combinations are retained.
Any best setting selected using the ground truth is an **exploratory oracle**,
not a deployable tuning or stopping rule. PSNR and SSIM can rank methods differently.

## Scope and licence

The work is educational and makes no research-novelty claim. Deep learning,
PINNs, deblurring, segmentation, ROF implementation, and large-scale
experiments are outside the current scope.

This project is licensed under the [MIT License](LICENSE).
Copyright (c) 2026 Mhamed Halhoul.

## Reading and building the phase-5 documents

Current PDFs and retained historical review material:

- [French report (52 pages; authorship and provenance edition)](report/main.pdf)
- [Presentation (33 slides; authorship and provenance edition)](slides/main.pdf)
- [Speaker notes](slides/speaker_notes.md)
- [External compilation and review record](docs/phase5_v2_external_compilation.md)

Editable sources of this edition: [report/main.tex](report/main.tex),
[report sections](report/sections/), [report bibliography](report/references.bib)
and [slides/main.tex](slides/main.tex). They match the rebuilt PDFs.
The [provenance annex source](report/sections/provenance.tex) complements the
[figure registry](docs/figure_provenance.md). Existing sections, bibliography,
generated tables, scientific figures, results and code are unchanged.
The phase logs, protection inventories and earlier build/reproduction notes
are historical evidence, not an instruction to repeat old writes. Preserve
their original contents and interpret their status in its recorded context.
The report distinguishes continuous Perona--Malik from the implemented
four-neighbour directional variant and proves the stated discrete
properties. Every experiment figure is reused from the archived study.
Tables retain exact source values in companion CSV/JSON; rounding is for
display only. Bands are sample standard deviations, never confidence intervals.

Routine read-only documentary checks, with no new scientific results:

    .\.venv\Scripts\python.exe -B scripts/export_report_material.py --check
    .\.venv\Scripts\python.exe -B scripts/check_documentation.py

--check compares exports without writing; check_documentation.py prints its
report without replacing earlier JSON reports. Documentary aggregation reads
only recorded CSV values, including recorded durations. Regenerating exports
without --check, or writing a documentary --report, is a separate authoring
operation for a working copy, not a routine check of the archived evidence.

To rebuild with an existing LaTeX installation including French Babel,
French hyphenation, Latin Modern, Beamer and TikZ:

    latexmk -cd -pdf -interaction=nonstopmode -halt-on-error report/main.tex
    latexmk -cd -pdf -interaction=nonstopmode -halt-on-error slides/main.tex

See [docs/phase5_build.md](docs/phase5_build.md) for the original Windows
attempt and fallback commands. Its unresolved checks describe that earlier
attempt, not the subsequent external compilation.
The compiler download/version metadata are in
[docs/phase5_v2_build/compiler.json](docs/phase5_v2_build/compiler.json).
This historical diagnostic has a public version with local personal paths
redacted. The original is preserved separately; historical inventories
describe that original rather than the redacted public version.
Static source validation is separate from successful compilation. The
preceding edition was compiled, all 49 pages and 32 slides rendered
and inspected, and internal PDF destinations checked. The slide notes
allocate 23 minutes, excluding backup frames and questions. Actual delivery
time still depends on the speaker. The earlier compilation record describes
the historical edition; its commands and warnings are preserved in context.

The compiled phase-5 review ZIP is documentary: it omits scientific src,
tests, quick results and the already audited large NPZ arrays. It supplies
the report, presentation, figures and source records needed for documentary
review and is not a standalone full scientific reproduction bundle. The
external integrity check covers the 52 protected files actually present;
the other 74 entries in the original inventory are outside this archive.
The following archive command applies to the complete original repository:

    .\.venv\Scripts\python.exe -B scripts/archive_phase5.py --name phase5-v2

It refuses to create the archive unless both report/main.pdf and
slides/main.pdf exist. The previous phase-5 ZIP is preserved.
The historical portable-compiler attempt is documented in the retained
build records. The academic revision consists of documentary source changes
and rebuilding the report and slides. It does not rerun solvers or scientific
tests, change recorded measurements or regenerate scientific figures.

## Contact de Halhoul Mhamed

These confirmed contacts belong only to Halhoul Mhamed, not to both document
authors. No contact information for Khalil Amraoui has been supplied.

- Institutional: [halhoul.mhamed@etu.uae.ac.ma](mailto:halhoul.mhamed@etu.uae.ac.ma)
- Personal: [halhoulmhamed@gmail.com](mailto:halhoulmhamed@gmail.com)
- Project: [GitHub repository](https://github.com/halhoulmhamed-droid/pde-image-denoising)

The Git noreply identity is a commit identity, not a public contact address.
Software attribution and the MIT licence remain unchanged. CITATION.cff retains
the software author and adds a separate two-author report citation.

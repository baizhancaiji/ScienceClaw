---
name: nature-figure
description: >-
  Submission-grade Nature/high-impact journal figure workflow, using Python (matplotlib/seaborn) by default.
  Use whenever the user asks to create, revise, audit, or polish manuscript figures, multi-panel scientific
  plots, figures4papers-style matplotlib plots, or journal-ready SVG/PDF/TIFF outputs. Before plotting,
  define the figure's conclusion, evidence logic, export needs, and review risks.
  Triggers: "Nature figure", "publication plot", "scientific figure", "SCI figure", "论文配图", "期刊图表".
  Not for dashboards or Illustrator/Figma-first infographics.
---

# Nature Figure Making Skill (Linux/ScienceClaw 适配版)

A guide for producing publication-quality scientific figures as a visual argument, not
as isolated pretty plots. Every figure starts from a claim, an evidence hierarchy, and a
review-risk check before code or aesthetics.

**默认后端：Python (matplotlib/seaborn)**。若用户明确要求 R，使用 ggplot2。不设阻塞式问答门——直接按 Python 执行，用户要求切换时再切。

Color policy: prefer **unified method families across all panels** over maximal hue separation.
Reserve green/red mainly for gains, drops, and other directional cues.

## 执行策略（Write → Execute → Fix 循环）

每张图按以下流程：

1. **设计合同**（见下方 "Figure Contract"）
2. **写 Python 脚本**到工作区
3. **`execute` 运行脚本** → 生成 PNG/SVG/PDF
4. **`read_file` 查看图片** → 目视 QA
5. **有问题则修改脚本重跑**，直到满意

## Figure Contract (before plotting)

1. Core conclusion: write the one-sentence claim the figure must defend.
2. Evidence chain: map each planned panel to the claim, and drop panels that do not carry
   a unique piece of evidence.
3. Archetype: classify the figure as `quantitative grid`, `schematic-led composite`,
   `image plate + quant`, or `asymmetric mixed-modality figure`.
4. Journal/export contract: set final dimensions, editable text, source data, statistics,
   image-integrity notes, and export formats before styling.

The highest-priority rule is: **the chart serves the scientific logic**. Aesthetic polish,
template matching, and complex layout are subordinate to making the core conclusion clear,
defensible, and reviewable.

## User-facing privacy rule

Do not disclose private local paths, private filenames, chat-attachment names, internal
reference filenames, template identifiers, or the provenance of private working materials
in user-facing replies, generated code comments, figure legends, reports, or manuscript
text. Use generic descriptions such as "the provided R template collection", "a private
working draft", or "the internal figure contract". Only reveal an exact path or source
file when the user explicitly asks for that audit trail.

## Python quick-start

**Python-only execution rule.** When the user has selected Python, do all figure
drawing, previewing, exporting, and visual QA in Python. Do not call R/ggplot2,
ComplexHeatmap, patchwork, or any R graphics device to create a temporary preview,
fallback export, or layout approximation. If Python or required Python plotting
packages are missing, stop before rendering and report the missing dependency. You
may still write the Python script, provide `pip`/environment install commands, or
ask permission to install dependencies, but do not cross-render the figure in R.

```python
import matplotlib as mpl
import matplotlib.pyplot as plt

mpl.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans", "sans-serif"],
    "svg.fonttype": "none",     # editable text in SVG
    "pdf.fonttype": 42,         # editable TrueType text in PDF
    "font.size": 7,             # use 15-24 only for large slide-sized panels
    "axes.spines.right": False,
    "axes.spines.top": False,
    "axes.linewidth": 0.8,
    "legend.frameon": False,
})

def save_pub_py(fig, filename, dpi=600):
    fig.savefig(f"{filename}.svg", bbox_inches="tight")
    fig.savefig(f"{filename}.pdf", bbox_inches="tight")
    fig.savefig(f"{filename}.tiff", dpi=dpi, bbox_inches="tight")
```

Use `text.usetex = True` only when LaTeX is installed and math-rich labels are required.

## R quick-start

```r
library(ggplot2)
library(patchwork)

theme_set(
  theme_classic(base_size = 6.5, base_family = "Arial") +
    theme(
      axis.line = element_line(linewidth = 0.35, colour = "black"),
      axis.ticks = element_line(linewidth = 0.35, colour = "black"),
      legend.title = element_text(size = 6.2),
      legend.text = element_text(size = 5.8),
      strip.text = element_text(size = 6.2, face = "bold"),
      plot.title = element_text(size = 7, face = "bold"),
      panel.grid = element_blank()
    )
)

save_pub_r <- function(plot, filename, width_mm = 183, height_mm = 120, dpi = 600) {
  w <- width_mm / 25.4
  h <- height_mm / 25.4
  svglite::svglite(paste0(filename, ".svg"), width = w, height = h)
  print(plot)
  dev.off()
  grDevices::cairo_pdf(paste0(filename, ".pdf"), width = w, height = h, family = "Arial")
  print(plot)
  dev.off()
  ragg::agg_tiff(paste0(filename, ".tiff"), width = w, height = h, units = "in", res = dpi)
  print(plot)
  dev.off()
}
```

## Default operating stance

- Start by classifying the requested figure into one of four archetypes:
  `quantitative grid`, `schematic-led composite`, `image plate + quant`, or `asymmetric mixed-modality figure`.
- Prefer one **hero panel** plus subordinate evidence panels over filling the canvas with equal-sized subplots.
- If the user asks for a single chart, still identify its role in the manuscript claim:
  discovery, mechanism, validation, comparison, robustness, or clinical/biological relevance.
- Keep the background white for plots and diagrams; switch to black only for microscopy / volume-rendering image plates.
- Prefer direct labels over legends when categories are spatially fixed or the legend would force unnecessary eye travel.
- Keep one restrained palette per figure: usually one neutral family, one signal family, and one accent family.
- Treat statistics, `n`, error-bar definitions, source-data traceability, and image-integrity notes as part of the figure,
  not as optional caption cleanup.
- When the user asks for broad `Nature` style rather than ML/NMI-specific style, read `references/nature-2026-observations.md` before choosing layout.
- When the user references `figures4papers` or the older `scientific-figure-making` skill,
  treat this skill as the successor and open `references/demos.md` for bundled Python demo scripts.

## When to load this skill

- Python or R figures for **papers, slides, or reports** targeting Nature, Science, Cell, NeurIPS, ICLR, or similar venues.
- Requests involving **grouped bars, trend lines, heatmaps, radar plots, multi-panel grids**, or **PDF/SVG/high-DPI** output.
- Any mention of "Nature style", "publication figure", "paper figure", "SCI figure", "figures4papers", "scientific-figure-making", "R plotting template", or "high-quality scientific plot".
- Requests to improve a figure's logic, aesthetics, panel layout, figure legend, export quality, or journal-readiness.

## When NOT to load

- Plotly, Altair, Bokeh, or other interactive/web-first plotting.
- EDA-only plots without a publication target.
- Primary workflow is 3D, GIS, or non-scientific illustration tooling.
- Illustrator / Figma–first layout.

## Related files

| File | Open when |
|------|-----------|
| [references/figure-contract.md](references/figure-contract.md) | Need to convert a user request into core conclusion, evidence hierarchy, panel map, and review-risk checks |
| [references/backend-selection.md](references/backend-selection.md) | User has not chosen Python/R, asks for a recommendation, or a mixed Python/R workflow is possible |
| [references/r-workflow.md](references/r-workflow.md) | User chooses R or provides R scripts/templates/data |
| [references/r-template-index.md](references/r-template-index.md) | Need to adapt a user-provided or private R template collection without exposing source paths |
| [references/qa-contract.md](references/qa-contract.md) | Before final delivery, revision package, microscopy/blot figure, or journal-specific audit |
| [references/design-theory.md](references/design-theory.md) | Typography, color theory, layout rationale, export policy |
| [references/api.md](references/api.md) | Python PALETTE, helper function signatures, validation rules |
| [references/common-patterns.md](references/common-patterns.md) | Python layout patterns: hero panels, legend-only axes, dark image plates, asymmetric layouts |
| [references/nature-2026-observations.md](references/nature-2026-observations.md) | Real `Nature` page archetypes: schematic-led composites, dark image plates, clinical triptychs, asymmetric hero layouts |
| [references/tutorials.md](references/tutorials.md) | End-to-end walkthroughs: bars, trends, heatmaps |
| [references/chart-types.md](references/chart-types.md) | Radar, 3D sphere, fill_between, scatter patterns |
| [references/demos.md](references/demos.md) | Bundled figures4papers Python scripts and output previews for concrete pattern adaptation |

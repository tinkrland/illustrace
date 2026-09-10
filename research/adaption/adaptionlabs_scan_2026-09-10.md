# AdaptionLabs Research & Illustrace Integration Report

**Date**: September 9, 2026  
**Target Repository**: `illustrace` (`/app/conversations/6a9ff0a40b2daadbdc35cf4c/illustrace`)  
**Output Report**: `/app/conversations/6a9ff0a40b2daadbdc35cf4c/scratch_adaptionlabs_report.md`  

---

## 1. AdaptionLabs API Status & Exposed Capabilities

### A. Live Probing & Status Verification
As instructed, the AdaptionLabs API environment was probed using `curl` and Python standard library HTTP clients with `$ADAPTIONLABS_API_KEY`. 

#### Direct Probing Results (Verified 2026-09-09)
* **Main Website (`https://adaptionlabs.ai`)**: **LIVE (HTTP 200 OK)**. Served via Next.js on Vercel (`server: Vercel`, `x-vercel-id: cle1:...`).
* **API Domain (`https://api.adaptionlabs.ai/*`)**: **UNREACHABLE / SERVICE UNAVAILABLE (HTTP 503)**.
  * The API domain resolves to an AWS Elastic Load Balancer (`server: awselb/2.0`), which returns an HTTP 503 status (`503 Service Temporarily Unavailable`).
  * Plain HTTP connections (`http://api.adaptionlabs.ai/`) timed out on port 80.
* **Codebase Cross-Verification**: This matches pre-existing findings in the `illustrace` codebase (`illustrace/research/adaption/upload_preferences.py`), where script documentation notes: *"adaption's storage verification endpoint was returning 503 on 2026-09-09 (s3 puts succeed, their verify service doesn't respond)."*

#### Exact Endpoints Tested & Confirmed Responses

| Endpoint / URL | Method | HTTP Status | Server / Header | Result / Note |
|---|---|---|---|---|
| `https://adaptionlabs.ai/` | GET | **200 OK** | Vercel | Main site online |
| `https://api.adaptionlabs.ai` | GET | **503** | `awselb/2.0` | Service Temporarily Unavailable |
| `https://api.adaptionlabs.ai/health` | GET | **503** | `awselb/2.0` | Service Temporarily Unavailable |
| `https://api.adaptionlabs.ai/v1/health` | GET | **503** | `awselb/2.0` | Service Temporarily Unavailable |
| `https://api.adaptionlabs.ai/v1/models` | GET | **503** | `awselb/2.0` | Service Temporarily Unavailable |
| `https://api.adaptionlabs.ai/docs` | GET | **503** | `awselb/2.0` | Service Temporarily Unavailable |
| `https://api.adaptionlabs.ai/openapi.json` | GET | **503** | `awselb/2.0` | Service Temporarily Unavailable |
| `http://api.adaptionlabs.ai/v1/models` | GET | **Timeout** | N/A | Connection timed out |
| `https://adaptionlabs.ai/api/health` | GET | **404** | Vercel | Route not found on web host |
| `https://adaptionlabs.ai/api/v1/models` | GET | **404** | Vercel | Route not found on web host |
| `https://adaptionlabs.ai/models` | GET | **404** | Vercel | Route not found on web host |
| `https://adaptionlabs.ai/docs` | GET | **404** | Vercel | Route not found on web host |

*(Total API probe requests performed: 13 requests).*

---

### B. Exposed API Architecture & SDK Capabilities (From AdaptionLabs Site Research)
Following the fallback protocol, full site pages and research articles were scraped via Firecrawl (`POST https://api.firecrawl.dev/v1/scrape`). AdaptionLabs exposes the following core product pillars, SDK constructs, and model endpoints:

#### 1. Python SDK Interface (`adaption`)
```python
from adaption import Adaption

client = Adaption(api_key=ADAPTION_API_KEY)

# 1. Dataset Upload & Adaptive Data Transformation
dataset = client.datasets.upload_file("dataset.jsonl")  # or client.datasets.upload.initiate/complete
adaptive_run = client.datasets.run(
    dataset.dataset_id,
    column_mapping={"prompt": "instruction", "completion": "output"}
)
client.datasets.wait_for_completion(dataset.dataset_id)

# 2. Automated Research Loop (AutoScientist)
run = client.autoscientist.create(
    dataset_id=dataset.dataset_id,
    target_win_rate=0.85
)

# 3. Model Registry Lookup
models = client.training_models.list()
```

#### 2. Key Capabilities & Product Pillars
* **Invent a Dataset (Specification-First Data Generation)**: Generates training datasets directly from intent/behavior descriptions without requiring a seed corpus, prior manual schema design, or pre-existing raw data.
* **AutoScientist Automated Research Loop**: Automatically co-optimizes training datasets and hyperparameter recipes across 4 phases: *Recipe Search → Data Optimization → Model Training → Evaluation*. Iterates until quality converges on target win rate or exhausts budget.
* **Multimodal AutoScientist**: Single automated research workflow supporting joint text and image training/alignment (e.g. document intelligence, UI layout, visual domain adaptation).
* **Tiny AutoScientist & Model Harnessing**: Optimizes smaller models (0.8B to 8B parameter range) via specialized evaluation harnesses and data shaping, enabling edge/on-device deployment without sacrificing accuracy.
* **Write-Time Agent Memory Structuring**: Extracts knowledge into structured memory at write time rather than optimizing search at retrieval time, explicitly separating *atomic facts* (e.g., exact values, contract numbers) from *narrative summaries* (reasoning, context).

---

## 2. Concrete AdaptionLabs Concepts to Further Illustrace

### Current Status in Illustrace
Illustrace currently integrates two AdaptionLabs concepts (documented in `illustrace/research/VALIDATION_LOOP.md`):
1. **Specification-First Validation Datasets**: Preregistered experiment specs (`survey/specs/batch_2.json`) that bind stimulus creation parameters, question prompts, catch positions, and registry pass criteria into a single document.
2. **Closed-Loop Metric vs Human Co-Optimization**: The AutoScientist loop shrunk to bench scale (`survey/analyze_batch.py`), which ingests survey results, excludes bad judges via catch rules, computes bootstrap 95% CIs, applies verdict rules to update `engine/registry.py` ladder statuses, and flags 50/50 human splits as stimulus failures.

---

### New AdaptionLabs Concepts to Extend Illustrace

#### Concept A: Write-Time Stylometric Extraction (Atomic vs Narrative Memory)
* **AdaptionLabs Philosophy**: Most agent memory systems fail at write time, not retrieval time. Extracting structured knowledge up front prevents context bloat and re-computation.
* **Application to Illustrace**: Currently, when Style Composer (`application/`) or Stylebench evaluates reference artworks (`data/test_images/`), raster metrics (`analyzer.py`) must re-analyze images or LLM passes must re-evaluate styles on every turn.
* **Concrete Integration**: Implement a write-time extraction pipeline (`engine/manifest.py` / `data/test_images/manifest.json`). When reference images or SVG substrate assets are added, compute and store both:
  1. *Atomic Stylometrics*: Quantitative factor numbers (`stroke_width_cv: 0.42`, `edge_direction_entropy: 0.82`, `texture_energy: 14.2`, `palette_temp: warm`).
  2. *Narrative Style Context*: Descriptive tags ("Riso street scene with hand-inked line quality, heavy grain on flat fills").
  Style Composer and Stylebench can then query atomic parameters instantly without re-running expensive image processing.

#### Concept B: Niche Domain Harnesses (Domain-Specific Metric Suites & Thresholds)
* **AdaptionLabs Philosophy**: *"The days of monolithic AI are over. Averages erase the exceptional."*
* **Application to Illustrace**: In `illustrace/README.md`, the core premise is that a single scalar `"style similarity: 0.81"` is a meaningless average. Furthermore, applying a single flat metric suite across all visual illustration domains causes false demotions (e.g., scoring line weight jitter on flat gouache paintings or texture energy on clean vector icons).
* **Concrete Integration**: Create domain-specific metric profiles in `engine/analyzer.py` and `engine/registry.py` (e.g., `Architectural Vector`, `Storybook Gouache`, `Low-Poly 3D`, `Riso Print`). Each domain bucket specifies which subset of the 10 visual factors to measure and sets domain-tailored validation thresholds.

#### Concept C: Intent-to-Benchmark Spec Generator ("Invent a Benchmark Spec")
* **AdaptionLabs Philosophy**: "Invent a Dataset" converts high-level human intent into structured dataset specs without requiring manual schema creation.
* **Application to Illustrace**: Currently, `survey/specs/batch_2.json` is written by hand. 
* **Concrete Integration**: Build `survey/build_spec.py`, an automated script that takes a research hypothesis (e.g. *"test whether human perception of line taper variation remains scale-invariant across 2x zoom on architectural assets"*) and automatically outputs a validated `batch_X.json` experiment spec with parameter recipes, catch positions, and ground-truth assertions.

#### Concept D: Multimodal Baseline Evaluation Harness
* **AdaptionLabs Philosophy**: Multimodal AutoScientist co-optimizes text and image conditioning in a unified research workflow.
* **Application to Illustrace**: Stylebench thesis requirement #5 demands evaluating whether reference-based generation systems prevent *reference-content leakage* (copying background objects, composition, or typography when only brush stroke was requested).
* **Concrete Integration**: Add a multimodal VLM pass to `benchmarks/run_bench.py` and `benchmarks/test_conflation_leakage.md`. Combine deterministic factor deltas (`analyzer.py`) with VLM-based semantic content leakage scoring to evaluate candidate baselines on both visual factor movement and content preservation.

#### Concept E: Tiny Model Stylometric Harness for Figma & Client Presets
* **AdaptionLabs Philosophy**: "A Better Harness Can Unlock Smaller Models" (0.8B - 8B range) for edge/interactive environments.
* **Application to Illustrace**: Illustrace produces parametric presets (recipes), not static baked renders. Running heavy diffusion or large VLM pipelines inside client apps (Figma plugin / web application) is slow and expensive.
* **Concrete Integration**: Use a compact vision model (1B–3B parameters) wrapped in an Illustrace metrology harness to perform real-time factor classification and recipe preset prediction directly in client tools.

---

## 3. Ranked Shortlist of Concrete Next Integrations

| Rank | Integration Title | AdaptionLabs Concept | Target File / Pipeline Stage | Concrete Description | Effort Estimate |
|---|---|---|---|---|---|
| **1** | **Intent-to-Spec Generator (`survey/build_spec.py`)** | *Invent a Dataset* | `survey/build_spec.py` → `survey/specs/batch_X.json` | An LLM-backed spec generator that converts natural language style hypotheses into schema-valid `batch_X.json` experiment specs (declaring stimulus recipes, catch positions, and pass criteria). | **Low** <br>*(1–2 days)* |
| **2** | **Write-Time Stylometric Manifest Pipeline** | *Write-Time Memory Structuring* | `engine/registry.py` & `data/test_images/manifest.json` | Write-time extraction script that runs when new reference images or SVG substrate assets are added. Extracts atomic factor vectors (`stroke_cv`, `edge_entropy`, `texture_energy`) + narrative tags into a persistent manifest, eliminating runtime re-analysis in `application/`. | **Low–Medium** <br>*(2 days)* |
| **3** | **Adaptive Stimulus Failure Regeneration Loop** | *AutoScientist Closed Loop* | `survey/analyze_batch.py` → `benchmarks/make_stimuli.py` | Connects `analyze_batch.py` directly to `make_stimuli.py`. Automatically reads `stimulus_failures_regenerate_next_batch` (50/50 human splits) and re-renders those specific stimulus pairs at higher parameter delta contrast for the next survey batch. | **Medium** <br>*(2–3 days)* |
| **4** | **Niche Domain Metric Harnesses** | *Niche Specialization* | `engine/analyzer.py` & `results/PARAMETER_MATRIX.md` | Extends `analyzer.py` with domain-specific metric profiles (`analyze_image(img, domain=" architectural_vector")`). Masks irrelevant factors and applies domain-specific pass thresholds per ontology bucket (preventing false demotions). | **Medium** <br>*(3–4 days)* |
| **5** | **Multimodal Reference-Leakage Evaluator** | *Multimodal AutoScientist / Harnessing* | `benchmarks/run_bench.py` & `benchmarks/test_conflation_leakage.md` | Integrates a lightweight VLM evaluation pass into `run_bench.py` to quantitatively score content-preservation and reference-leakage alongside deterministic factor deltas. | **Medium–High** <br>*(4–5 days)* |

---

## Summary of Verification Evidence & Methodology
1. **API Status**: Confirmed 503 Service Temporarily Unavailable on `api.adaptionlabs.ai` across 7 endpoint path variations via HTTP/HTTPS GET requests. Confirmed HTTP 200 OK on `adaptionlabs.ai`.
2. **Documentation & Blog Scraping**: Used Firecrawl (`POST https://api.firecrawl.dev/v1/scrape`) to retrieve full content for homepage, product pages (`/invent-a-dataset`, `/auto-scientist`), and research blog posts (`/blog/autoscientist-api`, `/blog/multimodal-autoscientist`, `/blog/agent-memory-write-time`, `/blog/a-better-harness-can-unlock-smaller-models`).
3. **Illustrace Codebase Audit**: Read and analyzed `illustrace/README.md`, `research/VALIDATION_LOOP.md`, `research/STYLEBENCH_THESIS.md`, `research/adaption/upload_preferences.py`, `survey/build_batch.py`, `survey/analyze_batch.py`, and `engine/registry.py`.

# Written analysis

Hand-written interpretation of the machine-found candidates above. Kept in a
separate file (`analysis_notes.md`) and appended by
`scripts/09_failure_analysis.py`, so regenerating the report never destroys it.

## The one catastrophic failure: `eval_syn_012`

The only unparseable output in 120 generations, and the single worst regression
(tuned rubric 1.00 vs base 3.60; lost pairwise to *both* baselines). It is worth
reading the actual break:

```
"The basis on which a refund is calculated was not stated consistently: "
    + "refunding the unused sessions at the discounted rate",
    + "refunding at the discounted rate less an administration amount",
```

The model emitted **Python-style string concatenation inside JSON**. It was not
truncated — it generated 717 tokens of a 2048 budget and closed the object
cleanly at the end.

Why here? This record is `vague`, and the input describes a refund policy stated
three inconsistent ways. The model tried to enumerate the competing alternatives
inside a single list item, and reached for a code idiom to join them. Nothing in
120 training examples demonstrates "the input contradicts itself, enumerate the
options", so under that pressure it fell back on a pretraining habit.

The lesson is about the *depth* of what LoRA learned. Strict-JSON compliance went
0% → 98%, but that discipline is shallow: it survives ordinary inputs and breaks
when the content pushes the model toward a structure it never saw supervised.
A schema-constrained decoder would eliminate this entire failure mode and is the
cheapest robustness win available (see SUMMARY v0.2).

## The field-level regressions: `bottlenecks_and_risks` and `human_approvals_controls`

These are the only two fields where tuned scores *below* a baseline:

| Field | Base 0-shot | Base 2-shot | Tuned |
|---|---|---|---|
| `bottlenecks_and_risks` | 3.32 | 3.19 | **2.77** |
| `human_approvals_controls` | 2.34 | 2.53 | **2.35** |

The obvious hypothesis — that tuned under-generates here — is **wrong**, and the
measurements say so. On `bottlenecks_and_risks` tuned produces 6.0 items of 19.4
words against a reference of 6.3 items of 23.9 words; the 2-shot baseline manages
5.5 items of 10.8 words. Tuned is *closer* to reference shape on both axes.

Reading an actual regressed record (`eval_syn_005`) shows what is really
happening:

- **Base 2-shot:** "Lack of monitoring leads to inconsistent and incorrect
  responses" — terse, generic, but safely hedged.
- **Tuned:** "No one owns the group so nobody takes responsibility for its
  content or quality" — fluent, longer, causal, confident.
- **Reference:** "A group of 1,400 members set up during a closure period was
  never wound down and now carries live operational questions with nobody
  assigned to it" / "A former duty manager who left last year remains an admin,
  so someone outside the business holds administrative control".

The reference's value is **evidential specificity**: the 1,400 members, the
ex-employee still holding admin rights. Tuned has learned the reference's
*rhetorical form* — the long "X, so Y" causal construction — without its
*anchoring in named facts from the input*. It writes confident analysis-shaped
prose that is less tied to evidence than it sounds.

That is a coherent story for why a judge instructed to reward grounding marks it
down relative to a terse baseline: confident-but-unanchored claims are penalised
harder than vague-but-safe ones. **Stated as the most plausible reading, not a
demonstrated one** — it rests on one inspected record against a 40-record
aggregate, and the two regressions are small (-0.42 and -0.18 on a 1-5 scale).

It is also the expected failure mode for 120 examples: style is cheap to learn
and specificity is not. These two fields are the most open-ended reasoning
targets in the schema, so they are exactly where form-without-substance shows up
first.

## Where fine-tuning helped least: seen verticals

The derived `vertical_unseen_in_train` axis produces the only negative rubric
slice in the whole analysis:

| Slice | n | det delta | rubric delta |
|---|---|---|---|
| vertical **seen** in train | 12 | +0.088 | **-0.10** |
| vertical **unseen** in train | 28 | +0.110 | +0.32 |

Fine-tuning helped *least* on the verticals it actually trained on. That is
counter-intuitive and worth stating plainly rather than smoothing over.

The likely explanation is a ceiling effect rather than damage: the 12 seen-vertical
records are the in-domain synthetic ones, where the baselines already performed
best (base composite 0.588 vs 0.632 on unseen), so there was less headroom. The
gains concentrate where the baseline was weakest — vague inputs (+0.50 rubric)
and contradictory inputs (+0.14 det composite from a much lower base).

Note this slice is **invisible** under the delivered `ood_vertical` flag, which
marks all 12 PET records `False` despite every PET vertical being unseen in
training. Under that flag alone the analysis would have shown a uniformly
positive picture. This is the concrete payoff of carrying three independent axes
instead of trusting one delivered label.

## Real text vs synthetic

PET (real, human-written) shows a *smaller* deterministic gain than synthetic
(+0.055 vs +0.124) but a *larger* rubric gain (+0.35 vs +0.12). The two signals
disagree, and neither should be suppressed.

The most likely reason is the reference asymmetry: PET references are
`model_generated_unverified`, so `step_coverage_vs_reference` measures agreement
with an unverified target rather than correctness. That is exactly why pairwise
judging was designated the primary signal for the PET slice — and on pairwise,
tuned wins there too.

The honest summary is that the tuned model transfers to real text, and the
transfer is real but measured less precisely than on synthetic data.

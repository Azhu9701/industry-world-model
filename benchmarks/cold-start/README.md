# World Model Cold Start Benchmark

The Cold Start Benchmark asks a deliberately unfamiliar Agent to enter an Industry World Model using only the public repository contract.

It tests a narrow question:

> Can an Agent with no private AIMAN context discover the rules, preserve epistemic boundaries, and produce a safe review-first contribution?

This is not a general intelligence benchmark. It measures interoperability with the World Model contract.

## v0.1 flow

The first benchmark has two stages.

1. **Discovery** — the Agent receives only the root `README.md` and must identify the public files it needs before acting, while preserving the write boundary.
2. **Contribution** — the Agent receives those public contracts plus a synthetic robotics change and must produce a v0.3 contribution packet.

The default case deliberately contains several traps that are common in real data work:

- the company already exists canonically and should not be redeclared;
- the robot is new and should be declared;
- "released" does not prove "manufactures";
- Q4 shipping is a future plan, not a completed deployment or mass-production Event;
- price appears in the source, but `price` is not a claim predicate in the current robotics pack;
- payload and locomotion are directly supported and are legal pack predicates;
- the product release should be corroborated by both supplied sources;
- all incoming factual objects must remain `proposed`.

## What is scored

The runner combines structural validation with semantic checks.

| Area | Examples |
| --- | --- |
| Discovery | finds `AGENTS.md`, WORLD docs, protocol, and pack |
| Authority | no direct canonical or database-write assumption |
| Protocol | generated packet passes v0.3 Schema + pack + Evidence validation |
| Identity | existing canonical Entity is referenced rather than redeclared |
| Evidence | multiple sources preserved and linked to the Event |
| Event semantics | product release modeled; future shipping not promoted to deployment |
| Relation semantics | no `manufactures` edge inferred from release wording |
| Recall | directly supported `release_date`, `payload`, and `locomotion` retained |
| Trust boundary | Claim / Relation / Event status remains `proposed` |

Critical failures fail the benchmark even if the numeric score is high.

The default pass threshold is 85.

## Self-test

Install the protocol validator dependencies:

```bash
python3 -m pip install -r protocol/requirements.txt
```

Then run:

```bash
python3 scripts/run-cold-start-benchmark.py --self-test
```

The self-test checks that the reference fixture scores 100 and that the evaluator catches:

- duplicate declaration of an existing canonical Entity;
- unsupported `manufactures` inference;
- future-plan-as-completed-deployment inference;
- self-promotion from `proposed` to `verified`.

CI runs the same self-test.

## Run an external model

The benchmark is model-agnostic. The command must read the prompt from stdin and write its answer to stdout.

The runner executes the supplied command through the local shell, so use only commands you trust. Model output is treated as data, not as a command.

Example with a local Ollama model:

```bash
python3 scripts/run-cold-start-benchmark.py \
  --command 'ollama run qwen3:1.7b --nowordwrap --think false --hidethinking --format json' \
  --output-dir /tmp/iwm-qwen-cold-start
```

The command is invoked twice: once for Discovery and once for Contribution.

For CLIs that do not guarantee clean JSON, the runner strips ANSI control codes and extracts the first parseable JSON object.

## Score saved responses

A model can also be evaluated without being installed locally:

```bash
python3 scripts/run-cold-start-benchmark.py \
  --discovery-response /path/to/discovery.txt \
  --contribution-response /path/to/contribution.txt \
  --output-dir /tmp/iwm-external-agent
```

This makes it easy to test ChatGPT, Claude, Gemini, Kimi, enterprise Agents, or a custom runtime using the same case.

## Artifacts

A run writes:

```text
discovery.prompt.txt
discovery.raw.txt
discovery.json
contribution.prompt.txt
contribution.raw.txt
contribution.json
report.json
```

Model stderr is also preserved when `--command` is used.

By default artifacts go to the system temporary directory, not the repository.

## Case format

Cases live under `benchmarks/cold-start/cases/`.

A case separates:

- discovery expectations;
- public context files;
- canonical lookup fixtures;
- source Evidence;
- task rules;
- hidden evaluator expectations.

The model receives the task fixture but **not** the hidden `expected` section. It cannot pass by copying the scoring answer.

The reference fixtures under `benchmarks/cold-start/fixtures/` are for evaluator self-test only and are not included in the model prompt.

## Why this exists

WORLD.md says specifications should mature from real Agent friction.

The benchmark turns that principle into an executable loop:

```text
change World docs / protocol
        ↓
run unfamiliar Agents
        ↓
observe identity / evidence / event failures
        ↓
classify repeated friction
        ↓
improve docs, Schema, validator, CI, or runtime
        ↓
run again
```

The benchmark should grow only when repeated real failures justify a new case or check.

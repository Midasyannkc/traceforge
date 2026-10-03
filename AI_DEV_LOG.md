# AI Development Log

This project was built with Claude Code as an AI-assisted development
tool, directly relevant to this JD's "AI-forward coding mindset, using
tools like Claude and Cursor to ship higher-quality work at pace" and its
"demonstrable, day-to-day usage and knowledge of AI-forward coding tools
such as Claude Code." This log discloses what was AI-assisted versus
human-directed and validated.

| Area | AI-assisted | Human-directed / validated |
|---|---|---|
| Real spec sourcing | Cloned and searched the OTel semantic-conventions repository for the real GenAI span/metric attribute definitions | Confirmed the extracted YAML is the real, current schema (not a deprecated or unrelated model) before building the event generator and instrumentation against it; decision to cite five real, dated, independently reported AI agent incidents rather than fabricate illustrative ones |
| Synthetic telemetry | Wrote the event generator and its baseline/shifted/burst period structure | Chose the specific shift magnitude (latency ~2.4x, tool-error rate ~9x) and burst rate (~3x) so the resulting incidents are genuinely detectable, not tuned to trivially pass |
| Iceberg loader | Wrote the naive and fixed loader implementations | Verified the real Iceberg `upsert` behavior against a genuine mixed-overlap retry batch (not just an exact-repeat retry) before trusting the fix |
| Kinesis consumer | Wrote the naive and fixed consumer implementations | Chose the time-boxed-poller framing (a real, common serverless anti-pattern) over an arbitrary throttle, and verified the fixed consumer drains the real burst exactly, not approximately |
| Drift monitor | Wrote the PSI implementation and both check functions | Identified the self-referential-baseline failure mode as the bug to model (a real, known production anti-pattern in model monitoring) rather than an arbitrary threshold miss, and added a no-false-positive test within the baseline period itself |
| PII redaction | Wrote the naive and fixed regex patterns | Chose the dot-separated phone format as the real, realistic coverage gap (not an exotic edge case), and verified the fix against all three real formats, not just the one that was missing |
| CDK infrastructure | Wrote the stack construct | Ran real `cdk synth` and real `aws_cdk.assertions.Template` checks rather than hand-inspecting generated JSON, so the "least-privilege IAM role" claim is a tested fact (no wildcard actions in any policy statement), not an assertion |
| Documentation | Drafted README/incident-report prose | Verified every number quoted in the docs against a live rerun of the test suite before publishing |

**What this demonstrates for the role:** AI tools accelerated the
mechanical parts (writing generators, loader/consumer/monitor
implementations, CDK constructs, drafting docs), while the judgment
calls this JD actually tests for -- choosing realistic failure modes
grounded in real incidents rather than convenient ones, verifying a fix
against a genuinely harder case than the one that exposed the bug, and
confirming infrastructure security properties with real assertions
instead of eyeballing generated templates -- stayed human-directed
throughout.

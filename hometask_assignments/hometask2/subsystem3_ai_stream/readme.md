# Subsystem 3 · Advisor stream processing

Joywin Bennis · Matriculation number 7225872 · joywin.bennis004@stud.fh-dortmund.de

`AdvisorSignalFilter` and `EnergyInsightTransformer` inherit the data subsystem's `StreamProcessor`. They support the same `process(reading)` contract and inherited `|`, `+`, and lazy `run(stream)` operations.

The filter selects significant after-hours use or high-power events. The transformer adds factual context and investigation suggestions. Run the advisor branch after the energy balance stage so advisor filtering does not change those balances.

From the repository root:

```bash
python -m hometask_assignments.hometask2.subsystem3_ai_stream.demo
```

No dependencies, API keys, or live model calls are required. See the [assignment README](../readme.md) for UML, configured thresholds, expected output, and interval timing.

# Subsystem 3 · Individual energy stream solution

Joywin Bennis · Matriculation number 7225872 · joywin.bennis004@stud.fh-dortmund.de

A self-contained implementation of all four Hometask 2 OOP requirements:

- `StreamProcessor`: ABC with an abstract `process()` method.
- `PowerFilter` and `CarbonTransformer`: specialized processors sharing that API.
- `Pipeline`: stages composed through overloaded `|`.
- `MeterStream`: explicit iterator consuming the `sample_readings()` generator.
- `run()`: generator producing transformed results lazily.

```bash
python -m hometask_assignments.hometask2.subsystem3_ai_stream.demo
```

Run from the repository root. Five simulated 15-minute readings produce three accepted results. The filter removes inactive, non-finite, and below-threshold power readings. The transformer calculates kWh and kg CO2 using a demonstration factor.

The code needs no database, model provider, third-party package, or subsystem 2 import. See the [assignment README](../readme.md) for the UML and calculation details.

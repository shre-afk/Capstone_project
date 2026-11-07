"""Run: python -m hometask_assignments.hometask2.subsystem3_ai_stream.demo"""

from .processors import CarbonTransformer, PowerFilter
from .stream import MeterStream, sample_readings


def main():
    pipeline = PowerFilter(min_power_kw=0.8) | CarbonTransformer()
    stream = MeterStream(sample_readings())
    for result in pipeline.run(stream):
        print(result)


if __name__ == '__main__':
    main()

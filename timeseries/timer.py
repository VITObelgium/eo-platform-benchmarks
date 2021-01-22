from time import perf_counter
from statistics import mean, stdev


class Timer:

    def __init__(self):
        self._start_time = None
        self._feature_splits = None
        self._period_splits = None
        self._stats = None

    def start(self):
        if self._start_time is not None:
            return

        self._start_time = perf_counter()
        self._feature_splits = [self._start_time]
        self._period_splits = [self._start_time]

    def split_feature(self):
        if self._start_time is None:
            return

        time = perf_counter()
        elapsed_time = time - self._feature_splits[-1]

        self._feature_splits.append(time)
        self._period_splits = [time]

        return elapsed_time

    def split_period(self):
        if self._start_time is None:
            return

        time = perf_counter()
        elapsed_time = time - self._period_splits[-1]

        self._period_splits.append(time)

        return elapsed_time

    def stop(self):
        if self._start_time is None:
            return

        self.split_period()

        elapsed_time = perf_counter() - self._start_time
        feature_timings = self._feature_timings()

        stats = {
            "min": min(feature_timings),
            "max": max(feature_timings),
            "mean": mean(feature_timings),
            "stdev": stdev(feature_timings)
        }

        self._start_time = None
        self._feature_splits = None
        self._period_splits = None

        return {
            "elapsed_time": elapsed_time,
            "stats": stats,
            "feature_timings": feature_timings
        }

    def _feature_timings(self):
        return [t - s for s, t in zip(self._feature_splits, self._feature_splits[1:])]

from time import perf_counter


class Timer:

    def __init__(self):
        self._start_time = None
        self._feature_splits = None
        self._period_splits = None

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

        elapsed_time = perf_counter() - self._start_time
        self._start_time = None
        self._feature_splits = None
        self._period_splits = None

        return elapsed_time

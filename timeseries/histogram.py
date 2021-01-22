from datetime import timedelta

import matplotlib as mpl
import matplotlib.pyplot as pl


def create_histogram(result_path, feature_timings):
    pl.ioff()

    def seconds_to_string(x, pos):
        delta = str(timedelta(seconds=x))
        split = delta.split(".")
        if len(split) > 1:
            split[-1] = split[-1].rstrip("0")
        return ".".join(split)

    formatter = mpl.ticker.FuncFormatter(seconds_to_string)
    pl.subplots()[1].xaxis.set_major_formatter(formatter)

    pl.hist(feature_timings)

    pl.xlabel("Timings")
    pl.ylabel("Frequency")

    pl.savefig(f"{result_path}.png")

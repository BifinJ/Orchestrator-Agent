import numpy as np

ROLLING_WINDOW = 5
ZSCORE_THRESHOLD = 2.5

def rolling_zscore(values):
    arr = np.array(values, dtype=float)
    z = np.full(len(arr), np.nan)
    for i in range(len(arr)):
        if i < ROLLING_WINDOW:
            continue
        window = arr[i-ROLLING_WINDOW:i]
        mean = np.mean(window)
        std = np.std(window)
        if std > 0:
            z[i] = (arr[i] - mean) / std
    return z

import numpy as np

def normalize_scores(judge_scores):
    mean = np.mean(judge_scores)
    std = np.std(judge_scores)
    if std == 0:
        std = 1

    normalized = []
    for score in judge_scores:
        z = (score - mean) / std
        normalized.append(50 + 10 * z)

    return normalized

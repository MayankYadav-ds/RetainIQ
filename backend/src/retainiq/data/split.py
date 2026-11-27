from collections import defaultdict

from .contract import SEED, digest, encoded
from .quality import Row, group_key


def partitions(rows: list[Row]) -> set[bytes]:
    """Greedy grouped allocation towards both class quotas with seeded tie-breaking."""
    groups: dict[bytes, list[int]] = defaultdict(lambda: [0, 0])
    total = [0, 0]
    for row in rows:
        label = int(row["churn"])
        groups[group_key(row)][label] += 1
        total[label] += 1
    desired = [n / 5 for n in total]
    current = [0, 0]
    chosen = set()

    def loss(pair: list[int]) -> float:
        return sum(((x - y) / max(y, 1)) ** 2 for x, y in zip(pair, desired, strict=True))

    for key in sorted(groups, key=lambda k: (-sum(groups[k]), digest(encoded(SEED) + k))):
        proposed = [current[i] + groups[key][i] for i in (0, 1)]
        if loss(proposed) < loss(current):
            chosen.add(key)
            current = proposed
    if not chosen or len(chosen) == len(groups):
        raise ValueError("group_split_infeasible")
    return chosen

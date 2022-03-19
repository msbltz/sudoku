from typing import Tuple


# An integer in [0, 8].
Index = int
# Location (i, j) of a cell.
Cell = Tuple[int, int]
# A number num at cell (i, j).
Node = Tuple[Cell, int]
# Cell (i, j) must be / cannot be a number num.
Event = Tuple[Cell, int, bool]

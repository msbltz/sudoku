"""
@author: yuan.shao
"""
from typing import Any, Dict, List, Set, Union

from constants import (
    ALL_NUMBERS_SET,
    ALL_NUMBERS_STRING_SET,
    COL_CELLS,
    COLORS,
    ENDC,
    POS_OR_NEG_COLOR,
    POS_OR_NEG_COLOR_WORDS,
    ROW_CELLS,
    SQR_CELLS,
)
from type_aliases import Cell, Event, Index, Node


def board_number_to_string(num: int) -> str:
    return str(num) if num > 0 else '.'


def cell_dist(cell1: Cell, cell2: Cell) -> int:
    di = abs(cell1[0] - cell2[0])
    dj = abs(cell1[1] - cell2[1])
    return 10 * max(di, dj) + min(di, dj)


def cell_intersect(cell1: Cell, cell2: Cell) -> bool:
    """
    Return whether two cells are in the same row, column or square.

    Parameters
    ----------
    cell1 : (int, int)
        Position of the first cell.
    cell2 : (int, int)
        Position of the second cell.

    Returns
    -------
    bool
        Whether the two cells intersect.

    """
    return (
        cell1[0] == cell2[0]
        or cell1[1] == cell2[1]
        or square_index_of(cell1) == square_index_of(cell2)
    )


def cell_to_string(cell: Cell) -> str:
    return f'({cell[0] + 1}, {cell[1] + 1})'


def cells_affected_by(cell: Cell) -> Set[Cell]:
    return set(
        row_of_cell(cell) + column_of_cell(cell) + square_of_cell(cell)
    ).difference({cell})


def char_or_int_to_number(c: Union[str, int]) -> int:
    return int(c) if c in ALL_NUMBERS_SET or c in ALL_NUMBERS_STRING_SET else 0


def char_to_number(c: str) -> int:
    return int(c) if c in ALL_NUMBERS_STRING_SET else 0


def color_to_words(positive: bool) -> str:
    return colored_string(
        POS_OR_NEG_COLOR_WORDS[positive], POS_OR_NEG_COLOR[positive],
    )


def colored_string(string: str, color: str) -> str:
    if color not in COLORS:
        return string
    return COLORS[color] + string + ENDC


def column_of_cell(cell: Cell) -> List[Cell]:
    return COL_CELLS[cell[1]]


def event_chain_to_string(chain: List[Set[Event]]) -> str:
    return ' ==> '.join([events_to_string(events) for events in chain])


def event_to_string(event: Event) -> str:
    cell, num, positive = event
    if not num:
        # Impossible event.
        return f'{cell_to_string(cell)}格不剩任何候选数，矛盾'
    v = '必须' if positive else '不能'
    return f'{cell_to_string(cell)}格{v}是{num}'


def events_to_string(events: Set[Event]) -> str:
    return '，'.join([event_to_string(event) for event in sorted(events)])


def index_to_string(idx: Index) -> str:
    return str(idx + 1)


def inverse_map(multi_map: Dict[Any, Set[Any]]) -> Dict[Any, Set[Any]]:
    res = dict()
    for x, y_set in multi_map.items():
        for y in y_set:
            if y not in res:
                res[y] = set()
            res[y].add(x)
    return res


def node_dist(node1: Node, node2: Node) -> int:
    return cell_dist(node1[0], node2[0])


def node_to_cell_string(node: Node) -> str:
    return cell_to_string(node[0])


def node_to_equal_string(node: Node) -> str:
    return f'{cell_to_string(node[0])} = {node[1]}'


def node_to_words(node: Node) -> str:
    return f'{cell_to_string(node[0])}格的候选数{node[1]}'


def only_element_in_set(s: Set[Any]) -> Any:
    return next(iter(s))


def plural(s: Union[List, Set]) -> str:
    return '们' if len(s) > 1 else ''


def row_of_cell(cell: Cell) -> List[Cell]:
    return ROW_CELLS[cell[0]]


def set_of_cells_to_string(cell_set: Set[Cell]) -> str:
    return ''.join([cell_to_string(cell) for cell in sorted(cell_set)])


def set_of_indices_to_string(idx_set: Set[Index]) -> str:
    return ''.join([index_to_string(idx) for idx in sorted(idx_set)])


def set_of_nodes_to_words(node_set: Set[Node]) -> str:
    num_set = {num for _, num in node_set}
    if len(num_set) > 1:
        m = dict()
        for cell, num in node_set:
            if cell not in m:
                m[cell] = set()
            m[cell].add(num)
        s = [
            f'{cell_to_string(cell)}格的候选数{set_of_numbers_to_string(m[cell])}'
            for cell in sorted(m.keys())
        ]
        return '和'.join(['、'.join(s[:-1]), s[-1]]) if len(s) > 1 else s[0]
    else:
        cell_set = {cell for cell, _ in node_set}
        return (
            f'{set_of_cells_to_string(cell_set)}格的候选数'
            f'{only_element_in_set(num_set)}'
        )


def set_of_numbers_to_string(s: Set[int]) -> str:
    return ''.join([str(n) for n in sorted(s)])


def square_index_of(cell: Cell) -> Index:
    return 3 * (cell[0] // 3) + cell[1] // 3


def square_of_cell(cell: Cell) -> List[Cell]:
    return SQR_CELLS[square_index_of(cell)]

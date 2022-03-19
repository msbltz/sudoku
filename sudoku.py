"""
@author: yuan.shao
"""
from __future__ import annotations

import math
from copy import deepcopy
from typing import Any, Callable, Dict, List, Set, Tuple, Union

from constants import (
    ALL_CELLS,
    ALL_NUMBERS,
    ALL_NUMBERS_SET,
    ALL_NUMBERS_STRING_SET,
    COL_CELLS,
    DEFAULT_MAX_CHAIN_LENGTH,
    DEFAULT_MAX_DERIVATION_DEPTH,
    NEGATIVE_COLOR,
    NUM_TO_WORD,
    POSITIVE_COLOR,
    ROW_CELLS,
    SOLVED_COLOR,
    SQR_CELLS,
    UNSOLVED_COLOR,
)
from type_aliases import Cell, Event, Index, Node
from utils import (
    board_number_to_string,
    cell_intersect,
    cell_to_string,
    cells_affected_by,
    char_or_int_to_number,
    char_to_number,
    color_to_words,
    colored_string,
    event_to_string,
    event_chain_to_string,
    index_to_string,
    inverse_map,
    node_dist,
    node_to_cell_string,
    node_to_equal_string,
    node_to_words,
    only_element_in_set,
    plural,
    POS_OR_NEG_COLOR,
    set_of_cells_to_string,
    set_of_indices_to_string,
    set_of_nodes_to_words,
    set_of_numbers_to_string,
    square_index_of,
)


class Sudoku:
    def __init__(self, board: List[List[int]]) -> None:
        self.board = deepcopy(board)
        self.possibility = {
            cell: deepcopy(ALL_NUMBERS_SET) for cell in ALL_CELLS
        }
        for cell in ALL_CELLS:
            if self.is_filled(cell):
                self.exclude_possibilities_given_known_cell(cell)

        self.sqr_cell_to_num, self.sqr_num_to_cell = [], []
        self.row_cell_to_num, self.row_num_to_cell = [], []
        self.col_cell_to_num, self.col_num_to_cell = [], []
        self.update_cell_num_maps()
        self.two_poss_cells, self.three_poss_cells = [], []
        self.update_two_and_three_poss_cells()

        self.link_graphs_per_num = dict()
        self.all_num_strong_links, self.all_num_weak_links = dict(), dict()
    
    @classmethod
    def from_matrix(cls, matrix: List[List[Union[int, str]]]) -> Sudoku:
        """
        Create Sudoku object from a matrix of integers or strings.
        
        Parameters
        ----------
        matrix : list of list of int or string
            9x9 list representation of a Sudoku board. Non-1-to-9 numbers or
            strings will be interpreted as unknown cells.
        
        Returns
        -------
        Sudoku
        
        """
        if len(matrix) != 9:
            raise ValueError(
                f'盘面矩阵输入的行数必须等于9。实际输入的矩阵行数是{len(matrix)}。'
            )
        for i, row in enumerate(matrix):
            if len(row) != 9:
                raise ValueError(
                    f'盘面矩阵输入每一行的列数都必须等于9。实际输入的'
                    f'第{index_to_string(i)}行的列数是{len(row)}。'
                )
        board = [[char_or_int_to_number(c) for c in row] for row in matrix]
        return cls(board)
    
    @classmethod
    def from_string(cls, string: str) -> Sudoku:
        """
        Create Sudoku object from a string of digits.
        
        Parameters
        ----------
        string : string
            81-character string representation of a Sudoku board. Non-digit
            characters will be interpreted as unknown cells.
        
        Returns
        -------
        Sudoku
        
        """
        if len(string) != 81:
            raise ValueError(
                f'盘面字符串输入的长度必须等于81。实际输入的字符串长度是{len(string)}。'
            )
        numbers = [char_to_number(c) for c in string]
        board = [numbers[(9 * i):(9 * i + 9)] for i in range(9)]
        return cls(board)
    
    def board_to_int_matrix(self) -> List[List[int]]:
        return deepcopy(self.board)
    
    def board_to_string(self) -> str:
        return ''.join([''.join([str(n) for n in row]) for row in self.board])

    def update_cell_num_maps(self) -> None:
        # Update cell to numbers and number to cells maps for each square, row
        # and column.
        self.sqr_cell_to_num = [
            {cell: self.get_possibility(cell) for cell in sqr}
            for sqr in SQR_CELLS
        ]
        self.sqr_num_to_cell = [inverse_map(m) for m in self.sqr_cell_to_num]
        self.row_cell_to_num = [
            {cell: self.get_possibility(cell) for cell in row}
            for row in ROW_CELLS
        ]
        self.row_num_to_cell = [inverse_map(m) for m in self.row_cell_to_num]
        self.col_cell_to_num = [
            {cell: self.get_possibility(cell) for cell in col}
            for col in COL_CELLS
        ]
        self.col_num_to_cell = [inverse_map(m) for m in self.col_cell_to_num]

    def update_two_and_three_poss_cells(self) -> None:
        self.two_poss_cells = [
            cell for cell in ALL_CELLS if len(self.get_possibility(cell)) == 2
        ]
        self.three_poss_cells = [
            cell for cell in ALL_CELLS if len(self.get_possibility(cell)) == 3
        ]

    def update_link_graphs(self) -> None:
        self.link_graphs_per_num = {
            num: self.generate_link_graphs_for_number(num)
            for num in ALL_NUMBERS
        }
        self.all_num_strong_links, self.all_num_weak_links = (
            self.generate_link_graphs_for_all_numbers(self.link_graphs_per_num)
        )

    def logical_deduction(
        self,
        print_details: bool = False,
        max_chain_length: int = DEFAULT_MAX_CHAIN_LENGTH,
        max_derivation_depth: int = DEFAULT_MAX_DERIVATION_DEPTH,
        max_difficulty_level: int = 5,
    ) -> Tuple[bool, Union[Cell, None], int]:
        """
        Fill in numbers using logical deduction.
        
        Parameters
        ----------
        print_details : bool
            Whether to print out detail logics.
        max_chain_length : int
            The maximum search length for strong-weak chains.
        max_derivation_depth : int
            The maximum search depth for two-way forks.
        max_difficulty_level : int
            The maximum difficulty level of the techniques to use, from 1 to 5.
        
        Returns
        -------
        bool
            Whether the sudoku is impossible due to a contradiction.
        tuple (int, int)
            Position of the impossible cell. None if not impossible.
        int
            Level of the hardest technique used, between 1 and 5. Return 0 if
            the sudoku is impossible.
        
        """
        difficulty_level = 0
        while True:
            if print_details:
                print()
                self.show_possibility()
                print()
            imp, cell = self.is_impossible()
            if imp:
                if print_details:
                    print(f'矛盾！{cell_to_string(cell)}格不剩任何候选数！')
                    print()
                return True, cell, 0
            if self.is_solved():
                if print_details:
                    print('求解成功！')
                    print()
                return False, None, difficulty_level
            
            if max_difficulty_level >= 1:
                self.update_cell_num_maps()
                new_fills = self.check_only_choice(print_details)
                if new_fills:
                    self.execute_fills(new_fills)
                    difficulty_level = max(1, difficulty_level)
                    continue
                new_erases = self.check_only_one_row_col_sqr(print_details)
                if new_erases:
                    self.execute_erases(new_erases)
                    difficulty_level = max(1, difficulty_level)
                    continue

            if max_difficulty_level >= 2:
                new_erases = self.check_full_subsets(print_details)
                if new_erases:
                    self.execute_erases(new_erases)
                    difficulty_level = max(2, difficulty_level)
                    continue
                new_erases = self.check_fish_structures(print_details)
                if new_erases:
                    self.execute_erases(new_erases)
                    difficulty_level = max(3, difficulty_level)
                    continue

            if max_difficulty_level >= 3:
                self.update_two_and_three_poss_cells()
                new_erases = self.check_xy_wings(print_details)
                if new_erases:
                    self.execute_erases(new_erases)
                    difficulty_level = max(3, difficulty_level)
                    continue
                new_erases = self.check_xyz_wings(print_details)
                if new_erases:
                    self.execute_erases(new_erases)
                    difficulty_level = max(3, difficulty_level)
                    continue

            if max_difficulty_level >= 4:
                self.update_link_graphs()
                new_erases = self.check_coloring_strong_links(print_details)
                if new_erases:
                    self.execute_erases(new_erases)
                    difficulty_level = max(4, difficulty_level)
                    continue
                new_fills, new_erases = self.check_strong_weak_chains(
                    print_details, max_chain_length,
                )
                if new_fills or new_erases:
                    self.execute_fills(new_fills)
                    self.execute_erases(new_erases)
                    difficulty_level = max(4, difficulty_level)
                    continue

            if max_difficulty_level >= 5:
                new_fills, new_erases = self.check_two_way_forks(
                    print_details, max_derivation_depth,
                )
                if new_fills or new_erases:
                    self.execute_fills(new_fills)
                    self.execute_erases(new_erases)
                    difficulty_level = max(5, difficulty_level)
                    continue
                new_fills = self.check_strong_link_clusters(print_details)
                if new_fills:
                    self.execute_fills(new_fills)
                    difficulty_level = max(5, difficulty_level)
                    continue
            
            break
        return False, None, 5

    def check_only_choice(self, print_details: bool) -> Set[Node]:
        new_fills = set()
        # 1.1. Check cells with only one possibility.
        for cell in ALL_CELLS:
            if (
                    len(self.get_possibility(cell)) == 1
                    and self.is_unfilled(cell)
            ):
                num = only_element_in_set(self.get_possibility(cell))
                if print_details and (cell, num) not in new_fills:
                    print(
                        f'在{cell_to_string(cell)}格填入{num}：此格仅剩的唯一候选数。'
                    )
                new_fills.add((cell, num))
        # 1.2. Examine each square for new fills.
        for s, num_to_cell in enumerate(self.sqr_num_to_cell):
            for num, cell in self.numbers_only_occurring_once(num_to_cell):
                if print_details and (cell, num) not in new_fills:
                    print(
                        f'在{cell_to_string(cell)}格填入{num}：'
                        f'第{index_to_string(s)}宫内数字{num}的唯一可能位置。'
                    )
                new_fills.add((cell, num))
        # 1.3. Examine each row for new fills.
        for i, num_to_cell in enumerate(self.row_num_to_cell):
            for num, cell in self.numbers_only_occurring_once(num_to_cell):
                if print_details and (cell, num) not in new_fills:
                    print(
                        f'在{cell_to_string(cell)}格填入{num}：'
                        f'第{index_to_string(i)}行内数字{num}的唯一可能位置。'
                    )
                new_fills.add((cell, num))
        # 1.4. Examine each column for new fills.
        for j, num_to_cell in enumerate(self.col_num_to_cell):
            for num, cell in self.numbers_only_occurring_once(num_to_cell):
                if print_details and (cell, num) not in new_fills:
                    print(
                        f'在{cell_to_string(cell)}格填入{num}：'
                        f'第{index_to_string(j)}列内数字{num}的唯一可能位置。'
                    )
                new_fills.add((cell, num))
        return new_fills

    def numbers_only_occurring_once(
        self, number_to_cells: Dict[int, Set[Cell]],
    ) -> List[Tuple[int, Cell]]:
        """
        Find the unfilled numbers that only appear once in the number to cells
        map.
        
        Parameters
        ----------
        number_to_cells : dict from int to set of tuples (int, int)
            A map from numbers to the set of possible cell positions.
        
        Returns
        -------
        list of tuples (num, cell)
            The number num only appears once, and it's at the unfilled cell.
        
        """
        res = []
        for num, cell_set in number_to_cells.items():
            if len(cell_set) == 1:
                cell = only_element_in_set(cell_set)
                if self.is_unfilled(cell):
                    res.append((num, cell))
        return res

    def check_only_one_row_col_sqr(self, print_details: bool) -> Set[Node]:
        new_erases = set()
        # 2.1. Examine each square for new erases from numbers only occurring
        # in one row or one column.
        for s, num_to_cell in enumerate(self.sqr_num_to_cell):
            rows, cols = self.numbers_only_occurring_in_row_or_column(
                num_to_cell
            )
            for num, i, j_set in rows:
                t = set()
                for cell in ROW_CELLS[i]:
                    if (
                        cell[1] not in j_set
                        and num in self.get_possibility(cell)
                    ):
                        new_erases.add((cell, num))
                        t.add(cell[1])
                if print_details and t:
                    print(
                        f'第{index_to_string(s)}宫内，'
                        f'数字{num}只可能在第{index_to_string(i)}行出现。'
                        f'在此行其余的第{set_of_indices_to_string(t)}列删去候选数{num}。'
                    )
            for num, i_set, j in cols:
                t = set()
                for cell in COL_CELLS[j]:
                    if (
                        cell[0] not in i_set
                        and num in self.get_possibility(cell)
                    ):
                        new_erases.add((cell, num))
                        t.add(cell[0])
                if print_details and t:
                    print(
                        f'第{index_to_string(s)}宫内，'
                        f'数字{num}只可能在第{index_to_string(j)}列出现。'
                        f'在此列其余的第{set_of_indices_to_string(t)}行删去候选数{num}。'
                    )
        if new_erases:
            return new_erases
        # 2.2. Examine each row for new erases from numbers only occurring in
        # one square.
        for i, num_to_cell in enumerate(self.row_num_to_cell):
            for num, s in self.numbers_only_occurring_in_square(num_to_cell):
                t = set()
                for cell in SQR_CELLS[s]:
                    if cell[0] != i and num in self.get_possibility(cell):
                        new_erases.add((cell, num))
                        t.add(cell)
                if print_details and t:
                    print(
                        f'第{index_to_string(i)}行内，'
                        f'数字{num}只可能在第{index_to_string(s)}宫出现。'
                        f'在此宫其余的{set_of_cells_to_string(t)}格删去候选数{num}。'
                    )
        if new_erases:
            return new_erases
        # 2.3. Examine each column for new erases from numbers only occurring
        # in one square.
        for j, num_to_cell in enumerate(self.col_num_to_cell):
            for num, s in self.numbers_only_occurring_in_square(num_to_cell):
                t = set()
                for cell in SQR_CELLS[s]:
                    if cell[1] != j and num in self.get_possibility(cell):
                        new_erases.add((cell, num))
                        t.add(cell)
                if print_details and t:
                    print(
                        f'第{index_to_string(j)}列内，'
                        f'数字{num}只可能在第{index_to_string(s)}宫出现。'
                        f'在此宫其余的{set_of_cells_to_string(t)}格删去候选数{num}。'
                    )
        return new_erases

    @staticmethod
    def numbers_only_occurring_in_row_or_column(
        number_to_cells: Dict[int, Set[Cell]]
    ) -> Tuple[
        List[Tuple[int, Index, Set[Index]]],
        List[Tuple[int, Set[Index], Index]],
    ]:
        """
        Find the numbers which appear more than once in the number to cells map
        but the cell positions are all in the same row or column.
        
        Parameters
        ----------
        number_to_cells : dict from int to set of tuples (int, int)
            A map from numbers to the set of possible cell positions.
        
        Returns
        -------
        list of tuples (num, i, set of j)
            The number num only appears in row i at columns j in the set.
        list of tuples (num, set of i, j)
            The number num only appears in column j at rows i in the set.
        
        """
        rows = []
        cols = []
        for num, cell_set in number_to_cells.items():
            if len(cell_set) <= 1:
                continue
            r = set(cell[0] for cell in cell_set)
            c = set(cell[1] for cell in cell_set)
            if len(r) == 1:
                rows.append((num, only_element_in_set(r), c))
                continue
            if len(c) == 1:
                cols.append((num, r, only_element_in_set(c)))
        return rows, cols

    @staticmethod
    def numbers_only_occurring_in_square(
        number_to_cells: Dict[int, Set[Cell]]
    ) -> List[Tuple[int, Index]]:
        """
        Find the numbers which appear more than once in the number to cells map
        but the cell positions are all in the same square.
        
        Parameters
        ----------
        number_to_cells : dict from int to set of tuples (int, int)
            A map from numbers to the set of possible cell positions.
        
        Returns
        -------
        list of tuples (num, s)
            The number num only appears in square s.
        
        """
        res = []
        for num, cell_set in number_to_cells.items():
            if len(cell_set) <= 1:
                continue
            s_set = set(square_index_of(cell) for cell in cell_set)
            if len(s_set) == 1:
                res.append((num, only_element_in_set(s_set)))
        return res

    def check_full_subsets(self, print_details: bool) -> Set[Node]:
        new_erases = set()
        # 3.1. Examine each square for new erases from full subsets: x numbers
        # occupy x cells.
        for s, cell_to_num in enumerate(self.sqr_cell_to_num):
            for cell_set, num_set in self.find_full_subsets(
                cell_to_num, math.ceil(len(cell_to_num) / 2),
            ):
                t = set()
                for cell in SQR_CELLS[s]:
                    if cell in cell_set:
                        continue
                    for num in num_set.intersection(
                        self.get_possibility(cell)
                    ):
                        new_erases.add((cell, num))
                        t.add(cell)
                if print_details and t:
                    print(
                        f'第{index_to_string(s)}宫内，'
                        f'{set_of_numbers_to_string(num_set)}'
                        f'这{NUM_TO_WORD[len(num_set)]}个数字'
                        f'占满了{set_of_cells_to_string(cell_set)}'
                        f'这{NUM_TO_WORD[len(cell_set)]}个格。'
                        f'在此宫其余的{set_of_cells_to_string(t)}格'
                        f'删去候选数{set_of_numbers_to_string(num_set)}。'
                    )
        if new_erases:
            return new_erases
        # 3.2. Examine each row for new erases from full subsets: x numbers
        # occupy x cells.
        for i, cell_to_num in enumerate(self.row_cell_to_num):
            for cell_set, num_set in self.find_full_subsets(
                cell_to_num, math.ceil(len(cell_to_num) / 2),
            ):
                t = set()
                for cell in ROW_CELLS[i]:
                    if cell in cell_set:
                        continue
                    for num in num_set.intersection(
                        self.get_possibility(cell)
                    ):
                        new_erases.add((cell, num))
                        t.add(cell[1])
                if print_details and t:
                    col_set = set(cell[1] for cell in cell_set)
                    print(
                        f'第{index_to_string(i)}行内，'
                        f'{set_of_numbers_to_string(num_set)}'
                        f'这{NUM_TO_WORD[len(num_set)]}个数字'
                        f'占满了第{set_of_indices_to_string(col_set)}'
                        f'这{NUM_TO_WORD[len(cell_set)]}列。'
                        f'在此行其余的第{set_of_indices_to_string(t)}列'
                        f'删去候选数{set_of_numbers_to_string(num_set)}。'
                    )
        if new_erases:
            return new_erases
        # 3.3. Examine each column for new erases from full subsets: x numbers
        # occupy x cells.
        for j, cell_to_num in enumerate(self.col_cell_to_num):
            for cell_set, num_set in self.find_full_subsets(
                cell_to_num, math.ceil(len(cell_to_num) / 2),
            ):
                t = set()
                for cell in COL_CELLS[j]:
                    if cell in cell_set:
                        continue
                    for num in num_set.intersection(
                        self.get_possibility(cell)
                    ):
                        new_erases.add((cell, num))
                        t.add(cell[0])
                if print_details and t:
                    row_set = set(cell[0] for cell in cell_set)
                    print(
                        f'第{index_to_string(j)}列内，'
                        f'{set_of_numbers_to_string(num_set)}'
                        f'这{NUM_TO_WORD[len(num_set)]}个数字'
                        f'占满了第{set_of_indices_to_string(row_set)}'
                        f'这{NUM_TO_WORD[len(cell_set)]}行。'
                        f'在此列其余的第{set_of_indices_to_string(t)}行'
                        f'删去候选数{set_of_numbers_to_string(num_set)}。'
                    )
        if new_erases:
            return new_erases
        # 3.4. Examine each square for new erases from full subsets: x numbers
        # can only go into x cells.
        for s, num_to_cell in enumerate(self.sqr_num_to_cell):
            for num_set, cell_set in self.find_full_subsets(
                num_to_cell, math.ceil(len(num_to_cell) / 2),
            ):
                erase = False
                for cell in cell_set:
                    for num in self.get_possibility(cell).difference(num_set):
                        new_erases.add((cell, num))
                        erase = True
                if print_details and erase:
                    print(
                        f'第{index_to_string(s)}宫内，'
                        f'{set_of_numbers_to_string(num_set)}'
                        f'这{NUM_TO_WORD[len(num_set)]}个数字'
                        f'只能出现在{set_of_cells_to_string(cell_set)}'
                        f'这{NUM_TO_WORD[len(cell_set)]}个格。'
                        f'在这{NUM_TO_WORD[len(cell_set)]}个格'
                        f'删去{set_of_numbers_to_string(num_set)}之外的所有候选数。'
                    )
        if new_erases:
            return new_erases
        # 3.5. Examine each row for new erases from full subsets: x numbers can
        # only go into x cells.
        for i, num_to_cell in enumerate(self.row_num_to_cell):
            for num_set, cell_set in self.find_full_subsets(
                num_to_cell, math.ceil(len(num_to_cell) / 2),
            ):
                erase = False
                for cell in cell_set:
                    for num in self.get_possibility(cell).difference(num_set):
                        new_erases.add((cell, num))
                        erase = True
                if print_details and erase:
                    col_set = set(cell[1] for cell in cell_set)
                    print(
                        f'第{index_to_string(i)}行内，'
                        f'{set_of_numbers_to_string(num_set)}'
                        f'这{NUM_TO_WORD[len(num_set)]}个数字'
                        f'只能出现在第{set_of_indices_to_string(col_set)}'
                        f'这{NUM_TO_WORD[len(cell_set)]}列。'
                        f'在这{NUM_TO_WORD[len(cell_set)]}个格'
                        f'删去{set_of_numbers_to_string(num_set)}之外的所有候选数。'
                    )
        if new_erases:
            return new_erases
        # 3.6. Examine each column for new erases from full subsets: x numbers
        # can only go into x cells.
        for j, num_to_cell in enumerate(self.col_num_to_cell):
            for num_set, cell_set in self.find_full_subsets(
                num_to_cell, math.ceil(len(num_to_cell) / 2),
            ):
                erase = False
                for cell in cell_set:
                    for num in self.get_possibility(cell).difference(num_set):
                        new_erases.add((cell, num))
                        erase = True
                if print_details and erase:
                    row_set = set(cell[0] for cell in cell_set)
                    print(
                        f'第{index_to_string(j)}列内，'
                        f'{set_of_numbers_to_string(num_set)}'
                        f'这{NUM_TO_WORD[len(num_set)]}个数字'
                        f'只能出现在第{set_of_indices_to_string(row_set)}'
                        f'这{NUM_TO_WORD[len(cell_set)]}行。'
                        f'在这{NUM_TO_WORD[len(cell_set)]}个格'
                        f'删去{set_of_numbers_to_string(num_set)}之外的所有候选数。'
                    )
        return new_erases

    def check_fish_structures(self, print_details: bool) -> Set[Node]:
        new_erases = set()
        # 4.1. Find row fish structures for each number.
        for num in ALL_NUMBERS:
            row_to_col = {
                i: set(cell[1] for cell in num_to_cell[num])
                for i, num_to_cell in enumerate(self.row_num_to_cell)
                if num in num_to_cell
            }
            for row_set, col_set in self.find_full_subsets(
                row_to_col, math.ceil(len(row_to_col) / 2),
            ):
                erase_cells = set()
                for j in col_set:
                    for cell in COL_CELLS[j]:
                        if (
                            cell[0] not in row_set
                            and num in self.get_possibility(cell)
                        ):
                            new_erases.add((cell, num))
                            erase_cells.add(cell)
                if print_details and erase_cells:
                    print(
                        f'第{set_of_indices_to_string(row_set)}'
                        f'这{NUM_TO_WORD[len(row_set)]}行内，'
                        f'数字{num}只可能出现在'
                        f'第{set_of_indices_to_string(col_set)}'
                        f'这{NUM_TO_WORD[len(col_set)]}列。'
                        f'在这{NUM_TO_WORD[len(col_set)]}列'
                        f'其余的{set_of_cells_to_string(erase_cells)}格'
                        f'删去候选数{num}。'
                    )
        if new_erases:
            return new_erases
        # 4.2. Find column fish structures for each number.
        for num in ALL_NUMBERS:
            col_to_row = {
                j: set(cell[0] for cell in num_to_cell[num])
                for j, num_to_cell in enumerate(self.col_num_to_cell)
                if num in num_to_cell
            }
            for col_set, row_set in self.find_full_subsets(
                col_to_row, math.ceil(len(col_to_row) / 2),
            ):
                erase_cells = set()
                for i in row_set:
                    for cell in ROW_CELLS[i]:
                        if (
                            cell[1] not in col_set
                            and num in self.get_possibility(cell)
                        ):
                            new_erases.add((cell, num))
                            erase_cells.add(cell)
                if print_details and erase_cells:
                    print(
                        f'第{set_of_indices_to_string(col_set)}'
                        f'这{NUM_TO_WORD[len(col_set)]}列内，'
                        f'数字{num}只可能出现在'
                        f'第{set_of_indices_to_string(row_set)}'
                        f'这{NUM_TO_WORD[len(row_set)]}行。'
                        f'在这{NUM_TO_WORD[len(row_set)]}行'
                        f'其余的{set_of_cells_to_string(erase_cells)}格'
                        f'删去候选数{num}。'
                    )
        return new_erases

    @staticmethod
    def find_full_subsets(
        multi_map: Dict[Any, Set[Any]], max_size: int = 5,
    ) -> List[Tuple[Set[Any], Set[Any]]]:
        """
        Find the smallest full subsets of size between 2 and max_size (both
        ends inclusive) from a many-to-many map multi_map. A full subset is a
        subset of the key set whose image set under multi_map has the same
        cardinality as itself.
        
        Parameters
        ----------
        multi_map : map from type X to set of type Y
            A many-to-many map.
        max_size : int
            The maximum size of full subsets to detect. Should be one of 2, 3,
            4 or 5.
        
        Returns
        -------
        list of tuples (set, set)
            List of the smallest full subsets and their images under multi_map.
        
        """
        res = []
        mp = {k: v for k, v in multi_map.items() if len(v) > 1}
        ks = sorted(mp.keys())
        n = len(mp)
        ml = min(n - 1, max_size)
        for i1 in range(n):
            t1 = mp[ks[i1]]
            for i2 in range(i1 + 1, n):
                t2 = t1.union(mp[ks[i2]])
                if len(t2) == 2:
                    res.append(({ks[i1], ks[i2]}, t2))
                    ml = 2
                if ml <= 2:
                    continue
                for i3 in range(i2 + 1, n):
                    t3 = t2.union(mp[ks[i3]])
                    if len(t3) == 3:
                        res.append(({ks[i1], ks[i2], ks[i3]}, t3))
                        ml = 3
                    if ml <= 3:
                        continue
                    for i4 in range(i3 + 1, n):
                        t4 = t3.union(mp[ks[i4]])
                        if len(t4) == 4:
                            res.append(({ks[i1], ks[i2], ks[i3], ks[i4]}, t4))
                            ml = 4
                        if ml <= 4:
                            continue
                        for i5 in range(i4 + 1, n):
                            t5 = t4.union(mp[ks[i5]])
                            if len(t5) == 5:
                                res.append((
                                    {ks[i1], ks[i2], ks[i3], ks[i4], ks[i5]},
                                    t5,
                                ))
                                ml = 5
        return [(s, t) for s, t in res if len(s) == ml]

    def check_xy_wings(self, print_details: bool) -> Set[Node]:
        new_erases = set()
        # 5. Examine cells with exactly two possibilities for new erases from
        # xy wings.
        for center in self.two_poss_cells:
            center_set = self.get_possibility(center)
            wing_candidates = [
                cell for cell in self.two_poss_cells
                if (
                    cell_intersect(center, cell)
                    and len(center_set.union(self.get_possibility(cell))) == 3
                )
            ]
            for a in range(len(wing_candidates)):
                wing1 = wing_candidates[a]
                wing1_set = self.get_possibility(wing1)
                for b in range(a + 1, len(wing_candidates)):
                    wing2 = wing_candidates[b]
                    wing2_set = self.get_possibility(wing2)
                    if (
                        cell_intersect(wing1, wing2)
                        or len(wing1_set.union(wing2_set)) != 3
                        or len(
                            center_set.union(wing1_set).union(wing2_set)
                        ) != 3
                    ):
                        continue
                    num = only_element_in_set(
                        wing1_set.intersection(wing2_set)
                    )
                    erase_cells = set()
                    for cell in ALL_CELLS:
                        if (
                            cell_intersect(cell, wing1)
                            and cell_intersect(cell, wing2)
                            and num in self.get_possibility(cell)
                        ):
                            new_erases.add((cell, num))
                            erase_cells.add(cell)
                    if print_details and erase_cells:
                        print(
                            f'{cell_to_string(wing1)}格的候选数'
                            f'{set_of_numbers_to_string(wing1_set)}、'
                            f'{cell_to_string(center)}格的候选数'
                            f'{set_of_numbers_to_string(center_set)}'
                            f'和{cell_to_string(wing2)}格的候选数'
                            f'{set_of_numbers_to_string(wing2_set)}'
                            f'形成双分支匹配，头尾两格当中必有一格等于{num}。'
                            f'在处于这两格共同作用域中的'
                            f'{set_of_cells_to_string(erase_cells)}格'
                            f'删去候选数{num}。'
                        )
        return new_erases

    def check_xyz_wings(self, print_details: bool) -> Set[Node]:
        new_erases = set()
        # 6. Examine cells with exactly three possibilities for new erases
        # from xyz wings.
        for center in self.three_poss_cells:
            center_set = self.get_possibility(center)
            wing_candidates = [
                cell for cell in self.two_poss_cells
                if (
                    cell_intersect(center, cell)
                    and self.get_possibility(cell).issubset(center_set)
                )
            ]
            for a in range(len(wing_candidates)):
                wing1 = wing_candidates[a]
                wing1_set = self.get_possibility(wing1)
                for b in range(a + 1, len(wing_candidates)):
                    wing2 = wing_candidates[b]
                    wing2_set = self.get_possibility(wing2)
                    if cell_intersect(wing1, wing2) or wing1_set == wing2_set:
                        continue
                    num = only_element_in_set(
                        wing1_set.intersection(wing2_set)
                    )
                    erase_cells = set()
                    for cell in ALL_CELLS:
                        if (
                            cell != center
                            and cell_intersect(cell, center)
                            and cell_intersect(cell, wing1)
                            and cell_intersect(cell, wing2)
                            and num in self.get_possibility(cell)
                        ):
                            new_erases.add((cell, num))
                            erase_cells.add(cell)
                    if print_details and erase_cells:
                        print(
                            f'{cell_to_string(wing1)}格的候选数'
                            f'{set_of_numbers_to_string(wing1_set)}、'
                            f'{cell_to_string(center)}格的候选数'
                            f'{set_of_numbers_to_string(center_set)}'
                            f'和{cell_to_string(wing2)}格的候选数'
                            f'{set_of_numbers_to_string(wing2_set)}'
                            f'形成三分支匹配，此三格当中必有一格等于{num}。'
                            f'在处于这三格共同作用域中的'
                            f'{set_of_cells_to_string(erase_cells)}格'
                            f'删去候选数{num}。'
                        )
        return new_erases

    def generate_link_graphs_for_number(
        self, num: int,
    ) -> Tuple[Dict[Node, Set[Node]], Dict[Node, Set[Node]]]:
        """
        Generate the link graphs for the number num.
        
        Parameters
        ----------
        num : int
            The number (between 1 and 9).
        
        Returns
        -------
        map from node (cell position, num) to set of strong link nodes
        map from node (cell position, num) to set of weak link nodes
            A node is an unfilled position where num is a possibility. A strong
            link between nodes P and Q means that P=>!Q and !P=>Q. A weak link
            between nodes P and Q means that P=>!Q.
        
        """
        all_nodes = {
            (cell, num) for cell in ALL_CELLS
            if (
                len(self.get_possibility(cell)) > 1
                and num in self.get_possibility(cell)
            )
        }
        strong_links = {node: set() for node in all_nodes}
        weak_links = {node: set() for node in all_nodes}
        row_nodes = [{n for n in all_nodes if n[0][0] == i} for i in range(9)]
        col_nodes = [{n for n in all_nodes if n[0][1] == j} for j in range(9)]
        sqr_nodes = [
            {n for n in all_nodes if square_index_of(n[0]) == s}
            for s in range(9)
        ]
        for nodes in row_nodes + col_nodes + sqr_nodes:
            if len(nodes) <= 1:
                continue
            for node in nodes:
                self.add_links(
                    nodes.difference({node}),
                    strong_links[node],
                    weak_links[node],
                )
        return strong_links, weak_links
    
    def generate_link_graphs_for_all_numbers(
        self,
        link_graphs_per_num: Dict[
            int, Tuple[Dict[Node, Set[Node]], Dict[Node, Set[Node]]],
        ],
    ) -> Tuple[Dict[Node, Set[Node]], Dict[Node, Set[Node]]]:
        """
        Generate the link graphs for all numbers.
        
        Parameters
        ----------
        map from int to tuple (strong link map, weak link map)
            The map from each number between 1 and 9 to the link graphs for
            that number.
        
        Returns
        -------
        map from node (cell position, number) to set of strong link nodes
        map from node (cell position, number) to set of weak link nodes
            A node is a pair of an unfilled position and a number where the
            number is a possibility at the position. A strong link between
            nodes P and Q means that P=>!Q and !P=>Q. A weak link between
            nodes P and Q means that P=>!Q.
        
        """
        strong_links = dict()
        weak_links = dict()
        for num in ALL_NUMBERS:
            strong_links_for_num, weak_links_for_num = link_graphs_per_num[num]
            for node, links in strong_links_for_num.items():
                strong_links[node] = deepcopy(links)
            for node, links in weak_links_for_num.items():
                weak_links[node] = deepcopy(links)
        for cell in ALL_CELLS:
            if len(self.get_possibility(cell)) > 1:
                nodes = {(cell, num) for num in self.get_possibility(cell)}
                for num in self.get_possibility(cell):
                    node = (cell, num)
                    self.add_links(
                        nodes.difference({node}),
                        strong_links[node],
                        weak_links[node],
                    )
        return strong_links, weak_links

    @staticmethod
    def add_links(
        links: Set[Node], strong: Set[Node], weak: Set[Node],
    ) -> None:
        if len(links) == 1:
            strong.add(only_element_in_set(links))
        else:
            for element in links:
                weak.add(element)

    def check_coloring_strong_links(self, print_details: bool) -> Set[Node]:
        new_erases = set()
        # 7.1. Find coloring strong links for each number.
        for num in ALL_NUMBERS:
            strong_links, weak_links = self.link_graphs_per_num[num]
            full_color_map, res1, res2 = self.coloring_strong_links(
                strong_links, weak_links, node_dist_func=node_dist,
            )
            to_print = dict()
            for color_value, nodes in res1.items():
                color_map = full_color_map[color_value]
                for n1, n2 in nodes:
                    new_erases.add(n1)
                    new_erases.add(n2)
                    if print_details:
                        if color_value not in to_print:
                            to_print[color_value] = []
                        cs1 = colored_string(
                            cell_to_string(n1[0]),
                            POS_OR_NEG_COLOR[color_map[n1] > 0],
                        )
                        cs2 = colored_string(
                            cell_to_string(n2[0]),
                            POS_OR_NEG_COLOR[color_map[n2] > 0],
                        )
                        to_print[color_value].append(
                            f'在{cs1}格和{cs2}格删去候选数{num}，因为它们相互作用且为同色。'
                        )
            for color_value, nodes in res2.items():
                m = dict()
                for node, pos, neg in nodes:
                    new_erases.add(node)
                    if (pos, neg) not in m:
                        m[(pos, neg)] = set()
                    m[(pos, neg)].add(node[0])
                if print_details:
                    if color_value not in to_print:
                        to_print[color_value] = []
                    for intersections, erase_cells in m.items():
                        pos, neg = intersections
                        cp = colored_string(
                            cell_to_string(pos[0]), POSITIVE_COLOR,
                        )
                        cn = colored_string(
                            cell_to_string(neg[0]), NEGATIVE_COLOR,
                        )
                        to_print[color_value].append(
                            f'在{set_of_cells_to_string(erase_cells)}格'
                            f'删去候选数{num}，'
                            f'因为它{plural(erase_cells)}'
                            f'处于两个异色格{cp}和{cn}的共同作用域中。'
                        )
            if print_details:
                for color_value, conclusions in to_print.items():
                    color_map = full_color_map[color_value]
                    print(f'对数字{num}的强关系图染色：')
                    self.show_possibility(color_map)
                    for conclusion in conclusions:
                        print(conclusion)
        if new_erases:
            return new_erases
        # 7.2. Find coloring strong links for all numbers.
        full_color_map, res1, res2 = self.coloring_strong_links(
            self.all_num_strong_links,
            self.all_num_weak_links,
            node_dist_func=node_dist,
        )
        to_print = dict()
        for color_value, nodes in res1.items():
            color_map = full_color_map[color_value]
            for n1, n2 in nodes:
                new_erases.add(n1)
                new_erases.add(n2)
                if print_details:
                    if color_value not in to_print:
                        to_print[color_value] = []
                    c1 = colored_string(
                        node_to_words(n1), POS_OR_NEG_COLOR[color_map[n1] > 0],
                    )
                    c2 = colored_string(
                        node_to_words(n2), POS_OR_NEG_COLOR[color_map[n2] > 0],
                    )
                    to_print[color_value].append(f'删去{c1}和{c2}，因为它们相互作用且为同色。')
        for color_value, nodes in res2.items():
            m = dict()
            for node, pos, neg in nodes:
                new_erases.add(node)
                if (pos, neg) not in m:
                    m[(pos, neg)] = set()
                m[(pos, neg)].add(node)
            if print_details:
                if color_value not in to_print:
                    to_print[color_value] = []
                for intersections, erase_nodes in m.items():
                    pos, neg = intersections
                    cp = colored_string(node_to_words(pos), POSITIVE_COLOR)
                    cn = colored_string(node_to_words(neg), NEGATIVE_COLOR)
                    to_print[color_value].append(
                        f'删去{set_of_nodes_to_words(erase_nodes)}，'
                        f'因为它{plural(erase_nodes)}'
                        f'处于两个异色的{cp}和{cn}的共同作用域中。'
                    )
        if print_details:
            for color_value, conclusions in to_print.items():
                color_map = full_color_map[color_value]
                print('对多个数字的强关系图染色：')
                self.show_possibility(color_map)
                for conclusion in conclusions:
                    print(conclusion)
        return new_erases

    def coloring_strong_links(
        self,
        strong_links: Dict[Node, Set[Node]],
        weak_links: Dict[Node, Set[Node]],
        node_cmpr_func: Callable[[Node, Node], bool] = lambda n1, n2: n1 < n2,
        node_dist_func: Callable[[Node, Node], int] = lambda n1, n2: 0,
    ) -> Tuple[
        Dict[int, Dict[Node, int]],
        Dict[int, List[Tuple[Node, Node]]],
        Dict[int, List[Tuple[Node, Node, Node]]],
    ]:
        """
        Find nodes to be erased, by coloring strong links.

        Parameters
        ----------
        strong_links : map from node to set of strong link nodes
        weak_links : map from node to set of weak link nodes
        node_cmpr_func : function (node, node) -> bool
            A function that returns whether the first node is "less than" the
            second node, to be used when determining the order of a pair of
            intersecting nodes.
        node_dist_func : function (node, node) -> number
            A function that computes the distance between two nodes, to be used
            when finding the closest positive and negative intersection nodes.

        Returns
        -------
        map from color_value to color_map
            Color map is a map from node to its coloring number which is
            color_value or -color_value.
        map from color_value to list of tuples (erase_node_1, erase_node_2)
            Erase nodes are two intersecting nodes with the same color in a
            strong link graph.
        map from color_value to list of tuples
            (erase_node, positive_intersection_node,
            negative_intersection_node)
            Erase nodes are nodes which intersect with two nodes of opposing
            color in a strong link graph.
            Two nodes are said to intersect with each other if there is a link
            between them, weak or strong.

        """
        full_color_map = self.compute_full_color_map(strong_links)
        res1, res2 = dict(), dict()
        erase_nodes = set()
        for color_value in sorted(full_color_map.keys()):
            color_map = full_color_map[color_value]
            res = self.two_intersecting_nodes_with_same_color(
                color_map, strong_links, weak_links, node_cmpr_func,
            )
            if res:
                res1[color_value] = []
                for n1, n2 in res:
                    if n1 not in erase_nodes or n2 not in erase_nodes:
                        res1[color_value].append((n1, n2))
                        erase_nodes.add(n1)
                        erase_nodes.add(n2)
            res = self.uncolored_nodes_intersecting_both_colors(
                color_map, strong_links, weak_links, node_dist_func,
            )
            if res:
                res2[color_value] = []
                for node, pos, neg in res:
                    if node not in erase_nodes:
                        res2[color_value].append((node, pos, neg))
                        erase_nodes.add(node)
        return (
            full_color_map,
            {cv: res for cv, res in res1.items() if res},
            {cv: res for cv, res in res2.items() if res},
        )

    @staticmethod
    def compute_full_color_map(
        strong_links: Dict[Node, Set[Node]]
    ) -> Dict[int, Dict[Node, int]]:
        component = 1
        full_color_map = dict()
        colored = set()
        for node in sorted(strong_links.keys()):
            if node in colored or not strong_links[node]:
                continue
            full_color_map[component] = dict()
            to_color = {node}
            c = component
            while to_color:
                new_to_color = set()
                for n in to_color:
                    full_color_map[component][n] = c
                    colored.add(n)
                for n in to_color:
                    for m in strong_links[n]:
                        if m not in colored:
                            new_to_color.add(m)
                to_color = new_to_color
                c *= -1
            component += 1
        return full_color_map

    @staticmethod
    def two_intersecting_nodes_with_same_color(
        color_map: Dict[Node, int],
        strong_links: Dict[Node, Set[Node]],
        weak_links: Dict[Node, Set[Node]],
        node_cmpr_func: Callable[[Node, Node], bool],
    ) -> List[Tuple[Node, Node]]:
        res = []
        nodes = sorted(color_map.keys())
        for i in range(len(nodes)):
            n1 = nodes[i]
            c = color_map[n1]
            affected = strong_links[n1].union(weak_links[n1])
            for j in range(i + 1, len(nodes)):
                n2 = nodes[j]
                if n2 in affected and color_map[n2] == c:
                    if node_cmpr_func(n1, n2):
                        res.append((n1, n2))
                    else:
                        res.append((n2, n1))
        return res

    @staticmethod
    def uncolored_nodes_intersecting_both_colors(
        color_map: Dict[Node, int],
        strong_links: Dict[Node, Set[Node]],
        weak_links: Dict[Node, Set[Node]],
        node_dist_func: Callable[[Node, Node], int],
    ) -> List[Tuple[Node, Node, Node]]:
        res = []
        color_map_nodes = sorted(color_map.keys())
        for node in sorted(strong_links.keys()):
            if node in color_map:
                continue
            affected = strong_links[node].union(weak_links[node])
            intersect = dict()
            for n in color_map_nodes:
                positive = (color_map[n] > 0)
                if n in affected and (
                    positive not in intersect
                    or node_dist_func(node, n) < node_dist_func(
                        node, intersect[positive],
                    )
                ):
                    intersect[positive] = n
            if True in intersect and False in intersect:
                res.append((node, intersect[True], intersect[False]))
        return res

    def check_strong_weak_chains(
        self, print_details: bool, max_chain_length: int,
    ) -> Tuple[Set[Node], Set[Node]]:
        new_fills, new_erases = set(), set()
        # 8.1. Find strong-weak chains for each number.
        for num in ALL_NUMBERS:
            strong_links, weak_links = self.link_graphs_per_num[num]
            chain_nodes, links_are_strong, erase_nodes = (
                self.strong_weak_chains(
                    strong_links,
                    weak_links,
                    max_chain_length,
                    node_dist_func=node_dist,
                )
            )
            if chain_nodes and links_are_strong:
                if print_details:
                    color_map = self.strong_weak_chain_to_color_map(
                        chain_nodes
                    )
                    cs = self.strong_weak_chain_to_string(
                        color_map,
                        chain_nodes,
                        links_are_strong,
                        node_to_cell_string,
                    )
                    print(f'考虑数字{num}的强弱交替关系链{cs}：')
                    self.show_possibility(color_map)
                if not erase_nodes:
                    new_fills.add(chain_nodes[0])
                    if print_details:
                        cs = colored_string(
                            node_to_cell_string(chain_nodes[0]),
                            POSITIVE_COLOR,
                        )
                        print(f'这条链是一个圈，所以它的起点{cs}格必须填入{num}。')
                else:
                    for node in erase_nodes:
                        new_erases.add(node)
                    if print_details:
                        cs = colored_string('链首链尾', POSITIVE_COLOR)
                        cell_set = {n[0] for n in erase_nodes}
                        print(
                            f'在{set_of_cells_to_string(cell_set)}格'
                            f'删去候选数{num}，'
                            f'因为它{plural(erase_nodes)}处于{cs}的共同作用域中。'
                        )
        if new_fills or new_erases:
            return new_fills, new_erases
        # 8.2. Find strong-weak chains for all numbers.
        chain_nodes, links_are_strong, erase_nodes = (
            self.strong_weak_chains(
                self.all_num_strong_links,
                self.all_num_weak_links,
                max_chain_length,
                node_dist_func=node_dist,
            )
        )
        if chain_nodes and links_are_strong:
            if print_details:
                color_map = self.strong_weak_chain_to_color_map(chain_nodes)
                cs = self.strong_weak_chain_to_string(
                    color_map,
                    chain_nodes,
                    links_are_strong,
                    node_to_equal_string,
                )
                print(f'考虑多个数字的强弱交替关系链{cs}：')
                self.show_possibility(color_map)
            if not erase_nodes:
                new_fills.add(chain_nodes[0])
                if print_details:
                    cs = colored_string(
                        node_to_words(chain_nodes[0]), POSITIVE_COLOR,
                    )
                    print(f'这条链是一个圈，所以它的起点{cs}必须成立。')
            else:
                for node in erase_nodes:
                    new_erases.add(node)
                if print_details:
                    cs = colored_string('链首链尾', POSITIVE_COLOR)
                    print(
                        f'删去{set_of_nodes_to_words(erase_nodes)}，'
                        f'因为它{plural(erase_nodes)}处于{cs}的共同作用域中。'
                    )
        return new_fills, new_erases

    def strong_weak_chains(
        self,
        strong_links: Dict[Node, Set[Node]],
        weak_links: Dict[Node, Set[Node]],
        max_chain_length: int,
        node_dist_func: Callable[[Node, Node], int] = lambda n1, n2: 0,
    ) -> Tuple[List[Node], List[bool], Set[Node]]:
        """
        Find nodes to be filled or erased, by strong-weak chains. When there is
        a node to be filled, we will skip checking nodes to be erased.
        A strong-weak chain is an odd-length chain in the link graph of the
        form N_0 == N_1 -- N_2 == N_3 -- ... == N_{2k-1}. The 1st, 3rd, 5th...
        and the last link are required to be strong, while the rest can be
        either strong or weak.
        If a strong-weak chain is a loop (i.e. N_0 is equal to N_{2k-1}), then
        N_0 must be True (filled).
        If there is another node N which has a strong or weak link with both
        the start node N_0 and the end node N_{2k-1} of the chain, then N must
        be False (erased).
        Note that finding fills and erases from strong-weak chains is
        equivalent to finding odd-length loops in which every other link is
        required to be strong.
        
        Parameters
        ----------
        strong_links : map from node to set of strong link nodes
        weak_links : map from node to set of weak link nodes
        max_chain_length : int
            The maximum length of the strong-weak chain to search for.
        node_dist_func : function (node, node) -> number
            A function that computes the distance between two nodes, to be used
            when sorting next step nodes.
        
        Returns
        -------
        list of nodes
            The nodes in the chain.
        list of bool
            Whether each link in the chain is a strong one.
        set of nodes
            The nodes (to be erased) which link to both the start and the end
            of a strong-weak chain. Empty if the first node of the chain is to
            be filled.
        
        """
        nodes = sorted(strong_links.keys())
        # Find an odd-length loop with 1st, 3rd, 5th... links strong. The start
        # node should be filled.
        for node in nodes:
            loop_nodes, links_are_strong = self.find_odd_loop_iterate(
                strong_links,
                weak_links,
                [node],
                [],
                True,
                max_chain_length,
                node_dist_func,
            )
            if loop_nodes and links_are_strong:
                return (
                    loop_nodes + [loop_nodes[0]],
                    links_are_strong + [True],
                    set(),
                )
        # Find an odd-length loop with 2nd, 4th, 6th... links strong. The start
        # node should be erased.
        for node in nodes:
            loop_nodes, links_are_strong = self.find_odd_loop_iterate(
                strong_links,
                weak_links,
                [node],
                [],
                False,
                max_chain_length + 2,
                node_dist_func,
            )
            if loop_nodes and links_are_strong:
                affected_by_start = strong_links[loop_nodes[1]].union(
                    weak_links[loop_nodes[1]]
                )
                affected_by_end = strong_links[loop_nodes[-1]].union(
                    weak_links[loop_nodes[-1]]
                )
                return (
                    loop_nodes[1:],
                    links_are_strong[1:],
                    affected_by_start.intersection(affected_by_end),
                )
        return [], [], set()
    
    def find_odd_loop_iterate(
        self,
        strong_links: Dict[Node, Set[Node]],
        weak_links: Dict[Node, Set[Node]],
        route_so_far: List[Node],
        links_are_strong_so_far: List[bool],
        next_link_must_be_strong: bool,
        max_loop_length: int,
        node_dist_func: Callable[[Node, Node], int],
    ) -> Tuple[List[Node], List[bool]]:
        if not route_so_far or len(route_so_far) > max_loop_length:
            return [], []
        start_node, last_node = route_so_far[0], route_so_far[-1]
        next_steps = {n: True for n in strong_links[last_node]}
        if not next_link_must_be_strong:
            for n in weak_links[last_node]:
                next_steps[n] = False
        if start_node in next_steps and len(route_so_far) % 2 == 1:
            return route_so_far, links_are_strong_so_far
        for next_node in sorted(
            next_steps.keys(), key=lambda n: node_dist_func(n, last_node),
        ):
            if next_node in route_so_far:
                continue
            rt, lk = self.find_odd_loop_iterate(
                strong_links,
                weak_links,
                route_so_far + [next_node],
                links_are_strong_so_far + [next_steps[next_node]],
                not next_link_must_be_strong,
                max_loop_length,
                node_dist_func,
            )
            if rt and lk:
                return rt, lk
        return [], []

    @staticmethod
    def strong_weak_chain_to_color_map(
        chain_nodes: List[Node]
    ) -> Dict[Node, int]:
        return {
            n: 1 if i == 0 or i == len(chain_nodes) - 1 else -1
            for i, n in enumerate(chain_nodes)
        }

    @staticmethod
    def strong_weak_chain_to_string(
        color_map: Dict[Node, int],
        chain_nodes: List[Node],
        links_are_strong: List[bool],
        node_to_string: Callable[[Node], str],
    ) -> str:
        s = colored_string(
            node_to_string(chain_nodes[0]),
            POS_OR_NEG_COLOR[color_map[chain_nodes[0]] > 0],
        )
        for r, l in zip(chain_nodes[1:], links_are_strong):
            if l:
                s = s + ' == '
            else:
                s = s + ' -- '
            s = s + colored_string(
                node_to_string(r), POS_OR_NEG_COLOR[color_map[r] > 0],
            )
        return s

    def check_two_way_forks(
        self, print_details: bool, max_derivation_depth: int,
    ) -> Tuple[Set[Node], Set[Node]]:
        new_fills, new_erases = set(), set()
        # 9. Examine cells with exactly two possibilities for contradictions or
        # common conclusions from two-way forks.
        for cell in self.two_poss_cells:
            contra, common = self.two_way_fork(cell, max_derivation_depth)
            if contra:
                conclusion, chain = contra
                c, num, _ = conclusion
                new_fills.add((c, num))
                if print_details:
                    c0, num0, _ = only_element_in_set(chain.pop(0))
                    print(
                        f'{event_to_string(conclusion)}，'
                        f'因为如若不然，{cell_to_string(c0)}格等于{num0}，'
                        f'则{event_chain_to_string(chain)}。'
                    )
                break
            if common:
                for conclusion, chain_1, chain_2 in common:
                    c, num, positive = conclusion
                    if positive:
                        new_fills.add((c, num))
                    else:
                        new_erases.add((c, num))
                    if print_details:
                        c1, num1, _ = only_element_in_set(chain_1.pop(0))
                        c2, num2, _ = only_element_in_set(chain_2.pop(0))
                        print(
                            f'{event_to_string(conclusion)}，因为在仅有的两种情况下：'
                        )
                        print(
                            f'情况一：如果{cell_to_string(c1)}格等于{num1}，'
                            f'则{event_chain_to_string(chain_1)}；'
                        )
                        print(
                            f'情况二：如果{cell_to_string(c2)}格等于{num2}，'
                            f'则{event_chain_to_string(chain_2)}。'
                        )
                break
        return new_fills, new_erases

    def two_way_fork(
        self, start_cell: Cell, max_derivation_depth: int,
    ) -> Tuple[
        Union[Tuple[Event, List[Set[Event]]], None],
        List[Tuple[Event, List[Set[Event]], List[Set[Event]]]],
    ]:
        """
        For a cell with only two possibility numbers, try both and use simple
        logic to see if both forks arrive at the same conclusion for other
        cells, or if any fork leads to a contradiction.
        
        Parameters
        ----------
        start_cell : tuple (int, int)
            Row and column indices of the cell.
        max_derivation_depth : int
            The maximum depth of positive derivations.
        
        Returns
        -------
        tuple (conclusion, contradiction_derivation_chain)
            If one of the forks leads to a contradiction, return the conclusion
            made for this cell and the derivation chain for the impossible
            event. None if no contradictions are found.
        list of tuples (conclusion, derivation_chain, derivation_chain)
            List of all common conclusions and their derivation chains under
            the two cases. If there exists positive conclusions, then only
            positive conclusions are returned.
        
        """
        if max_derivation_depth == 0:
            return None, []
        possibility = {
            cell: deepcopy(self.get_possibility(cell))
            for cell in ALL_CELLS
            if len(self.get_possibility(cell)) > 1
        }
        g1, g2 = sorted(self.get_possibility(start_cell))
        start_event_1 = (start_cell, g1, True)
        start_event_2 = (start_cell, g2, True)
        imp_event_1, reason_map_1, depth_map_1 = self.derive(
            possibility, start_event_1, max_derivation_depth,
        )
        if imp_event_1:
            return (
                (
                    start_event_2,
                    self.derivation_chain(
                        imp_event_1, reason_map_1, depth_map_1,
                    ),
                ),
                [],
            )
        imp_event_2, reason_map_2, depth_map_2 = self.derive(
            possibility, start_event_2, max_derivation_depth,
        )
        if imp_event_2:
            return (
                (
                    start_event_1,
                    self.derivation_chain(
                        imp_event_2, reason_map_2, depth_map_2,
                    ),
                ),
                [],
            )
        inter = set(reason_map_1.keys()).intersection(set(reason_map_2.keys()))
        res = []
        if inter:
            exists_positive = any([event[-1] for event in inter])
            for event in inter:
                if exists_positive and not event[-1]:
                    continue
                res.append((
                    event,
                    self.derivation_chain(event, reason_map_1, depth_map_1),
                    self.derivation_chain(event, reason_map_2, depth_map_2),
                ))
        return None, res
    
    def derive(
        self,
        original_possibility: Dict[Cell, Set[int]],
        start_event: Event,
        max_depth: int,
    ) -> Tuple[Union[Event, None], Dict[Event, Set[Event]], Dict[Event, int]]:
        original_nsrc_map = self.nsrc_map(original_possibility)
        possibility = deepcopy(original_possibility)
        positive_events = {start_event}
        reason_map = dict()
        depth_map = {start_event: 0}
        for _ in range(max_depth):
            # Generate all negative events from the set of positive events.
            for positive_event in positive_events:
                cell, num, _ = positive_event
                if cell not in possibility or num not in possibility[cell]:
                    continue
                negative_events = set()
                for m in possibility[cell].difference({num}):
                    negative_events.add((cell, m, False))
                possibility.pop(cell)
                for c in cells_affected_by(cell):
                    if c in possibility and num in possibility[c]:
                        negative_events.add((c, num, False))
                        possibility[c].discard(num)
                for negative_event in negative_events:
                    if negative_event not in reason_map:
                        reason_map[negative_event] = {positive_event}
                        depth_map[negative_event] = (
                            depth_map[positive_event] + 1
                        )
            # Look for impossible positions.
            for cell, num_set in possibility.items():
                if not num_set:
                    impossible_event = (cell, 0, True)
                    source = {
                        (cell, m, False) for m in original_possibility[cell]
                    }
                    reason_map[impossible_event] = source
                    depth_map[impossible_event] = (
                        max(depth_map[e] for e in source) + 1
                    )
                    return impossible_event, reason_map, depth_map
            # Look for new positive events after erasing the negative events.
            nsrc_map = self.nsrc_map(possibility)
            new = dict()
            for cell, num_set in possibility.items():
                if len(num_set) == 1:
                    positive_event = (cell, only_element_in_set(num_set), True)
                    if positive_event not in reason_map:
                        source = {
                            (cell, m, False)
                            for m in original_possibility[cell].difference(
                                num_set
                            )
                        }
                        new[positive_event] = source
            for num in ALL_NUMBERS:
                for idx, cell_set in enumerate(nsrc_map[num]):
                    if len(cell_set) == 1:
                        positive_event = (
                            only_element_in_set(cell_set), num, True,
                        )
                        if positive_event not in reason_map:
                            source = {
                                (cell, num, False)
                                for cell in (
                                    original_nsrc_map[num][idx].difference(
                                        cell_set
                                    )
                                )
                            }
                            if (
                                positive_event not in new
                                or len(source) < len(new[positive_event])
                            ):
                                new[positive_event] = source
            if not new:
                break
            for positive_event, source in new.items():
                reason_map[positive_event] = source
                depth_map[positive_event] = (
                    max(depth_map[e] for e in source) + 1
                )
            positive_events = set(new.keys())
        return None, reason_map, depth_map

    @staticmethod
    def nsrc_map(
        possibility: Dict[Cell, Set[int]]
    ) -> Dict[int, List[Set[Cell]]]:
        res = dict()
        for num in ALL_NUMBERS:
            res[num] = [set() for _ in range(27)]
            for cell, num_set in possibility.items():
                if num in num_set:
                    res[num][square_index_of(cell)].add(cell)
                    res[num][9 + cell[0]].add(cell)
                    res[num][18 + cell[1]].add(cell)
        return res

    @staticmethod
    def derivation_chain(
        event: Event,
        reason_map: Dict[Event, Set[Event]],
        depth_map: Dict[Event, int],
    ) -> List[Set[Event]]:
        dm = dict()
        events = {event}
        seen = set()
        while events:
            new_events = set()
            seen = seen.union(events)
            for e in events:
                d = depth_map[e]
                if d not in dm:
                    dm[d] = set()
                dm[d].add(e)
                if e in reason_map:
                    for source in reason_map[e]:
                        if source not in seen:
                            new_events.add(source)
            events = new_events
        return [dm[i] for i in range(depth_map[event] + 1)]

    def check_strong_link_clusters(self, print_details: bool) -> Set[Node]:
        # 10. Follow weak link bridges between strong link connected components
        # to find fills from contradictions.
        new_fills, contra, route_1, route_2 = self.strong_link_clusters(
            self.all_num_strong_links, self.all_num_weak_links,
        )
        if new_fills and print_details:
            contra_cluster, contra_color_map = contra
            if not route_1:
                route_1, route_2 = route_2, route_1
            print(
                f'考虑如下所示的强关系图。'
                f'如果其中的{color_to_words(contra_cluster[1])}结点成立：'
            )
            self.show_possibility(contra_color_map)
            for bridge, cluster, color_map in route_1:
                prev_node, node = bridge
                print(
                    f'通过弱关系{node_to_equal_string(prev_node)} '
                    f'-- {node_to_equal_string(node)}搭桥，'
                    f'下面的强关系图中的'
                    f'{color_to_words(not cluster[1])}结点不成立，'
                    f'{color_to_words(cluster[1])}结点成立：'
                )
                self.show_possibility(color_map)
            if route_2:
                print(
                    f'另一方面，回到最开始的强关系图。'
                    f'如果其中的{color_to_words(contra_cluster[1])}结点成立：'
                )
                self.show_possibility(contra_color_map)
                for bridge, cluster, color_map in route_2:
                    prev_node, node = bridge
                    print(
                        f'通过弱关系{node_to_equal_string(prev_node)} '
                        f'-- {node_to_equal_string(node)}搭桥，'
                        f'下面的强关系图中的'
                        f'{color_to_words(not cluster[1])}结点不成立，'
                        f'{color_to_words(cluster[1])}结点成立：'
                    )
                    self.show_possibility(color_map)
            print(
                f'这表明在这个强关系图中，'
                f'{color_to_words(True)}{color_to_words(False)}结点'
                f'需要同时成立，矛盾。'
            )
            self.show_possibility(contra_color_map)
            print(
                f'因此在最初的强关系图中，'
                f'{color_to_words(contra_cluster[1])}结点不能成立，'
                f'{color_to_words(not contra_cluster[1])}结点'
                f'{set_of_nodes_to_words(new_fills)}必须成立。'
            )
        return new_fills

    def strong_link_clusters(
        self,
        strong_links: Dict[Node, Set[Node]],
        weak_links: Dict[Node, Set[Node]],
    ) -> Tuple[
        Set[Node],
        Union[Tuple[Tuple[int, bool], Dict[Node, int]], None],
        List[Tuple[Tuple[Node, Node], Tuple[int, bool], Dict[Node, int]]],
        List[Tuple[Tuple[Node, Node], Tuple[int, bool], Dict[Node, int]]],
    ]:
        """
        Connected components in the strong link graph are connected by weak
        link bridges. Follow these bridges to find a contradiction.
        Each connected component consists of two clusters: positive and
        negative.
        If starting from a certain cluster, following weak link bridges we can
        arrive at both positive and negative clusters of another connected
        component, then this starting cluster must be False.

        Parameters
        ----------
        strong_links : map from node to set of strong link nodes
        weak_links : map from node to set of weak link nodes

        Returns
        -------
        set of nodes
            The nodes to fill.
        tuple (cluster, color_map)
            The cluster (color_value, positive) which gives the contradiction
            and its color map.
        list of tuples (bridge, cluster, color_map)
        list of tuples (bridge, cluster, color_map)
            The routes to arrive at the contradiction.

        """
        full_color_map = self.compute_full_color_map(strong_links)
        node_to_cluster, cluster_to_nodes = dict(), dict()
        for color_value, color_map in full_color_map.items():
            cluster_to_nodes[(color_value, True)] = set()
            cluster_to_nodes[(color_value, False)] = set()
            for node, color in color_map.items():
                cluster = (color_value, color > 0)
                node_to_cluster[node] = cluster
                cluster_to_nodes[cluster].add(node)
        bridges = dict()
        for color_value, color_map in full_color_map.items():
            bridges[(color_value, True)] = dict()
            bridges[(color_value, False)] = dict()
            for node in sorted(color_map.keys()):
                cluster = node_to_cluster[node]
                for n in sorted(weak_links[node]):
                    if n in node_to_cluster:
                        # If node is True, then n must be False, so the nodes
                        # with the opposite color as n in the cluster of n must
                        # be True.
                        linked_cluster = (
                            node_to_cluster[n][0], not node_to_cluster[n][1],
                        )
                        if linked_cluster not in bridges[cluster]:
                            bridges[cluster][linked_cluster] = (node, n)
        for curr_cluster in sorted(cluster_to_nodes.keys()):
            cluster_queue = {curr_cluster}
            seen = set()
            prev = dict()
            while cluster_queue:
                for cluster in cluster_queue:
                    seen.add(cluster)
                new_cluster_queue = set()
                for cluster in cluster_queue:
                    for c in bridges[cluster]:
                        if c not in seen:
                            new_cluster_queue.add(c)
                            if c not in prev:
                                prev[c] = cluster
                cluster_queue = new_cluster_queue
            for color_value, positive in seen:
                if (color_value, not positive) in seen:
                    # Have found a contradiction. Current cluster must be
                    # False.
                    fill_nodes = cluster_to_nodes[
                        (curr_cluster[0], not curr_cluster[1])
                    ]
                    route_1 = []
                    c = (color_value, positive)
                    while c in prev:
                        route_1.append(
                            (bridges[prev[c]][c], c, full_color_map[c[0]])
                        )
                        c = prev[c]
                    route_1.reverse()
                    route_2 = []
                    c = (color_value, not positive)
                    while c in prev:
                        route_2.append(
                            (bridges[prev[c]][c], c, full_color_map[c[0]])
                        )
                        c = prev[c]
                    route_2.reverse()
                    return (
                        fill_nodes,
                        (curr_cluster, full_color_map[curr_cluster[0]]),
                        route_1,
                        route_2,
                    )
        return set(), None, [], []
    
    def is_impossible(self) -> Tuple[bool, Union[Cell, None]]:
        """
        Whether the possibility map is impossible (i.e. if any cell has an
        empty possibility set).
        
        Parameters
        ----------
        None.
        
        Returns
        -------
        bool
            Whether the possibility map is impossible.
        tuple (int, int)
            Position of the impossible cell. None if not impossible.
        
        """
        for cell in ALL_CELLS:
            if len(self.get_possibility(cell)) == 0:
                return True, cell
        return False, None
    
    def exclude_possibilities_given_known_cell(self, cell: Cell) -> None:
        """
        Given the cell is filled, exclude the possibilities of the filled
        number from the possibility map in the row, column and square that the
        cell belongs to.
        
        Parameters
        ----------
        cell : tuple (int, int)
            Row and column indices of the cell.
        
        Returns
        -------
        None.
        
        """
        num = self.board[cell[0]][cell[1]]
        self.possibility[cell] = {num}
        for c in cells_affected_by(cell):
            self.remove_possibility(c, num)
    
    def is_solved(self) -> bool:
        for cell in ALL_CELLS:
            if self.is_unfilled(cell) or len(self.get_possibility(cell)) != 1:
                return False
        return True

    def is_filled(self, cell: Cell) -> bool:
        return self.board[cell[0]][cell[1]] > 0

    def is_unfilled(self, cell: Cell) -> bool:
        return self.board[cell[0]][cell[1]] == 0
    
    def write_cell(self, cell: Cell, num: int) -> None:
        self.board[cell[0]][cell[1]] = num
        self.exclude_possibilities_given_known_cell(cell)
    
    def execute_fills(self, fills: Set[Node]) -> None:
        for cell, num in fills:
            self.write_cell(cell, num)
    
    def execute_erases(self, erases: Set[Node]) -> None:
        for cell, num in erases:
            self.remove_possibility(cell, num)
    
    def remove_possibility(self, cell: Cell, num: int) -> None:
        self.possibility[cell].discard(num)
    
    def get_possibility(self, cell: Cell) -> Set[int]:
        return self.possibility[cell]
    
    def print_board(self, with_color: bool = False) -> None:
        if with_color:
            color = [
                [
                    UNSOLVED_COLOR if self.is_unfilled(cell) else SOLVED_COLOR
                    for cell in row
                ]
                for row in ROW_CELLS
            ]
        else:
            color = [[UNSOLVED_COLOR for _ in row] for row in ROW_CELLS]
        row_separator = '-' * 6 + '+' + '-' * 7 + '+' + '-' * 6
        for i in range(9):
            if i == 3 or i == 6:
                print(row_separator)
            self.print_board_row(self.board[i], color[i])

    @staticmethod
    def print_board_row(row: List[int], color: List[str]) -> None:
        print(
            '{} {} {} | {} {} {} | {} {} {}'.format(
                *[
                    colored_string(board_number_to_string(num), clr)
                    for num, clr in zip(row, color)
                ]
            )
        )

    def show_possibility(self, color_map: Dict[Node, int] = None) -> None:
        max_possibility_len = max(
            len(self.get_possibility(cell)) for cell in ALL_CELLS
        )
        square_len = 3 * max_possibility_len + 3
        row_separator = (
            '-' * square_len + '+'
            + '-' * (square_len + 1) + '+'
            + '-' * square_len
        )
        for i in range(9):
            if i == 3 or i == 6:
                print(row_separator)
            self.print_possibility_row(i, color_map, max_possibility_len)
    
    def print_possibility_row(
        self, i: Index, color_map: Dict[Node, int], width: int,
    ) -> None:
        print(
            '{} {} {} | {} {} {} | {} {} {}'.format(
                *[
                    self.possibility_string(cell, color_map, width)
                    for cell in ROW_CELLS[i]
                ]
            )
        )
    
    def possibility_string(
        self, cell: Cell, color_map: Dict[Node, int], width: int,
    ) -> str:
        num_string = set_of_numbers_to_string(
            self.get_possibility(cell)
        ).ljust(width)
        if self.is_filled(cell):
            return colored_string(num_string, SOLVED_COLOR)
        if color_map is None:
            return num_string
        num_char_list = [char for char in num_string]
        for idx, char in enumerate(num_string):
            if char not in ALL_NUMBERS_STRING_SET:
                continue
            node = (cell, int(char))
            if node in color_map:
                num_char_list[idx] = colored_string(
                    char, POS_OR_NEG_COLOR[color_map[node] > 0],
                )
        return ''.join(num_char_list)

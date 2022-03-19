"""
@author: yuan.shao
"""
import getopt
import sys
from copy import deepcopy
from time import time
from typing import Dict, List, Set, Tuple, Union

from constants import (
    ALL_CELLS,
    ALL_NUMBERS,
    CURRENT_GUESS_COLOR,
    DEFAULT_MAX_CHAIN_LENGTH,
    DEFAULT_MAX_DERIVATION_DEPTH,
    WRONG_GUESS_COLOR,
)
from evaluator import SudokuEvaluator
from sudoku import Sudoku
from type_aliases import Cell, Node
from utils import cell_to_string, colored_string


class SudokuSolver:
    def __init__(
        self,
        print_details: bool = False,
        check_multiple: bool = False,
        max_chain_length: int = DEFAULT_MAX_CHAIN_LENGTH,
        max_derivation_depth: int = DEFAULT_MAX_DERIVATION_DEPTH,
    ) -> None:
        """
        Initiate the Sudoku solver.

        Parameters
        ----------
        print_details : bool
            Whether to print out detail logics.
        check_multiple : bool
            Whether to check multiple solutions.
        max_chain_length : int
            The maximum search length for strong-weak chains.
        max_derivation_depth : int
            The maximum search depth for two-way forks.

        Returns
        -------
        SudokuSolver

        """
        self.print_details = print_details
        self.check_multiple = check_multiple
        self.max_chain_length = max_chain_length
        self.max_derivation_depth = max_derivation_depth

    def solve(
        self, sudoku: Sudoku,
    ) -> Tuple[bool, Union[Sudoku, None], Union[Sudoku, None], int]:
        """
        Solve the given Sudoku.

        Parameters
        ----------
        sudoku : Sudoku

        Returns
        -------
        bool
            Whether the solve is successful.
        Sudoku
            The final state of the Sudoku.
        Sudoku
            The final state of the second solution. None if impossible to solve
            or solution is unique.
        int
            The total number of guesses.

        """
        final_state, prev_solution, ng = self.solve_iterate(
            deepcopy(sudoku), None, 0, [],
        )
        if prev_solution:
            if final_state.is_solved():
                return True, prev_solution, final_state, ng
            else:
                return True, prev_solution, None, ng
        else:
            return final_state.is_solved(), final_state, None, ng

    def solve_iterate(
        self,
        sudoku: Sudoku,
        prev_solution: Union[Sudoku, None],
        num_of_guesses: int,
        guess_chain: List[Tuple[Cell, List[int], int]],
    ) -> Tuple[Sudoku, Union[Sudoku, None], int]:
        ng = num_of_guesses
        imp, _, _ = sudoku.logical_deduction(
            print_details=(self.print_details and not prev_solution),
            max_chain_length=self.max_chain_length,
            max_derivation_depth=self.max_derivation_depth,
        )
        if imp or sudoku.is_solved():
            return sudoku, prev_solution, ng
        # Find the "best" cell to make a guess.
        link_graphs_per_num = {
            num: sudoku.generate_link_graphs_for_number(num)
            for num in ALL_NUMBERS
        }
        all_num_strong_links, all_num_weak_links = (
            sudoku.generate_link_graphs_for_all_numbers(link_graphs_per_num)
        )
        full_color_map = sudoku.compute_full_color_map(all_num_strong_links)
        node_score = dict()
        for color_value, color_map in full_color_map.items():
            score = self.rate_color_map(color_map, all_num_weak_links)
            for node in color_map:
                node_score[node] = score
        for node, weak_links in all_num_weak_links.items():
            if node not in node_score:
                node_score[node] = len(
                    set(n for n in weak_links if n[0] != node[0])
                )
        max_score, guess_cell = 0, None
        for cell in ALL_CELLS:
            num_set = sudoku.get_possibility(cell)
            if len(num_set) > 1:
                score = (
                    sum(node_score[(cell, num)] for num in num_set)
                    / len(num_set)
                )
                if score > max_score:
                    max_score, guess_cell = score, cell
        guess_list = sorted(sudoku.get_possibility(guess_cell))
        for idx, num in enumerate(guess_list):
            if idx < len(guess_list) - 1:
                ng += 1
            guess = deepcopy(sudoku)
            guess.write_cell(guess_cell, num)
            if self.print_details and not prev_solution:
                print(f'已有猜测：{self.print_guess_chain(guess_chain, idx > 0)}。')
            if idx == 0:
                guess_chain.append((guess_cell, guess_list, 0))
            else:
                guess_chain[-1] = (guess_cell, guess_list, idx)
            if self.print_details and not prev_solution:
                print(f'现在假设：{self.print_guess_chain(guess_chain, False)}。')
            final_state, prev_solution, ng = self.solve_iterate(
                guess, prev_solution, ng, guess_chain,
            )
            if final_state.is_solved():
                if prev_solution or not self.check_multiple:
                    return final_state, prev_solution, ng
                prev_solution = final_state
            if self.print_details and not prev_solution:
                print(f'回溯到上一个猜测：{self.print_guess_chain(guess_chain, True)}。')
                sudoku.show_possibility()
                print()
        guess_chain.pop(-1)
        return sudoku, prev_solution, ng

    @staticmethod
    def rate_color_map(
        color_map: Dict[Node, int],
        weak_links: Dict[Node, Set[Node]],
    ) -> float:
        erase = set()
        for node in color_map:
            for n in weak_links[node]:
                # Do not count erases at the same cell. Otherwise, nodes in
                # cells with a lot of possibility numbers would earn a high
                # score.
                if n[0] != node[0]:
                    erase.add(n)
        return len(color_map) + len(erase) / 2

    def print_guess_chain(
        self, guess_chain: List[Tuple[Cell, List[int], int]], curr_fail: bool,
    ) -> str:
        if not guess_chain:
            return '无'
        guess_list_str = [
            self.guess_list_to_string(
                guess[1], guess[2], idx == len(guess_chain) - 1 and curr_fail,
            )
            for idx, guess in enumerate(guess_chain)
        ]
        return '，'.join(
            [
                f'{cell_to_string(guess[0])}格取候选数{{{s}}}'
                for guess, s in zip(guess_chain, guess_list_str)
            ]
        )

    @staticmethod
    def guess_list_to_string(
        guess_list: List[int], curr_index: int, curr_fail: bool,
    ) -> str:
        if curr_fail:
            curr_color = WRONG_GUESS_COLOR
        else:
            curr_color = CURRENT_GUESS_COLOR
        return (
                colored_string(
                    ''.join([str(num) for num in guess_list[:curr_index]]),
                    WRONG_GUESS_COLOR,
                )
                + colored_string(str(guess_list[curr_index]), curr_color)
                + ''.join([str(num) for num in guess_list[(curr_index + 1):]])
        )


def sudokus_from_file(f: str) -> List[Sudoku]:
    """
    Parse a csv file into a list of Sudoku objects.

    Parameters
    ----------
    f : string
        Csv file name. It can contain one or more boards. A board can be
        represented by a string of length 81, or 9 rows of 9 comma-separated
        cells.

    Returns
    -------
    list of Sudoku

    """
    sudokus = []
    matrix = []
    for line in open(f, 'r').read().splitlines():
        if not line:
            continue
        cells = line.split(',')
        if len(cells) == 1:
            sudokus.append(Sudoku.from_string(cells[0].strip()))
        elif len(cells) == 9:
            matrix.append([c.strip() for c in cells])
            if len(matrix) == 9:
                sudokus.append(Sudoku.from_matrix(matrix))
                matrix = []
    return sudokus


def main():
    short_options = 'b:f:pmc:d:'
    long_options = [
        'board=',
        'file=',
        'print_details',
        'multiple_solutions',
        'max_chain_length=',
        'max_derivation_depth=',
    ]
    try:
        args, _ = getopt.getopt(sys.argv[1:], short_options, long_options)
    except getopt.error as err:
        print(str(err))
        sys.exit(2)

    sudokus = []
    print_details = False
    check_multiple = False
    max_chain_length = DEFAULT_MAX_CHAIN_LENGTH
    max_derivation_depth = DEFAULT_MAX_DERIVATION_DEPTH
    for a, v in args:
        if a in ('-b', '--board') and len(sudokus) == 0:
            sudokus.append(Sudoku.from_string(v))
        elif a in ('-f', '--file') and len(sudokus) == 0:
            sudokus = sudokus_from_file(v)
        elif a in ('-p', '--print_details'):
            print_details = True
        elif a in ('-m', '--multiple_solutions'):
            check_multiple = True
        elif a in ('-c', '--max_chain_length'):
            max_chain_length = int(v)
        elif a in ('-d', '--max_derivation_depth'):
            max_derivation_depth = int(v)

    solver = SudokuSolver(
        print_details, check_multiple, max_chain_length, max_derivation_depth,
    )
    for i, sudoku in enumerate(sudokus):
        start_time = time()
        solved, final_state, second_solution, number_of_guesses = solver.solve(
            sudoku
        )
        solve_time = time() - start_time
        if len(sudokus) > 1:
            print(f'=== 第{i + 1}个数独 ===')
        sudoku.print_board()
        if solved:
            print('得解。答案：')
        else:
            print('无解。最终盘面：')
        final_state.print_board(with_color=True)
        if second_solution:
            print('解不唯一。另一可行解：')
            second_solution.print_board(with_color=True)
        difficulty = ''
        if solved and not second_solution:
            difficulty = f'难度等级：{SudokuEvaluator.evaluate(sudoku, True)}。'
        print(f'用时{solve_time:.3f}秒。共猜数{number_of_guesses}次。{difficulty}')
        print()


if __name__ == '__main__':
    main()

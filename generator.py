"""
@author: yuan.shao
"""
import getopt
import sys
from copy import deepcopy
from random import choice, shuffle
from typing import Set, Tuple, Union

from constants import (
    ALL_CELLS,
    DEFAULT_MAX_CHAIN_LENGTH,
    DEFAULT_MAX_DERIVATION_DEPTH,
)
from evaluator import SudokuEvaluator
from solver import SudokuSolver
from sudoku import Sudoku


class SudokuGenerator:
    def __init__(self, target_difficulty: Set[int]) -> None:
        self.target_difficulty = target_difficulty
        self.solver = SudokuSolver(print_details=False, check_multiple=True)

    def generate(self) -> Tuple[Sudoku, Sudoku, int]:
        while True:
            success, problem, solution, difficulty = self.generate_iterate(
                Sudoku.from_string('0' * 81)
            )
            if success:
                problem = self.remove_unnecessary_entries(problem, difficulty)
                return problem, solution, difficulty

    def generate_iterate(
        self, sudoku: Sudoku,
    ) -> Tuple[bool, Union[Sudoku, None], Union[Sudoku, None], int]:
        sudoku_deducted = deepcopy(sudoku)
        impossible, _, difficulty = sudoku_deducted.logical_deduction(
            print_details=False,
            max_chain_length=DEFAULT_MAX_CHAIN_LENGTH,
            max_derivation_depth=DEFAULT_MAX_DERIVATION_DEPTH,
        )
        if impossible:
            return False, None, None, 0
        if sudoku_deducted.is_solved():
            if difficulty in self.target_difficulty:
                return True, sudoku, sudoku_deducted, difficulty
            else:
                return False, None, None, 0
        cell = choice(
            [cell for cell in ALL_CELLS if sudoku_deducted.is_unfilled(cell)]
        )
        nums = list(sudoku.get_possibility(cell))
        shuffle(nums)
        for num in nums:
            sudoku_new = deepcopy(sudoku)
            sudoku_new.write_cell(cell, num)
            solved, final_state, second_solution, _ = self.solver.solve(
                sudoku_new
            )
            if not solved:
                continue
            if second_solution:
                success, problem, solution, difficulty = self.generate_iterate(
                    sudoku_new
                )
                if success:
                    return success, problem, solution, difficulty
            else:
                difficulty = SudokuEvaluator.evaluate(sudoku_new, False)
                if difficulty in self.target_difficulty:
                    return True, sudoku_new, final_state, difficulty
        return False, None, None, 0

    def remove_unnecessary_entries(
        self, sudoku: Sudoku, difficulty: int,
    ) -> Sudoku:
        sudoku_new = deepcopy(sudoku)
        while True:
            reduced = False
            cell_list = [
                cell for cell in ALL_CELLS if sudoku_new.is_filled(cell)
            ]
            shuffle(cell_list)
            for cell in cell_list:
                board = sudoku_new.board_to_int_matrix()
                board[cell[0]][cell[1]] = 0
                sudoku_reduced = Sudoku.from_matrix(board)
                sudoku_reduced.logical_deduction(
                    print_details=False,
                    max_chain_length=DEFAULT_MAX_CHAIN_LENGTH,
                    max_derivation_depth=DEFAULT_MAX_DERIVATION_DEPTH,
                    max_difficulty_level=difficulty,
                )
                if sudoku_reduced.is_unfilled(cell):
                    continue
                _, _, second_solution, _ = self.solver.solve(sudoku_reduced)
                if second_solution:
                    continue
                reduced = True
                sudoku_new = Sudoku.from_matrix(board)
                break
            if not reduced:
                return sudoku_new


def main():
    short_options = 'd:'
    long_options = ['difficulty=']
    try:
        args, _ = getopt.getopt(sys.argv[1:], short_options, long_options)
    except getopt.error as err:
        print(str(err))
        sys.exit(2)

    target_difficulty = {1, 2, 3, 4, 5}
    for a, v in args:
        if a in ('-d', '--difficulty'):
            difficulty = {
                int(s.strip()) for s in v.split(',')
                if s.strip() in {'1', '2', '3', '4', '5'}
            }
            if difficulty:
                target_difficulty = difficulty

    generator = SudokuGenerator(target_difficulty)
    problem, solution, difficulty = generator.generate()
    print('生成数独：')
    problem.print_board()
    print(f'数字串：{problem.board_to_string()}')
    print(f'难度等级：{difficulty} - {SudokuEvaluator.DESCRIPTION[difficulty]}')
    print('答案：')
    solution.print_board(with_color=True)
    print()


if __name__ == '__main__':
    main()

"""
@author: yuan.shao
"""
from copy import deepcopy
from typing import Union

from constants import DEFAULT_MAX_CHAIN_LENGTH, DEFAULT_MAX_DERIVATION_DEPTH
from sudoku import Sudoku


class SudokuEvaluator:
    DESCRIPTION = {0: '', 1: '容易', 2: '中等', 3: '困难', 4: '极难', 5: '最难'}

    @classmethod
    def evaluate(cls, sudoku: Sudoku, return_words: bool) -> Union[str, int]:
        """
        Evaluate the difficulty of the given Sudoku.

        Parameters
        ----------
        sudoku : Sudoku
        return_words : bool
            Return the difficulty in words or integer scale (1 to 5).

        Returns
        -------
        string or int

        """
        _, _, difficulty = deepcopy(sudoku).logical_deduction(
            print_details=False,
            max_chain_length=DEFAULT_MAX_CHAIN_LENGTH,
            max_derivation_depth=DEFAULT_MAX_DERIVATION_DEPTH,
        )
        return cls.DESCRIPTION[difficulty] if return_words else difficulty

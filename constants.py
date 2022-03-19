"""
@author: yuan.shao
"""
DEFAULT_MAX_CHAIN_LENGTH = 5
DEFAULT_MAX_DERIVATION_DEPTH = 2

ALL_CELLS = [(x // 9, x % 9) for x in range(81)]
SQR_CELLS = [
    [(3 * (s // 3) + x // 3, 3 * (s % 3) + x % 3) for x in range(9)]
    for s in range(9)
]
ROW_CELLS = [[(i, j) for j in range(9)] for i in range(9)]
COL_CELLS = [[(i, j) for i in range(9)] for j in range(9)]
ALL_NUMBERS = [1, 2, 3, 4, 5, 6, 7, 8, 9]
ALL_NUMBERS_SET = set(ALL_NUMBERS)
ALL_NUMBERS_STRING_SET = set(str(num) for num in ALL_NUMBERS)
NUM_TO_WORD = {
    1: '一', 2: '两', 3: '三', 4: '四', 5: '五', 6: '六', 7: '七', 8: '八', 9: '九',
}

COLORS = {
    'black':   '\033[90m',
    'red':     '\033[91m',
    'green':   '\033[92m',
    'yellow':  '\033[93m',
    'blue':    '\033[94m',
    'magenta': '\033[95m',
    'cyan':    '\033[96m',
    'white':   '\033[97m',
}
ENDC = '\033[0m'
SOLVED_COLOR = 'green'
UNSOLVED_COLOR = ''
POSITIVE_COLOR = 'yellow'
NEGATIVE_COLOR = 'magenta'
POS_OR_NEG_COLOR = {True: POSITIVE_COLOR, False: NEGATIVE_COLOR}
POS_OR_NEG_COLOR_WORDS = {True: '黄色', False: '紫色'}
CURRENT_GUESS_COLOR = 'green'
WRONG_GUESS_COLOR = 'red'

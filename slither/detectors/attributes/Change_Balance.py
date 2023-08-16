import typing
from typing import List

from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function
from slither.core.variables import Variable, StateVariable
from slither.utils.output import Output
from slither.core.cfg.node import NodeType
from slither.core.expressions import (
    CallExpression,
    BinaryOperation,
    BinaryOperationType,
    Identifier,
)

class ERC20ChangeBalance(AbstractDetector):
    ARGUMENT = "erc20-change-balance"
    HELP = "ERC20 Change Balance Functionality"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#erc20-change-balance"
    WIKI_TITLE = "ERC20 Change Balance Functionality"
    WIKI_DESCRIPTION = "Detect ERC20 change balance functionality."
    WIKI_RECOMMENDATION = "Make sure users are clear about how and when functionality can be paused."

    def _detect_change_balance_function(self, c: Contract) -> List[str]:
        results = []
        ignored_functions = ["mint", "burn","Transfer","transferFrom"]

        for f in c.functions:
            if f.name not in ignored_functions:
                if any(modifier.name == "onlyOwner" for modifier in f.modifiers):
                    if self._has_balance_altering_operations(f.instructions):
                        if self._performs_balance_increment_or_decrement(f.instructions):
                            results.append(f.name)

        return results

    def _detect(self) -> List[Output]:
        results = []

        # Your detection logic goes here

        return results

    def _has_balance_altering_operations(self, instructions):
        for instruction in instructions:
            if self._is_balance_altering_instruction(instruction):
                return True
        return False

    def _is_balance_altering_instruction(self, instruction):
        if isinstance(instruction, CallExpression) and "transfer" in str(instruction.called):
            return True

        return False

    def _performs_balance_increment_or_decrement(self, instructions):
        for instruction in instructions:
            if self._is_balance_increment_or_decrement_instruction(instruction):
                return True
        return False

    def _is_balance_increment_or_decrement_instruction(self, instruction):
        if isinstance(instruction, BinaryOperation) and instruction.type in [BinaryOperationType.ADD, BinaryOperationType.SUB]:
            left_operand = instruction.left
            right_operand = instruction.right

            if self._is_balance_variable(left_operand) or self._is_balance_variable(right_operand):
                return True

        return False

    def _is_balance_variable(self, variable):
        # Check if the variable is of type "mapping(address => uint256)" and its name is "balanceOf"
        if isinstance(variable, StateVariable) and variable.type.name == "mapping(address => uint256)" and variable.name == "balanceOf":
            return True

        return False

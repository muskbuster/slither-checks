"""
Module detecting unimplemented interfaces

Collect all the interfaces
Check for contracts which implement all interface functions but do not explicitly derive from those interfaces.
"""
import typing
from typing import List
from slither.detectors.abstract_detector import (
    AbstractDetector,
    DetectorClassification,
    DETECTOR_INFO,
)
from slither.core.declarations.contract import Contract
from slither.core.declarations.function import Function
from slither.core.variables import (
    Variable,
    StateVariable
)
from slither.utils.output import Output
from slither.core.cfg.node import NodeType
from slither.core.expressions import (
    CallExpression,
    BinaryOperation,
    BinaryOperationType,
    UnaryOperation,
    UnaryOperationType,
    AssignmentOperation,
    TupleExpression,
    Identifier
)
from slither.core.solidity_types import ElementaryType
from slither.analyses.data_dependency import data_dependency



class ERC20TransferLimit(AbstractDetector):
    ARGUMENT = "erc20-transfer-limit"
    HELP = "ERC20 Transfer Limit Detector"
    IMPACT = DetectorClassification.INFORMATIONAL
    CONFIDENCE = DetectorClassification.HIGH

    WIKI = "https://github.com/crytic/slither/wiki/Detector-Documentation#erc20-transfer-limit"
    WIKI_TITLE = "ERC20 Transfer Limit Detector"
    WIKI_DESCRIPTION = "Detect ERC20 contracts with transfer limits."
    WIKI_RECOMMENDATION = "Ensure the token transfer limits are set appropriately to avoid potential issues."

    def _detect(self) -> List[Output]:
        results = []

        for contract in self.contracts:
            if contract.is_token:
                transfer_functions = self._get_transfer_functions(contract)
                for transfer_function in transfer_functions:
                    transfer_limit = self._detect_transfer_limit(transfer_function)
                    if transfer_limit is not None:
                        results.append(self.generate_result(contract, transfer_function.name, transfer_limit))

        return results

    def _get_transfer_functions(self, contract: Contract) -> List[Function]:
        transfer_functions = []
        transfer_signatures = [
            "transfer(address,uint256)",
            "transferFrom(address,address,uint256)"
        ]
        for signature in transfer_signatures:
            function = contract.get_function_from_signature(signature)
            if function:
                transfer_functions.append(function)
        return transfer_functions

    def _detect_transfer_limit(self, function: Function) -> typing.Optional[int]:
        transfer_limit = None
        for node in function.all_nodes():
            if node.type == NodeType.EXPRESSION:
                exp = node.expression
                if self._is_transfer_require_statement(exp):
                    transfer_limit = self._get_transfer_limit(exp)
                    break
        return transfer_limit

    def _is_transfer_require_statement(self, exp) -> bool:
        return (
            isinstance(exp, BinaryOperation)
            and exp.type == BinaryOperationType.AND
            and self._is_transfer_require(exp.expression_left)
            and self._is_transfer_require(exp.expression_right)
        )

    def _is_transfer_require(self, exp) -> bool:
        return (
            isinstance(exp, BinaryOperation)
            and exp.type == BinaryOperationType.LT
            and isinstance(exp.expression_left, Identifier)
            and isinstance(exp.expression_right, Literal)
            and isinstance(exp.expression_left.value, StateVariable)
            and isinstance(exp.expression_right.value, int)
            and exp.expression_left.value.type.name == "uint256"
        )

    def _get_transfer_limit(self, exp) -> int:
        if exp.expression_left.value == "msg.value":
            return exp.expression_right.value
        elif exp.expression_right.value == "msg.value":
            return exp.expression_left.value
        else:
            return None

"""Pylint checker ensure correct usage of datetime module, especially around aware/naive objects."""

from typing import Any, assert_never

import astroid
from astroid import nodes, util
from pylint import checkers, lint

# function calls to fromisoformat, strptime and fromisoformat can't be checked - they parse strings
# if the specified timezone is None, still allowed although they produce naive objects


class DatetimeChecker(checkers.BaseChecker):  # type: ignore[misc]
    """class for custom pylint checker."""

    name = "pylint-datetime"
    priority = -1
    msgs = {
        "W9801": (
            "timedelta() called without keyword arguments",
            "datetime-timedelta-no-keyword-args",
            "timedelta() called without keyword arguments.",
        ),
        "W9802": (
            'Function call to "%s" should be called with a timezone argument',
            "datetime-call-without-timezone",
            'Function call to "%s" should be called with a timezone argument',
        ),
        "W9803": (
            'Function call to "%s" can only produce naive objects',
            "datetime-naive-object-used",
            'Function call to "%s" can only produce naive objects, aware objects necessary',
        ),
        "W9904": (
            'Attribute access "%s" should be directly followed by a call to replace with tzinfo',
            "datetime-missing-timezone-replace",
            'Attribute access "%s" should be directly followed by a call to replace with tzinfo',
        ),
    }

    def __init__(self, linter: lint.PyLinter) -> None:
        """Initialize checker.

        Args:
            linter: instance of pylint linter.
        """
        super().__init__(linter)

    # check for positional arguments cheesy, uses fact, that they have one Attribute Argument.

    def check_function_called_with_timezone(
        self, node: nodes.Call, func_name: str
    ) -> None:
        """Check calls to datetime, now, fromtimestamp, astimezone and time for timezone arg.

        Args:
            node: the node that visit_call originates from.
            func_name: name of the function being called.
        """
        if not any(
            isinstance(arg, astroid.Keyword) and arg.arg in ("tz", "tzinfo")
            for arg in node.keywords
        ):
            if not any(isinstance(arg, astroid.Attribute) for arg in node.args):
                self.add_message(
                    "datetime-call-without-timezone", node=node, args=(func_name,)
                )

    def visit_call(self, node: nodes.Call) -> None:
        """Pylint function responds when any function is called.

        Args:
            node: origin node for function call.
        """
        func = node.func
        assert func is not None

        if isinstance(func, (nodes.FunctionDef, astroid.Name)):
            func_name = func.name
        elif isinstance(func, astroid.Attribute):
            func_name = func.attrname
        else:
            assert False, "function call without name or attrname"

        if func_name in ("timedelta", "datetime"):
            for argument in node.args:
                if argument.value != 0:
                    self.add_message("datetime-timedelta-no-keyword-args", node=node)
                    break

        if func_name in ("fromordinal", "fromisocalendar"):
            if not self.has_replace_with_tzinfo(node):
                self.add_message(
                    "datetime-missing-timezone-replace", node=node, args=(func_name,)
                )

        if func_name in ("datetime", "now", "fromtimestamp", "astimezone"):
            self.check_function_called_with_timezone(node, func_name)

        if func_name in ("today", "utcnow", "utcfromtimestamp", "utctimetuple", "time"):
            self.add_message("datetime-naive-object-used", node=node, args=(func_name,))

    def visit_attribute(self, node: astroid.Attribute) -> None:
        """Check attribute access to datetime.datetime.min/max, datetime.time.min/max.

        Args:
            node: origin node for attribute.
        """
        if not isinstance(node, astroid.Attribute):
            print("ooh, hello")
            return
        if isinstance(node.expr, astroid.Name):
            name = node.expr.name
        elif isinstance(node.expr, astroid.Attribute):
            name = node.expr.attrname
        else:
            return
        if node.attrname in ("min", "max") and name in (
            "datetime",
            "time",
        ):
            if not self.has_replace_with_tzinfo(node):
                self.add_message(
                    "datetime-missing-timezone-replace",
                    node=node,
                    args=(node.attrname,),
                )

    def has_replace_with_tzinfo(self, node: astroid.Call) -> bool:
        """Check if the function call has a subsequent call to 'replace()' with 'tzinfo' argument.

        Args:
            node: origin node for function call.

        Returns:
            bool: if replace call has tzinfo
        """
        if (
            isinstance(node.parent, astroid.Attribute)
            and node.parent.attrname == "replace"
        ):
            for arg in node.parent.parent.args:
                if isinstance(arg, astroid.Attribute) and arg.expr.name in (
                    "timezone",
                    "None",
                ):
                    return True
            for arg in node.parent.parent.keywords:
                if arg.arg == "tzinfo":
                    return True
        return False


def register(linter: lint.PyLinter) -> None:
    """Pylint function to register checker.

    Args:
        linter: instance of pylint linter.
    """
    linter.register_checker(DatetimeChecker(linter))

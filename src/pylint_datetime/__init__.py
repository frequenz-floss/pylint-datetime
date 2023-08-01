"""Pylint checker ensure correct usage of datetime module, especially around aware/naive objects."""

from typing import Any, assert_never

import astroid
from astroid import bases, nodes, util
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
            'Attribute access "%s" should be followed by a call to replace with timezone argument',
            "datetime-missing-timezone-replace",
            'Attribute access "%s" should be followed by a call to replace with timezone argument',
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

        if func_name == "timedelta":
            for argument in node.args:
                if argument.value != 0:
                    self.add_message("datetime-timedelta-no-keyword-args", node=node)
                    break

        if func_name in ("datetime", "now", "fromtimestamp", "astimezone"):
            self.check_function_called_with_timezone(node, func_name)

        if func_name in ("today", "utcnow", "utcfromtimestamp", "utctimetuple", "time"):
            self.add_message("datetime-naive-object-used", node=node, args=(func_name,))

    def naive_properties_methods_replace(
        self, node: nodes.Assign, assigned_value: Any, assigned_var: Any
    ) -> None:
        """Check for a replace call specifiying timezone after naive property or function.

        Args:
            node: the node that visit_call originates from.
            assigned_value: the value of the assignment that triggered function call.
            assigned_var: the variable that the value was assigned to.
        """
        next_node = assigned_var
        next_is_empty = True
        if next_node and next_node.next_sibling():
            next_is_empty = False
            next_node = next_node.next_sibling()
            if (
                isinstance(next_node.value, astroid.Call)
                and isinstance(next_node.value.func, astroid.Attribute)
                and next_node.value.func.attrname == "replace"
            ):
                if not any(
                    isinstance(arg, astroid.Keyword) and arg.arg == "tzinfo"
                    for arg in next_node.value.keywords
                ) and (
                    not any(
                        isinstance(arg, astroid.Attribute)
                        for arg in next_node.value.args
                    )
                ):
                    new_node = next_node.value
                    self.add_message(
                        "datetime-call-without-timezone",
                        node=new_node,
                        args=("replace",),
                    )
            else:
                self.add_message(
                    "datetime-missing-timezone-replace",
                    node=node,
                    args=(assigned_value,),
                )
        if next_is_empty:
            self.add_message(
                "datetime-missing-timezone-replace", node=node, args=(assigned_value,)
            )

    def visit_assign(self, node: nodes.Assign) -> None:
        """Pylint function responds when any assignment takes place.

        Args:
            node: the node that visit_call originates from.
        """
        assigned_var = node.targets[0]
        assigned_value = node.value

        if isinstance(assigned_var, astroid.AssignName):
            assigned_var_type = assigned_var.inferred()[0]
            if assigned_var_type is not util.Uninferable:
                if assigned_var_type.qname() in ("datetime.datetime", "datetime.time"):
                    if isinstance(assigned_value, astroid.Attribute):
                        if assigned_value.attrname in ("min", "max"):
                            ass_val_name = assigned_value.attrname
                            self.naive_properties_methods_replace(
                                node, ass_val_name, assigned_var
                            )
                    if isinstance(assigned_value, astroid.Call):
                        func = assigned_value.func
                        assert isinstance(func, nodes.Attribute)
                        if func.attrname in (
                            "fromordinal",
                            "fromisocalendar",
                        ):
                            ass_val_name = func.attrname
                            self.naive_properties_methods_replace(
                                node, ass_val_name, assigned_var
                            )


def register(linter: lint.PyLinter) -> None:
    """Pylint function to register checker.

    Args:
        linter: instance of pylint linter.
    """
    linter.register_checker(DatetimeChecker(linter))

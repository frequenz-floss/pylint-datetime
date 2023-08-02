# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the frequenz.pylint_datetime package."""
from typing import Any

import astroid
from pylint import testutils

from pylint_datetime import DatetimeChecker

# tz=None and tzinfo=None is always allowed

# it makes a difference for astroid if for example timedelta is called or datetime.timedelta
# maybe this needs to be tested more thoroughly


class TestDatetimeChecker(testutils.CheckerTestCase):  # type: ignore
    """Test class for DatetimeChecker."""

    CHECKER_CLASS = DatetimeChecker

    def asserting_messages_calls(
        self,
        msg_id: str,
        node: Any,
        args: Any = None,
    ) -> None:
        """Assert messages for calls.

        Args:
            msg_id: message id.
            node: node to check.
            args: arguments to pass to the message.
        """
        with self.assertAddsMessages(
            testutils.MessageTest(
                msg_id=msg_id,
                node=node,
                args=args,
            ),
            ignore_position=True,
        ):
            self.checker.visit_call(node)

    def asserting_messages_attribute(
        self,
        msg_id: str,
        node: Any,
        args: Any = None,
    ) -> None:
        """Assert messages for assignments.

        Args:
            msg_id: message id.
            node: node to check.
            args: arguments to pass to the message.
        """
        with self.assertAddsMessages(
            testutils.MessageTest(
                msg_id=msg_id,
                node=node,
                args=args,
            ),
            ignore_position=True,
        ):
            self.checker.visit_attribute(node)

    def test_timedelta_without_kargs(self) -> None:
        """Test timedelta without keyword arguments."""
        call_node_1, call_node_2, call_node_3 = astroid.extract_node(
            """
        import datetime
        from datetime import timedelta, datetime
        timedelta(1) #@
        datetime.timedelta(1) #@
        datetime(1, 1, 1, 1, timezone.utc) #@
        """
        )
        self.asserting_messages_calls("datetime-timedelta-no-keyword-args", call_node_1)
        self.asserting_messages_calls("datetime-timedelta-no-keyword-args", call_node_2)
        self.asserting_messages_calls("datetime-timedelta-no-keyword-args", call_node_3)

    def test_timedelta_with_kargs(self) -> None:
        """Test timedelta with keyword arguments."""
        call_node_1, call_node_2, call_node_3, call_node_4 = astroid.extract_node(
            """
        import datetime
        from datetime import timedelta
        timedelta(seconds=1) #@
        datetime.timedelta(seconds=1) #@
        timedelta(0) #@
        datetime.timedelta(0) #@
        """
        )
        with self.assertNoMessages():
            self.checker.visit_call(call_node_1)
            self.checker.visit_call(call_node_2)
            self.checker.visit_call(call_node_3)
            self.checker.visit_call(call_node_4)

    def test_no_timezone_argument(self) -> None:
        """Test missing timezone arguments."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
        ) = astroid.extract_node(
            """
        import datetime
        from datetime import datetime
        datetime.now() #@
        datetime.fromtimestamp(1)  #@
        datetime()  #@
        datetime.astimezone()  #@
        """
        )
        self.asserting_messages_calls(
            "datetime-call-without-timezone", call_node_1, args=("now",)
        )
        self.asserting_messages_calls(
            "datetime-call-without-timezone", call_node_2, args=("fromtimestamp",)
        )
        self.asserting_messages_calls(
            "datetime-call-without-timezone", call_node_3, args=("datetime",)
        )
        self.asserting_messages_calls(
            "datetime-call-without-timezone", call_node_4, args=("astimezone",)
        )

    def test_passed_timezone_argument(self) -> None:
        """Test correctly passed timezone arguments."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
        ) = astroid.extract_node(
            """
        import datetime
        from datetime import datetime, timezone
        datetime.now(tz=timezone.utc) #@
        datetime.fromtimestamp(1, timezone.utc)  #@
        datetime(tzinfo=timezone.utc)  #@
        datetime.astimezone(tzinfo=timezone.utc)  #@
        """
        )
        with self.assertNoMessages():
            self.checker.visit_call(call_node_1)
            self.checker.visit_call(call_node_2)
            self.checker.visit_call(call_node_3)
            self.checker.visit_call(call_node_4)

    def test_no_naive_methods(self) -> None:
        """Test wrong naive method calls."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
            call_node_5,
        ) = astroid.extract_node(
            """
        import datetime
        from datetime import datetime
        datetime.today() #@
        datetime.utcnow() #@
        datetime.utcfromtimestamp(1)  #@
        datetime.utctimetuple()  #@
        datetime.time()  #@
        """
        )
        self.asserting_messages_calls(
            "datetime-naive-object-used", call_node_1, args=("today",)
        )
        self.asserting_messages_calls(
            "datetime-naive-object-used", call_node_2, args=("utcnow",)
        )
        self.asserting_messages_calls(
            "datetime-naive-object-used", call_node_3, args=("utcfromtimestamp",)
        )
        self.asserting_messages_calls(
            "datetime-naive-object-used", call_node_4, args=("utctimetuple",)
        )
        self.asserting_messages_calls(
            "datetime-naive-object-used", call_node_5, args=("time",)
        )

    def test_naive_objects_not_replaced(self) -> None:
        """Test naive objects without subsequent call to replace."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
            call_node_5,
            call_node_6,
        ) = astroid.extract_node(
            """
        import datetime
        datetime.datetime.min #@
        datetime.datetime.max #@
        datetime.datetime.fromisocalendar(1, 1, 1) #@
        datetime.datetime.fromordinal(1) #@
        datetime.time.min #@
        datetime.time.max #@
        """
        )
        self.asserting_messages_attribute(
            "datetime-missing-timezone-replace", call_node_1, args=("min",)
        )
        self.asserting_messages_attribute(
            "datetime-missing-timezone-replace", call_node_2, args=("max",)
        )
        self.asserting_messages_calls(
            "datetime-missing-timezone-replace", call_node_3, args=("fromisocalendar",)
        )
        self.asserting_messages_calls(
            "datetime-missing-timezone-replace", call_node_4, args=("fromordinal",)
        )
        self.asserting_messages_attribute(
            "datetime-missing-timezone-replace", call_node_5, args=("min",)
        )
        self.asserting_messages_attribute(
            "datetime-missing-timezone-replace", call_node_6, args=("max",)
        )

    def test_naive_objects_replaced(self) -> None:
        """Test naive objects without subsequent call to replace."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
            call_node_5,
            call_node_6,
        ) = astroid.extract_node(
            """
        import datetime
        datetime.datetime.min.replace(tzinfo=timezone.utc) #@
        datetime.datetime.max.replace(tzinfo=timezone.utc) #@
        datetime.datetime.fromisocalendar(1, 1, 1).replace(tzinfo=timezone.utc) #@
        datetime.datetime.fromordinal(1).replace(tzinfo=timezone.utc) #@
        datetime.time.min.replace(tzinfo=timezone.utc) #@
        datetime.time.max.replace(tzinfo=timezone.utc) #@
        """
        )
        with self.assertNoMessages():
            self.checker.visit_attribute(call_node_1)
            self.checker.visit_attribute(call_node_2)
            self.checker.visit_call(call_node_3)
            self.checker.visit_call(call_node_4)
            self.checker.visit_attribute(call_node_5)
            self.checker.visit_attribute(call_node_6)

    def test_naive_objects_falsely_replaced(self) -> None:
        """Test naive objects with subsequent call to replace but lacking timezone info."""
        (
            call_node_1,
            call_node_2,
            call_node_3,
            call_node_4,
            call_node_5,
            call_node_6,
        ) = astroid.extract_node(
            """
        import datetime
        datetime.datetime.min.replace(1) #@
        datetime.datetime.max.replace(1) #@
        datetime.datetime.fromisocalendar(1, 1, 1).replace(1) #@
        datetime.datetime.fromordinal(1).replace(year=1) #@
        datetime.time.min.replace(year=1) #@
        datetime.time.max.replace(year=1) #@
        """
        )
        self.asserting_messages_attribute(
            "datetime-missing-timezone-replace",
            list(list(call_node_1.get_children())[0].get_children())[0],
            args=("min",),
        )
        self.asserting_messages_attribute(
            "datetime-missing-timezone-replace",
            list(list(call_node_2.get_children())[0].get_children())[0],
            args=("max",),
        )
        self.asserting_messages_calls(
            "datetime-missing-timezone-replace",
            list(list(call_node_3.get_children())[0].get_children())[0],
            args=("fromisocalendar",),
        )
        self.asserting_messages_calls(
            "datetime-missing-timezone-replace",
            list(list(call_node_4.get_children())[0].get_children())[0],
            args=("fromordinal",),
        )
        self.asserting_messages_attribute(
            "datetime-missing-timezone-replace",
            list(list(call_node_5.get_children())[0].get_children())[0],
            args=("min",),
        )
        self.asserting_messages_attribute(
            "datetime-missing-timezone-replace",
            list(list(call_node_6.get_children())[0].get_children())[0],
            args=("max",),
        )

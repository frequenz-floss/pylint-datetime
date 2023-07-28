# License: MIT
# Copyright © 2023 Frequenz Energy-as-a-Service GmbH

"""Tests for the frequenz.pylint_datetime package."""
import pytest


# TODO(cookiecutter): Remove this function - when it isn't need anymore
def delete_me(*, blow_up: bool = False) -> bool:
    """Do stuff for demonstration purposes.

    Args:
        blow_up: If True, raise an exception.

    Returns:
        True if no exception was raised.

    Raises:
        RuntimeError: if blow_up is True.
    """
    if blow_up:
        raise RuntimeError("This function should be removed!")
    return True


def test_pylint_datetime_succeeds() -> None:  # TODO(cookiecutter): Remove
    """Test that the delete_me function succeeds."""
    assert delete_me() is True


def test_pylint_datetime_fails() -> None:  # TODO(cookiecutter): Remove
    """Test that the delete_me function fails."""
    with pytest.raises(RuntimeError, match="This function should be removed!"):
        delete_me(blow_up=True)

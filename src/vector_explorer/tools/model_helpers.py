from typing import Any, Callable, TypeVar

from django.db import models

from typing_extensions import ParamSpec

T = TypeVar("T", bound=models.Field)
P = ParamSpec("P")


def field(model_class: Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> Any:
    """
    Helper function to hide Field creation - but return Any
    So the type checker doesn't complain about the return type - and you can specify the
    Specify type of the item
    """
    return model_class(*args, **kwargs)

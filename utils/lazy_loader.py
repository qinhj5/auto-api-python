# -*- coding: utf-8 -*-
from typing import Any, Callable


class LazyLoader:
    def __init__(self, loader_func: Callable[[], Any]) -> None:
        """
        Initialize the LazyLoader with a loader function.

        Args:
            loader_func (Callable[[], Any]): A function that returns the object
            to be loaded when called.
        """
        self.loader = loader_func
        self._loaded = False
        self._obj = None

    def __call__(self) -> Any:
        """
        Call the loader function if the object is not loaded.

        Returns:
            Any: The loaded object.
        """
        if self._obj is None:
            self._obj = self.loader()
            self._loaded = True
        return self._obj

    def __getattr__(self, name: str) -> Any:
        """
        Get an attribute from the loaded object.

        Args:
            name (str): The name of the attribute to retrieve.

        Returns:
            Any: The value of the requested attribute from the loaded object.
        """
        return getattr(self(), name)

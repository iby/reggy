import datetime
import functools
import inspect
import sys
from typing import Callable, IO, Optional


class Tracer():
    """
    Provides `trace` decorator for class methods.
    """

    # Custom output stream, `sys.stderr` is used if not provided.
    out_stream: Optional[IO] = None

    # Default trace skip value.
    skip: bool = True

    # Default trace quiet value.
    quiet: bool = False

    @classmethod
    def trace(cls, skip: Optional[bool] = None, quiet: Optional[bool] = None):
        def decorator(decoratee: Callable):
            @functools.wraps(decoratee)
            def wrapper(*args, **kwargs):
                if cls.skip if skip is None else skip:
                    return decoratee(*args, **kwargs)

                verbose: bool = not (cls.quiet if quiet is None else quiet)

                # This is hacky, but does the job. We assume that decorator is used on class methods, but in theory can be applied
                # on any callable and class will be empty and we won't know who owns the decoratee.
                decoratee_cls: Optional[type] = cls.get_method_class(decoratee)
                owner: Optional[str] = decoratee_cls.__name__ if decoratee_cls is not None else None

                # When decoratee has a class the first passed argument would be `self`, so we drop it.
                cls.log_call(owner, decoratee, lambda: ', '.join([f'{arg!r}' for arg in (args if owner is None else args[1:])] + [f'{kw}={arg!r}' for kw, arg in kwargs.items()]), verbose)

                try:
                    value: any = decoratee(*args, **kwargs)
                    cls.log_exit(owner, decoratee, value, verbose)
                except Exception as exception:
                    cls.log_fail(owner, decoratee, exception, verbose)
                    raise

                return value

            return wrapper

        return decorator

    @classmethod
    def log(cls, message):
        print(f'{datetime.datetime.now().strftime("%Y.%m.%d-%H:%M:%S.%f")} {message}', file=cls.out_stream or sys.stderr)

    @classmethod
    def log_operation(cls, operation: str, owner: any, function: Callable, details: Optional[str]):
        cls.log('%s%s %s%s' % (f'{owner} ' or '', operation, function.__name__, details or ''))

    @classmethod
    def log_call(cls, owner: any, function: Callable, signature: Callable[[], str], verbose: bool = True):
        # Signature is a lambda that constructs function signature on demand to eliminate redundant overhead in non-verbose mode.
        cls.log_operation('CALL', owner, function, f' with signature: ({signature()})' if verbose else None)

    @classmethod
    def log_exit(cls, owner: any, function: Callable, result: any, verbose: bool = True):
        cls.log_operation('EXIT', owner, function, f' with result: {result!r}' if verbose else None)

    @classmethod
    def log_fail(cls, owner: any, function: Callable, exception: Exception, verbose: bool = True):
        cls.log_operation('FAIL', owner, function, f' with exception: {exception!r}' if verbose else None)

    @staticmethod
    def get_method_class(method) -> Optional[type]:
        """
        Returns method's class. All kudos to Yoel – https://stackoverflow.com/a/25959545/458356.
        """

        if inspect.ismethod(method):
            for cls in inspect.getmro(method.__self__.__class__):
                if cls.__dict__.get(method.__name__) is method:
                    return cls

            # Fallback to __qualname__ parsing.
            method = method.__func__

        if inspect.isfunction(method):
            cls = getattr(inspect.getmodule(method), method.__qualname__.split('.<locals>', 1)[0].rsplit('.', 1)[0])
            if isinstance(cls, type):
                return cls

        # Handle special descriptor objects.
        return getattr(method, '__objclass__', None)

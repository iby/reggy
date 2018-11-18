import re
from io import BytesIO, TextIOWrapper
from typing import Optional

import pytest
from pytest import mark

from reggy.test import StreamUtility
from reggy.tracer import Tracer


class Traceable():
    """
    Test dummy.
    """

    @Tracer.trace()
    def foo(self, p1: str, p2: Optional[str]) -> str:
        if not p1:
            raise Exception()

        return 'SUCH FOO!'


__tracer_test_data = [

    # Trace verbosely.
    [False, False, '\n'.join([
        'Traceable CALL foo with signature: (\'bar\', \'baz\')',
        'Traceable EXIT foo with result: \'SUCH FOO!\'',
        'Traceable CALL foo with signature: (\'\', p2=\'baz\')',
        'Traceable FAIL foo with exception: Exception()'
    ])],

    # Trace quietly.
    [False, True, '\n'.join([
        'Traceable CALL foo',
        'Traceable EXIT foo',
        'Traceable CALL foo',
        'Traceable FAIL foo'
    ])],

    # Don't trace with verbose mode on.
    [True, False, ''],

    # Don't trace with verbose mode off.
    [True, True, '']
]


@mark.parametrize(['skip', 'quiet', 'expected_result'], __tracer_test_data)
def test_tracer(skip: bool, quiet: bool, expected_result: str):
    Tracer.out_stream = TextIOWrapper(BytesIO(), line_buffering=True)

    traceable = Traceable()
    Tracer.skip = skip
    Tracer.quiet = quiet

    traceable.foo('bar', 'baz')
    with pytest.raises(Exception):
        traceable.foo('', p2='baz')

    result = StreamUtility.data(Tracer.out_stream).strip()

    # Remove timestamps for easier assertions.
    result = re.sub(r'\d\d\d\d\.\d\d\.\d\d-\d\d:\d\d:\d\d\.\d\d\d\d\d\d ', '', result)

    assert result == expected_result

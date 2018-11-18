from io import BytesIO, TextIOWrapper
from typing import IO, Optional, Tuple

from pytest import mark

from reggy.cli import Cli
from reggy.test import StreamUtility

Streams = Tuple[IO, IO, IO]
Outputs = Tuple[str, str, str]


def stream(data: Optional[str] = None, isatty: bool = False) -> IO:
    """
    Constructs a new stream mock object with the specified data written into it and custom `isatty` value.
    """

    stream: IO = TextIOWrapper(BytesIO(), line_buffering=True)
    stream.isatty = lambda: isatty

    # Write data and make sure stream is ready to be read.
    stream.write(data or '')
    stream.flush()
    stream.seek(0)

    return stream


def streams(in_data: Optional[str] = None, is_in_tty: bool = False, is_out_tty: bool = False, is_err_tty: bool = False) -> Streams:
    """
    Constructs in, out and err streams with the given configuration.
    """

    in_stream: IO = stream(data=in_data or '', isatty=is_in_tty)
    out_stream: IO = stream(isatty=is_out_tty)
    err_stream: IO = stream(isatty=is_err_tty)
    return (in_stream, out_stream, err_stream)


class PatternTestCase:
    """
    Represents a data set for pattern testing.
    """

    def __init__(self, pattern: str, matches: [str], mismatches: [str]):
        self.pattern = pattern
        self.matches = matches
        self.mismatches = mismatches

    pattern: str
    matches: [str]
    mismatches: [str]

    def input(self):
        """Input stream text for testing."""
        return '\n'.join(self.matches + self.mismatches)

    def output(self):
        """Expected output stream text."""
        return '\n'.join(self.matches) + '\n'


__cli_run_test_data = [

    # Simple pattern.
    PatternTestCase('foo %{0} is a %{1}', [
        'foo blah is a bar',
        'foo blah is a very big boat'
    ], [
        'foo blah is bar',
        'foo blah',
        'foo blah is'
    ]),

    # Simple pattern with space limit modifier.
    PatternTestCase('foo %{0} is a %{1S0}', [
        'foo blah is a bar'
    ], [
        'foo blah is a very big boat',
        'foo blah is bar',
        'foo blah',
        'foo blah is'
    ]),

    # Ambiguous pattern with space limit modifier.
    PatternTestCase('the %{0S1} %{1} ran away', [
        'the big brown fox ran away'
    ], [
        'the big fox ran away'
    ]),

    # Ambiguous pattern with greedy modifier.
    PatternTestCase('bar %{0G} foo %{1}', [
        'bar foo bar foo bar foo bar foo'
    ], [
        'bar foo bar bar bar bar bar foo'
    ])
]


@mark.parametrize('case', __cli_run_test_data)
def test_cli_run(case: PatternTestCase):
    """
    Cli must process input and print all matched lines into the out stream.
    """

    (in_stream, out_stream, err_stream) = streams(case.input())
    code: int = Cli().run(['…', case.pattern], in_stream, out_stream, err_stream)

    assert code == 0
    assert StreamUtility.data(out_stream) == case.output()


@mark.parametrize(['is_in_tty', 'is_out_tty'], [[False, False], [True, False], [False, True], [True, True]])
def test_cli_run_is_tty_friendly(is_in_tty: bool, is_out_tty: bool):
    """
    Cli must use user-friendly style when streams are tty-capable.
    """

    (in_stream, out_stream, err_stream) = streams('\n'.join(['foo', 'foo bar']), is_in_tty=is_in_tty, is_out_tty=is_out_tty)
    code: int = Cli().run(['…', 'foo %{0}'], in_stream, out_stream, err_stream)

    assert code == 0

    out_stream_data = StreamUtility.data(out_stream)

    string = 'Enter the text to match and finish with entering an empty line or the EOF character'
    assert string in out_stream_data if is_in_tty else string not in out_stream_data

    string = 'Matched 1 lines out of total 2'
    assert string in out_stream_data if is_out_tty else string not in out_stream_data


@mark.parametrize('argv', [[], ['foo', 'bar']])
def test_cli_run_check_input_arguments(argv):
    """
    Cli must fail if the number of arguments is not equal to one.
    """

    (in_stream, out_stream, err_stream) = streams()
    code: int = Cli().run(['…'] + argv, in_stream, out_stream, err_stream)

    assert code == 1

    err_stream_data = StreamUtility.data(err_stream)
    string = 'The program expects exactly one argument'

    assert string in err_stream_data

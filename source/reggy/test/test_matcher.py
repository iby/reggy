from pytest import mark

from reggy.matcher import Matcher

__match_test_data = [

    # Must handle simple patterns.
    ['foo %{0} baz %{1}', 'foo bar baz qux', {0: ['bar'], 1: ['qux']}],
    ['foo %{0} baz %{1} fex', 'foo bar baz qux fex', {0: ['bar'], 1: ['qux']}],

    # Must match non-greedily when patterns are ambiguous.
    ['foo %{0} baz %{1}', 'foo bar baz bar baz bar baz qux', {0: ['bar'], 1: ['bar baz bar baz qux']}],

    # Must match greedily when the patterns are greedy.
    ['foo %{0G} baz %{1}', 'foo bar baz bar baz bar baz qux', {0: ['bar baz bar baz bar'], 1: ['qux']}],
    ['foo %{0G} baz %{1G}', 'foo bar baz bar baz bar baz qux', {0: ['bar baz bar baz bar'], 1: ['qux']}],
    ['foo %{0} baz %{1G}', 'foo bar baz bar baz bar baz qux', {0: ['bar'], 1: ['bar baz bar baz qux']}],

    # Must match correct number of whitespaces when the pattern has the explicit whitespace specifier.
    ['foo %{0S2} baz %{1}', 'foo bar baz bar baz bar baz qux', {0: ['bar baz bar'], 1: ['bar baz qux']}],
    ['foo %{0S2} baz %{1}', 'foo bar\tbaz\xA0bar baz bar baz qux', {0: ['bar\tbaz\xA0bar'], 1: ['bar baz qux']}],  # Tab character, space and non-breaking space are also whitespaces.
    ['foo %{0S3} baz %{1}', 'foo \t \xA0 baz bar baz qux', {0: ['\t \xA0'], 1: ['bar baz qux']}],  # Continuous whitespaces is also a valid case.

    # Must handle patterns with unordered token rule indices.
    ['foo %{1} baz %{2} fex %{0}', 'foo bar baz qux fex pao', {1: ['bar'], 2: ['qux'], 0: ['pao']}],

    # Must match and handle patterns with arbitrary repeating rule indices.
    ['foo %{5} baz %{3} fex %{3} nit %{5}', 'foo bar baz qux fex pao nit meh', {5: ['bar', 'meh'], 3: ['qux', 'pao']}],
]


@mark.parametrize(['pattern', 'string', 'result'], __match_test_data)
def test_match(pattern: str, string: str, result: {int: [str]}):
    """
    Matcher can match tokens in the string using valid patterns.
    """

    assert Matcher().match(pattern, string) == result


def test_match_with_invalid_input():
    """
    Matcher must not fail with invalid input.
    """

    matcher: Matcher = Matcher()

    # Empty pattern must not result in an error…
    assert matcher.match('', '') is None

    # …so is pattern without a token capture.
    assert matcher.match('foo', 'foo') == {}

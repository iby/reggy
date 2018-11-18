import re
from typing import Dict, List, Match, Optional, Pattern

from reggy.tracer import Tracer


class Matcher:

    @Tracer.trace()
    def match(self, pattern: str, string: str) -> Optional[Dict[int, List[str]]]:
        """
        Finds tokens in the string matched with the given pattern and returns them organized by rule index. For example:

            match('foo %{0} is a %{1}', 'foo blah is a bar')                # {0: ['blah], 1: ['bar']}
            match('foo %{0} baz %{1}', 'foo bar baz bar baz bar baz qux')   # {0: ['bar'], 1: ['bar baz bar baz qux']}
            match('foo %{0G} baz %{1}', 'foo bar baz bar baz bar baz qux')  # {0: ['bar baz bar baz bar'], 1: ['qux']}
            match('foo %{0S2} baz %{1}', 'foo bar baz bar baz bar baz qux') # {0: ['bar baz bar'], 1: ['bar baz qux']}
            match('foo %{1} baz %{2} fex %{0}', 'foo bar baz qux fex pao')  # {1: ['bar'], 2: ['qux'], 0: ['pao']}

        :param pattern: A pattern is a text string, delimited with token capture sequences which identify the variable text extracted from
            the message. A token capture sequence is represented as a percent sign '%' character followed by a '{' character, non-negative
            integer, an optional token capture modifier, and finally a '}' character. The non-negative integer denotes the index into the token
            list associate with the rule to which the pattern belongs. A simple token capture sequence would be written as "%{0}" and "%{25}",
            and will capture any amount of text which occurs between the adjacent text literals.
            
            A token capture modifier specifies special handling of the token capture in order to differentiate otherwise ambiguous patterns. There
            are two types of token capture modifiers: space limitation (S#) and greedy (G). A space limitation modifier specifies a precise number
            of whitespace characters which must be appear between text literals in order to match the associated token capture sequence. For example,
            the token capture sequence %{1S2} specifies token one, with a space limitation modifier of exactly two spaces.

            The whitespace modifier is intended to be used to limit possibly ambiguous matches, as in the example above, or in cases where two
            token capture sequences occur adjacent within a pattern without intervening literal text.

            A greedy token capture modifier specifies special handling of the token capture in order to differentiate patterns which are ambiguous
            due to repetitions of token value text that also occurs in the literal text of the pattern. The greedy capture modifier captures
            as mush as possible text between preceding and following string literals.

        :param string: A string to match against the pattern.

        :return: Dictionary containing all found matches organized by the token pattern rule index or `None` if pattern is empty or otherwise
            invalid, or no matches are found.
        """

        # No pattern – no profit.
        if not pattern:
            return None

        (regex, rule_indices) = self.__parse_regex(pattern)
        match: Match = regex.fullmatch(string)

        # No match – no profit.
        if match is None:
            return None

        tokens: {int: [str]} = {}

        # Make sure match contains groups.
        if match.lastindex is not None:
            for i in range(match.lastindex):
                # Not forgetting that zero-group represents the full match and the one we're interested in would be +1…
                tokens.setdefault(rule_indices.pop(0), []).append(match[i + 1])

        return tokens

    def __parse_regex(self, pattern: str) -> (Pattern, [int]):
        """
        Parses the given pattern string into a compiled regex pattern object and a mapping between capture group and rule indices.
        """

        # Find patterns. Pattern consists of a rule index and optional space limit or greediness flag.
        matches = list(re.finditer('%{(?P<rule>\\d+)(?:S(?P<space_limit>\\d+)|(?P<is_greedy>G))?}', pattern))

        # If didn't find any patterns convert the whole string into a plain regex.
        if not matches:
            return (re.compile(re.escape(pattern)), [])

        raw_pattern: str = pattern
        regex_pattern: str = '^'
        index: int = 0

        # Map between matched groups and pattern rule indices.
        match_group_rule_index_map: [int] = []

        # Iterate over all matches and construct regex patterns merging them with adjacent literals (on the left) into the final result.
        for match in matches:
            rule = match['rule']
            space_limit = match['space_limit']
            is_greedy = match['is_greedy']

            regex_pattern += re.escape(raw_pattern[index:match.start()])

            if space_limit is None:
                # Simple any non-empty text match.
                regex_pattern += '(.+'
            else:
                # Match text with exact number of whitespace within it.
                regex_pattern += f'((?:\\S*\\s){{{space_limit}}}\\S*?'

            # Use non-greedy operator unless it's explicitly requested.
            if space_limit is None and is_greedy is None:
                regex_pattern += '?'

            # Finalize the regex group and map the match group index to the rule index.
            regex_pattern += ')'
            match_group_rule_index_map.append(int(rule))

            index = match.end()

        # Close the final pattern.
        regex_pattern += re.escape(raw_pattern[index:]) + '$'

        return (re.compile(regex_pattern), match_group_rule_index_map)

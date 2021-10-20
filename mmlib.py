#!/usr/bin/env python3

from collections import namedtuple
from itertools import product
import copy


def mm_tokens(bs):
    in_comment = False
    i, l = 0, 0  # bs[i:i+l] is the next token, so far
    for c in bs:
        if c <= 32:  # = whitespace, in a correct .mm database file
            if l > 0:
                result = bs[i:i+l]
                if result == b'$(':
                    in_comment = True
                elif result == b'$)':
                    in_comment = False
                yield result
            if in_comment and c == ord('\n'):
                yield bs[i+l:i+l+1]
            i, l = i+l+1, 0  # make next token empty
        else:
            l = l+1  # extend next token
    assert i+l == len(bs)
    if i < i+l:
        yield bs[i:i+l]


MMStatement = namedtuple(
    'MMStatement', ['type', 'label', 'tokens', 'expression', 'proof'])


def mm_statements(bs):
    it = mm_tokens(bs)

    def next_until(terminator):
        result = []
        while True:
            try:
                c = next(it)
            except StopIteration:
                raise Exception("Terminator %s not found" % terminator)
            if c == terminator:
                break
            result.append(c)
        return result

    while True:
        try:
            c = next(it)
        except StopIteration:
            break
        label = None
        if c[0] not in b'$':
            # c is the label for this statement, in a correct .mm database file
            label = c
            try:
                c = next(it)
            except StopIteration:
                raise Exception("Label %s then EOF" % label)
        d = c[1]
        if d in b'(':
            try:
                while next(it) != b'$)':
                    pass
            except StopIteration:
                raise Exception("Unterminated comment")
        elif d in b'{}':
            yield MMStatement(d, None, None, None, None)
        elif d in b'cdv':
            yield MMStatement(d, label, set(next_until(b'$.')), None, None)
        elif d in b'p':
            yield MMStatement(d, label, None, next_until(b'$='), next_until(b'$.'))
        elif d in b'aef':
            yield MMStatement(d, label, None, next_until(b'$.'), None)
        else:
            assert False


MMInferenceRule = namedtuple(
    'MMInferenceRule', ['dollards', 'types', 'hypotheses', 'conclusion'])


def mm_assertions(bs):
    State = namedtuple('State', ['dollards', 'dollares', 'dollarfs'])

    states = []
    state = State(dollards=set(), dollares=[], dollarfs={})

    it = mm_statements(bs)
    while True:
        try:
            s = next(it)
        except StopIteration:
            break
        if s.type in b'{':
            states.append(state)
            state = copy.deepcopy(state)
        elif s.type in b'}':
            state = states.pop()
        elif s.type in b'f':
            state.dollarfs[s.expression[1]] = (s.expression[0], s.label)
            yield (b' '.join(s.expression),  # HACK! to avoid using different labels for same typing; should really be s.label,
                   s.type, MMInferenceRule(
                dollards=frozenset(),
                types=[],
                hypotheses=[],
                conclusion=s.expression))
        elif s.type in b'e':
            state.dollares.append(s.expression)
        elif s.type in b'd':
            for v, w in product(s.tokens, s.tokens):
                if v != w:
                    state.dollards.add(frozenset([v, w]))
        elif s.type in b'ap':
            active_vars = frozenset(v for v in state.dollarfs.keys() if any(
                v in h for h in state.dollares) or v in s.expression)
            # TODO: add 'database order' information for $f/$e statements?
            yield (s.label, s.type, MMInferenceRule(
                dollards=frozenset(r for r in state.dollards for (
                    a, b) in (r,) if a in active_vars and b in active_vars),
                types=[(l, [t, v]) for v, (t, l)
                       in state.dollarfs.items() if v in active_vars],
                hypotheses=state.dollares,
                conclusion=s.expression))
        elif s.type in b'cv':
            # we don't need $c, $v in a correct .mm database file
            pass
        else:
            assert False, "unknown s.type: %s ('%s')" % (
                str(s.type), chr(s.type))

#!/usr/bin/env python3

import copy


def find_substitutions(variables, source, target, sep=b' '):

    # performance optimization for special case
    if not variables:
        ### print('find_substitutions (opt)', variables, source, target)
        if len(source) == len(target) and all(x == y for x, y in zip(source, target)):
            yield {}
        return

    def findss(vars, constss, tgt):
        ### print(f"calling findss({vars}, {constss}, {tgt})")
        # assert len(vars) == len(constss)
        if len(vars) == 0:
            if tgt == b'':
                # print('HERE')
                yield {}
            return
        for i in range(len(tgt)):
            if tgt.startswith(constss[0], i):
                ### print(f'found "{constss[0]}" in "{tgt}" at {i}')
                for sb in findss(vars[1:], constss[1:], tgt[i+len(constss[0]):]):
                    if vars[0] in sb.keys():
                        if sb[vars[0]] == tgt[:i].split(sep):
                            yield sb
                    else:
                        sb[vars[0]] = tgt[:i].split(sep)
                        yield sb

    # split source on variables
    source_vars = []
    source_constss = []
    consts = [b'']
    for s in source:
        if s in variables:
            consts.append(b'')
            source_constss.append(sep.join(consts))
            consts = [b'']
            source_vars.append(s)
        else:
            consts.append(s)
    consts.append(b'')
    source_constss.append(sep.join(consts))
    # assert len(source_vars) + 1 == len(source_constss)

    # create target
    target_string = sep.join((b'', *target, b''))

    ### print('find_substitutions', source_vars, source_constss, target_string)

    # trivial case: part before first variable should match first part of target_string
    if not target_string.startswith(source_constss[0]):
        return
    # recursively handle the rest
    for sb in findss(source_vars, source_constss[1:], target_string[len(source_constss[0]):]):
        yield sb


def find_substitutions_orig(variables, source, target):
    """
    Generates all variable -> expression dicts which changes 'source' to 'target'
    """
    source_pos = 0
    target_pos = 0
    substitution = {}
    while True:
        # Either find source[source_pos] at target[target_pos] and move on,
        # or don't find it and backtrack (and try a longer var match, if applicable).
        backtrack = False
        if source_pos == len(source):
            # find end-of-list at target_pos
            if target_pos == len(target):
                # found...
                yield copy.deepcopy(substitution)
                # ...but we backtrack to find possibly more
                # print('YIELDING RESULT!')
            # print('backtrack at end of source')
            backtrack = True
        else:
            src = source[source_pos]
            if src in variables:
                # find anything matching this variable
                if src in substitution:
                    orig_target_pos = target_pos
                    for c in substitution[src]:
                        if target_pos < len(target) and target[target_pos] == c:
                            # found constant, move on
                            target_pos += 1
                        else:
                            target_pos = orig_target_pos
                            # print('backtrack at not found duplicate for', src)
                            backtrack = True
                            break
                    else:  # no break
                        source_pos += 1
                else:
                    substitution[src] = []
                    source_pos += 1
                    # ...and the longer matches will be found on backtracking
            else:
                # find anything matching this constant
                if target_pos < len(target) and target[target_pos] == src:
                    # found constant, move on
                    source_pos += 1
                    target_pos += 1
                else:
                    # print('backtrack at not found constant', src)
                    backtrack = True
        while backtrack:
            while True:
                # print('state on backtrack:', source_pos, 'read from', source, 'AND', target_pos, 'read from', target, 'SUBST', substitution)
                if source_pos == 0:
                    # print('DONE!')
                    return  # we're done!
                source_pos -= 1
                src = source[source_pos]
                if src in variables:
                    if src not in source[:source_pos-1]:
                        break
                    # print('push back match for variable', src)
                    target_pos -= len(substitution[src])
                    # assert 0 <= target_pos < len(target)
                    # assert substitution[src] == target[target_pos:target_pos+len(substitution[src])] # sanity check
                else:
                    # print('push back constant', src)
                    target_pos -= 1
                    # assert src == target[target_pos] # sanity check
            if target_pos < len(target):
                source_pos += 1
                substitution[src] += [target[target_pos]]
                target_pos += 1
                backtrack = False
            else:
                target_pos -= len(substitution[src])
                # assert 0 <= target_pos < len(target)
                del substitution[src]


def assert_find_substitutions(*, variables, source, target, expected_substitutions):
    source = source.encode('ASCII').split()
    source_vars = variables.encode('ASCII').split()
    target = target.encode('ASCII').split()

    it = find_substitutions(source_vars, source, target)
    for s in expected_substitutions:
        try:
            x = next(it)
        except StopIteration:
            assert False, f'expecting substitution {s}'
        y = {k.encode('ASCII'): v.encode('ASCII').split()
             for k, v in s.items()}
        assert x == y, f'expecting {x} == {y} (s = {s})'
    try:
        next(it)
        assert False
    except StopIteration:
        pass


def test_none():
    assert_find_substitutions(
        variables='',
        source='wff T.',
        target='wff F.',
        expected_substitutions=[
        ])


def test_empty():
    assert_find_substitutions(
        variables='',
        source='wff T.',
        target='wff T.',
        expected_substitutions=[
            {}
        ])


def test_simple():
    assert_find_substitutions(
        variables='ps',
        source='wff ps',
        target='wff ph',
        expected_substitutions=[
            {'ps': 'ph'}
        ])


def test_duplicate_simple():
    assert_find_substitutions(
        variables='ph',
        source='wff ( ph ph )',
        target='wff ( false I think false I think )',
        expected_substitutions=[
            {'ph': 'false I think'},
        ])


def test_duplicate():
    assert_find_substitutions(
        variables='ph ps',
        source='wff ( ph -> ps )',
        target='wff ( ph -> ( ps -> ph ) )',
        expected_substitutions=[
            {'ph': 'ph', 'ps': '( ps -> ph )'},
            {'ph': 'ph -> ( ps', 'ps': 'ph )'},
        ])

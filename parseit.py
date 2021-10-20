#!/usr/bin/env python3
"""Metamath formula parser based on $a TOP ... $. axioms

Usage:
  ./r [-i <file>]
  ./r -h

Options:
  -h, --help  Show this message and exit.
  -i <file>, --input <file>  The .mm file to parse [default: set.mm]
"""
from type_docopt import docopt

import mmlib
from collections import defaultdict
import findsubst
from itertools import product
import json

"""
Exception: multiple parse trees found: at least '
('TOP.turnstile', (('wi', (('wor', (('cY', ()), ('crpss', ()))), ('wor', (('cra', (('wcel', (('cdif', (('cA.wceq', ()), ('cv', (('vu', ()),)))), ('cY', ()))), ('vu', ()), ('cpw', (('cA.wceq', ()),)))), ('crpss', ()))))),))
' and '
('TOP.turnstile', (('wi', (('wor', (('cY', ()), ('crpss', ()))), ('wor', (('cra', (('wcel', (('cdif', (('cA.wceq', ()), ('cv', (('vu', ()),)))), ('cY', ()))), ('vu', ()), ('cpw', (('wcel.cA', ()),)))), ('crpss', ()))))),))
'
"""


def parse(expression, top_kind, asss):
    """
    Find the one proof of [top_kind, *expression] using assertions from asss : kind -> (name -> assertion)
    """
    result = None
    for p in find_proofs((top_kind, *expression), asss):
        if result:
            raise Exception(
                "multiple parse trees found: at least '%s' and '%s'" % (result, p))
        result = p
        break
    if not result:
        raise Exception("no parse tree found")
    return result


def find_proofs(expression, asss):
    yielded_once = False
    #print('>looking at:', expression)
    kind = expression[0]
    for name, assertion in asss[kind].items():
        #print('>>trying:', name, assertion.conclusion)
        assert len(assertion.hypotheses) == 0, (
            "short-cut assumption that a syntax $a has no $e expected to hold for assertion %s: %s" % (name, assertion))
        assertion_vars = [v for l, (t, v) in assertion.types]
        assert len(assertion.types) > 0 or assertion_vars == []
        for substitution in findsubst.find_substitutions(assertion_vars, assertion.conclusion, expression):
            # we found a possible proof step
            #print('s', substitution)
            subproofss = (
                find_proofs((t, *substitution[v]), asss)
                for l, (t, v) in assertion.types
            )
            for subproofs_combination in product(*subproofss):
                #print('=', name, subproofs_combination)
                yield (name, *subproofs_combination) if subproofs_combination else name
                return
                assert not yielded_once
                yielded_once = True
        #print('<<tried :', assertion.conclusion)
    #print('<looked at :', expression)
    return

if __name__ == '__main__':
    from type_docopt import docopt
    arguments = docopt()

    with open(arguments['--input'], 'rb') as f:
        setmm = f.read()
        assertions_by_kind = defaultdict(dict)
        for nr, (name, typ, assertion) in enumerate(mmlib.mm_assertions(setmm)):
            #print(name, assertion.conclusion)
            t = assertion.conclusion[0]
            once = True
            while once:
                once = False
                if t == b'TOP':
                    # don't parse
                    continue
                if typ == ord(b'f'):
                    # don't parse $f statements
                    continue
                if typ == ord(b'a') and chr(t[0]).upper() != chr(t[0]):
                    # don't parse $a statements whose typecode starts with lowercase letter
                    continue
                try:
                    if nr % 1 == 0:
                        print(nr, ':', str(name, 'ASCII'), str(
                            b' '.join(assertion.conclusion), 'ASCII'))
                        parse_tree = parse(assertion.conclusion,
                                           b'TOP', assertions_by_kind)
                    if nr % 1 == 0:
                        print(nr, ':', '-->', json.dumps(parse_tree,
                              indent=None, default=lambda x: str(x, 'ASCII')))
                        print()
                except Exception:
                    print(name, assertion.conclusion)
                    import traceback
                    traceback.print_exc()
                    import sys
                    sys.exit(1)
            if typ in (ord(b'a'), ord(b'f')):
                assertions_by_kind[t][name] = assertion
                if False:
                    print('using:', t, name, assertion)

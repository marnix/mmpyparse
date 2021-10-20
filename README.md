**Warning: Hacked-up code ahead.**  (But it seems to work...)

# What it does

This demonstrates an idea which I posted about several times
on the Metamath mailing list metamath@googlegroups.com.
Here are links into the Google Groups archive:

- [Automated Metamath ambiguity checking](https://groups.google.com/g/metamath/c/DrXCGlyj6_w/m/pHGsht_VBwAJ)
- [New marker: "this database is unambiguous"](https://groups.google.com/g/metamath/c/wtZhLZT6IpI/m/NbUBsn9kBAAJ)
- [Minimalist Metamath](https://groups.google.com/g/metamath/c/8QJqoFgMXhE/m/07Q60TflBwAJ)

The parsing algorithm assumes there is a `... $a TOP xyzzy ... $.` axiom for each typecode.
It works as follows:

* For every statement expression like `|- x y z z y`,
* find the unique proof for `TOP |- x y z z y`
* which uses only the non-`$p` statements that are in scope for that statement.
* Skip (that is, don't try to parse) syntax-related statements:
    * `$f` statements;
    * statements whose expression starts with `TOP`;
    * `$a` statements whose typecode starts with a lowercase letter.

Each such proof is the parse tree for that statement's expression.

As far as I can see, this works for set.mm and iset.mm.


# How to use

Make sure you have a recent Python version.
(Tested with 3.8, 3.3+ might work.)

Download a Metamath .mm file, like set.mm.

Extend that .mm file with a `... $a TOP xyzzy ... $.` axiom for each typecode,
for example by applying set.mm.patch.

Run `parseit`, for example `./parseit -i set.mm`.
(This creates a virtual environment.)

Enjoy the parsed formulas rolling over your screen.
(And observe how statements like `opelopabt`
```
|- ( ( A. x A. y ( x = A -> ( ph <-> ps ) ) /\ A. x A. y ( y = B -> ( ps <-> ch ) ) /\ ( A e. V /\ B e. W ) ) -> ( <. A , B >. e. { <. x , y >. | ph } <-> ch ) )
```
make it sweat...)

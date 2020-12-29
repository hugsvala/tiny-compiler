# tiny-compiler

A small compiler written in Python, for a very small subset of C.

While this compiler has no practical usage, its purpose have been to learn more about some concepts of compiler design with regards to the front-end phases. In particular I have been curious about implementing a front-end without using any lexer/parser generators, hence the very small subset of C that can be compiled.

The parser is LL(1), implemented as recursive descent. Apart from building the parse tree, the parser.py module also define functions for building the abstract syntax tree. Node classes in the ast are defined in the abstract_syntax_tree.py module.  

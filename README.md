# tiny-compiler

A small compiler written in Python, for a very small subset of C.

While this compiler has no practical usage, its purpose have been to learn more about some concepts of compiler design with regards to the front-end phases. In particular I have been curious about implementing a front-end without using any lexer/parser generators, hence the very small subset of C that can be compiled.

The parser is LL(1), implemented as recursive descent. Apart from building the parse tree, the parser.py module also define functions for building the abstract syntax tree. Node classes in the ast are defined in the abstract_syntax_tree.py module.  

While the compiler only knows about one type, namely integers, the type_checker is actually quite busy. Besides making sure that variables are declared before they are used, complain about redeclarations and make sure that the function calls are using the correct number of arguments. The type_checker also keeps track of the number of local variables, and assign to them a local_index which the code generator can use to properly address the variables on the stack.

The intermediate language is quite simple, and also quite pointless. Although sometimes it proved useful. Mostly for catching bugs in other parts of the compiler.

The code generator was the most fun, and perilous, part of the compiler, though it is not yet complete. While it is able to generate code for most of the tasks I had in mind there is still one thing that it does not achieve, recursion.


Known issues:
Currently the lexer treats negative numbers as a token, this leads to bad parsing for input such as: 2-1 since the parser will fail to recognize the expression as 2 - 1. Initially this was handled by the lexer simply treating all numbers as positive, and then the parser would handle the sign. I might go back to this solution if I don't find a better one.

The parse tree seem to be a bit confused by some longer expressions (such as: 1 * 2 - 3 + 4 * 5). While it is possible to get the correct expression by using parentheses, I find it quite annoying. I've checked the production rules against two references which I trust, and I can't find a problem with it. It might be that this is an issue inherent to LL(1), or it might be a bug in the parser. It might also be that I need some more elaborate way of deciding on precedence.

Recursion. Currently the backend does not like it very much.

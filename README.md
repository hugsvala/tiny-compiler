# tiny-compiler

A small compiler written in Python, for a very small subset of C.

While this compiler has no practical usage, its purpose has been to learn more about some concepts of compiler design with regards to the front-end phases. In particular I have been curious about implementing a front-end without using any lexer/parser generators, hence the very small subset of C that can be compiled.

The parser is LL(1), implemented as recursive descent. Apart from building the parse tree, the parser.py module also define functions for building the abstract syntax tree. Node classes in the ast are defined in the abstract_syntax_tree.py module.  

While the compiler only knows about one type, namely integers, the type_checker is actually quite busy. Besides making sure that variables are declared before they are used, complain about redeclarations and make sure that function calls are using the correct number of arguments. The type_checker also keeps track of the number of local variables, and assign to them a local_index which the code generator can use to properly address the variables on the stack.

The intermediate language is quite simple, and also quite pointless, although sometimes it proved useful. Mostly for catching bugs in other parts of the compiler.

The code generator was the most fun, and perilous, part of the compiler. The generated code is highly unoptimized. For example, there are some jump instructions that could be avoided by inverting the branch conditions. Arguments are pushed onto the stack rather than using registers.

The compiler has a built in function called "print" which takes as argument an integer to print. See output.s for an example.  

Currently the lexer treats negative numbers as a token, this leads to bad parsing for input such as: 2-1 since the parser will fail to recognize the expression as 2 - 1. Initially this was handled by the lexer simply treating all numbers as positive, and then the parser would handle the sign. I might go back to this solution if I don't find a better one.

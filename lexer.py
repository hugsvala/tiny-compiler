###============================###
# Lexer for a small subset of C. #
###============================###
import re
import sys

# This pattern define the current subset of the language. Currently it only
# operates on integers.
language = '[a-zA-Z][a-zA-Z0-9_]*|-?[0-9]+|[,;(){}+\-*/=!<>]'
id = '[a-zA-Z][a-zA-Z0-9_]*'
literal = '-?[0-9]+'
valid_tokens = { "int" : "int", "return" : "return", "if" : "if",
                 "else" : "else", "(" : "left_paren", ")" : "right_paren",
                 "{" : "left_bracket", "}" : "right_bracket", ";" :
                 "separator", "," : "comma", "<" : "less_than",
                 ">" : "greater_than", "+" : "add", "-" : "sub",
                 "*" : "mul", "/" : "div", "=" : "equals", "!" : "not"}

# Get the input file from command line argument.
with open(sys.argv[-1], 'r') as file:
    inputStr = file.read()

# Tokenize the string.
def scan():
    words = re.findall(language, inputStr)
    tokens = []

    # Once the input is scanned, we loop through and evaluate the result.
    for w in words:
        if m := re.match(literal, w):
                tokens.append(("literal", m.group(0)))
        elif valid_tokens.get(w):
            tokens.append((valid_tokens[w], w))
        elif m := re.match(id, w):
                tokens.append(("id", m.group(0)))

    tokens.append(("eof", "$"))
    return tokens

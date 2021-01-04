###======================================================================###
# LL(1) parser for a small subset of C, implemented as a recursive descent #
# parser, see productions.txt for details regarding productions.           #
###======================================================================###
from itertools import count
from collections import deque
import abstract_syntax_tree as ast
import codegen
import ir_instr
import lexer
import sys
import type_checker

# Representation of a node in the parse tree.
# sym refer to a terminal or nonterminal symbol.
# id is a unique integer used for debugging purposes.
# succs is a list of successor nodes in the parse tree.
# name represents for example a variable name (parameter) or a function name.
# val represents for example a literal value or variable name (argument).
class Node:
    _node_id = count(0, 1)
    def __init__(self, symbol):
        self.sym = symbol
        self.id = next(self._node_id)
        self.succs = []
        self.name = None
        self.val = None

    def add_succ(self, succ):
        self.succs.append(succ)

# Get the tokens from the lexer.
tokens = lexer.scan()

# Use a generator to count the next token.
next_tok = count(0, 1)
def next_token():
    return tokens[next(next_tok)]

# Report an error if expecting a token but recieve another. Exit program.
def report_error(tok):
    print("Erroneous parse!", tok)
    sys.exit()

# The following functions parse the language defined in productions.txt.
# Parsing a terminal symbol results in a call to next_token().
# Each function also return the corresponding subtree in the parse tree.
def parse_program(tok, prog):
    if tok[0] == "int":
        tok, parse = parse_def(tok)
        prog.add_succ(parse)
        tok, prog = parse_program(tok, prog)
    elif tok[0] == "eof":
        return tok, prog
    else:
        report_error(tok)
    return tok, prog

def parse_def(tok):
    if tok[0] == "int":
        tok = next_token()
        if tok[0] == "id":
            func = Node("func")
            func.name = tok[1]
            tok = next_token()
            if tok[0] == "left_paren":
                tok = next_token()
                tok, params = parse_param(tok)
                for p in params:
                    func.add_succ(p)
                if tok[0] == "right_paren":
                    tok = next_token()
                    if tok[0] == "left_bracket":
                        tok, block = parse_block(tok)
                        func.add_succ(block)
                    else:
                        report_error(tok)
                else:
                    report_error(tok)
            else:
                report_error(tok)
        else:
            report_error(tok)
    else:
        report_error(tok)
    return tok, func

def parse_param(tok):
    params = []
    if tok[0] == "int":
        tok = next_token()
        if tok[0] == "id":
            param = Node("param")
            param.name = tok[1]
            params.append(param)
            tok = next_token()
            tok, params = parse_params(tok, params)
        else:
            report_error(tok)
    elif tok[0] == "right_paren":
        return tok, params
    else:
        report_error(tok)
    return tok, params

def parse_params(tok, params):
    if tok[0] == "comma":
        tok = next_token()
        if tok[0] == "int":
            tok = next_token()
            if tok[0] == "id":
                param = Node("param")
                param.name = tok[1]
                params.append(param)
                tok = next_token()
                tok, params = parse_params(tok, params)
            else:
                report_error(tok)
        else:
            report_error(tok)
    return tok, params

def parse_stmt(tok):
    if tok[0] == "id":
        id = tok[1]
        tok = next_token()
        if tok[0] == "equals":
            stmt = Node("assignment")
            stmt.name = id
            tok, assign = parse_assignment(tok)
            stmt.add_succ(assign)
        elif tok[0] == "left_paren":
            stmt = Node("func_call")
            stmt.name = id
            tok, args = parse_func_call(tok)
            for arg in args:
                stmt.add_succ(arg)
        else:
            report_error(tok)
    elif tok[0] == "int":
        tok, stmt = parse_decl(tok)
    elif tok[0] == "left_bracket":
        tok, stmt = parse_block(tok)
    elif tok[0] == "if":
        tok, stmt = parse_if_stmt(tok)
    elif tok[0] == "return":
        tok, stmt = parse_return_stmt(tok)
    else:
        report_error(tok)
    return tok, stmt

def parse_decl(tok):
    if tok[0] == "int":
        tok = next_token()
        if tok[0] == "id":
            decl = Node("decl")
            decl.name = tok[1]
            tok = next_token()
            if tok[0] == "equals":
                tok, opt_assign = parse_opt_assign(tok)
                decl.add_succ(opt_assign)
                if tok[0] == "separator":
                    tok = next_token()
                else:
                    report_error(tok)
            elif tok[0] == "separator":
                tok = next_token()
            else:
                report_error(tok)
        else:
            report_error(tok)
    return tok, decl

def parse_opt_assign(tok):
    if tok[0] == "equals":
        tok = next_token()
        tok, exp = parse_exp(tok)
    return tok, exp

def parse_block(tok):
    if tok[0] == "left_bracket":
        tok = next_token()
        block = Node("block")
        stmts = []
        tok, stmts = parse_stmts(tok, stmts)
        for s in stmts:
            block.add_succ(s)
        if tok[0] == "right_bracket":
            tok = next_token()
        else:
            report_error(tok)
    return tok, block

def parse_assignment(tok):
    if tok[0] == "equals":
        tok = next_token()
        tok, exp = parse_exp(tok)
        if tok[0] == "separator":
            tok = next_token()
        else:
            report_error(tok)
    else:
        report_error(tok)
    return tok, exp

def parse_func_call(tok):
    args = []
    if tok[0] == "left_paren":
        tok = next_token()
        tok, args = parse_arg(tok)
        if tok[0] == "right_paren":
            tok = next_token()
            if tok[0] == "separator":
                tok = next_token()
            else:
                report_error(tok)
        else:
            report_error(tok)
    else:
        report_error(tok)
    return tok, args

def parse_arg(tok):
    args = []
    if tok[0] == "literal" or tok[0] == "id" or tok[0] == "left_paren":
        tok, exp = parse_exp(tok)
        arg = Node("arg")
        arg.add_succ(exp)
        args.append(arg)
        if tok[0] == "comma":
            tok, args = parse_args(tok, args)
            if tok[0] == "right_paren":
                return tok, args
            else:
                report_error(tok)
        elif tok[0] == "right_paren":
            return tok, args
        else:
            report_error(tok)
    return tok, args

def parse_args(tok, args):
    if tok[0] == "comma":
        tok = next_token()
        tok, exp = parse_exp(tok)
        arg = Node("arg")
        arg.add_succ(exp)
        args.append(arg)
        tok, args = parse_args(tok, args)
    return tok, args

def parse_if_stmt(tok):
    if tok[0] == "if":
        if_stmt = Node("if")
        tok = next_token()
        if tok[0] == "left_paren":
            tok = next_token()
            tok, condition = parse_condition(tok)
            if_stmt.add_succ(condition)
            if tok[0] == "right_paren":
                tok = next_token()
                if (tok[0] == "id" or tok[0] == "int" or tok[0] == "left_bracket"
                    or tok[0] == "if" or tok[0] == "return"):
                    tok, stmt = parse_stmt(tok)
                    if_stmt.add_succ(stmt)
                    tok, opt_else = parse_opt_else(tok)
                    if_stmt.add_succ(opt_else)
                else:
                    report_error(tok)
            else:
                report_error(tok)
    return tok, if_stmt

def parse_condition(tok):
    if tok[0] == "literal" or tok[0] == "id" or tok[0] == "left_paren":
        tok, exp = parse_exp(tok)
        condition = Node("condition")
        condition.add_succ(exp)
        tok, condition = parse_opt_comparison(tok, condition)
    return tok, condition

def parse_opt_comparison(tok, condition):
    if tok[0] == "less_than":
        tok = next_token()
        if tok[0] == "equals":
            tok = next_token()
            tok, exp = parse_exp(tok)
            condition.name = "less_than_equal"
            condition.add_succ(exp)
        else:
            tok, exp = parse_exp(tok)
            condition.name = "less_than"
            condition.add_succ(exp)
    elif tok[0] == "greater_than":
        tok = next_token()
        if tok[0] == "equals":
            tok = next_token()
            tok, exp = parse_exp(tok)
            condition.name = "greater_than_equal"
            condition.add_succ(exp)
        else:
            tok, exp = parse_exp(tok)
            condition.name = "greater_than"
            condition.add_succ(exp)
    elif tok[0] == "equals": #Token is called equals, but the operator is equal
        tok = next_token()
        if tok[0] == "equals":
            tok = next_token()
            tok, exp = parse_exp(tok)
            condition.name = "equal"
            condition.add_succ(exp)
        else:
            report_error(tok)
    elif tok[0] == "not":
        tok = next_token()
        if tok[0] == "equals":
            tok = next_token()
            tok, exp = parse_exp(tok)
            condition.name = "not_equal"
            condition.add_succ(exp)
        else:
            report_error(tok)
    return tok, condition

def parse_opt_else(tok):
    else_stmt = Node("else")
    if tok[0] == "else":
        tok = next_token()
        if (tok[0] == "id" or tok[0] == "int" or tok[0] == "left_bracket"
            or tok[0] == "if" or tok[0] == "return"):
            tok, stmt = parse_stmt(tok)
            else_stmt.add_succ(stmt)
        else:
            report_error(tok)
    return tok, else_stmt

def parse_return_stmt(tok):
    if tok[0] == "return":
        tok = next_token()
        tok, exp = parse_exp(tok)
        return_stmt = Node("return")
        return_stmt.add_succ(exp)
        if tok[0] == "separator":
            tok = next_token()
        else:
            report_error(tok)
    return tok, return_stmt

def parse_stmts(tok, stmts):
    if (tok[0] == "int" or tok[0] == "id" or tok[0] == "left_bracket"
        or tok[0] == "if" or tok[0] == "return"):
        tok, stmt = parse_stmt(tok)
        stmts.append(stmt)
        tok, stmts = parse_stmts(tok, stmts)
    return tok, stmts

def parse_exp(tok):
    if tok[0] == "literal" or tok[0] == "id" or tok[0] == "left_paren":
        tok, term = parse_term(tok)
        tok, exp2 = parse_exp2(tok)
        exp = Node("exp")
        exp.add_succ(term)
        exp.add_succ(exp2)
    return tok, exp

def parse_term(tok):
    if tok[0] == "literal" or tok[0] == "id" or tok[0] == "left_paren":
        tok, factor = parse_factor(tok)
        tok, exp3 = parse_exp3(tok)
        term = Node("term")
        term.add_succ(factor)
        term.add_succ(exp3)
    return tok, term

def parse_factor(tok):
    factor = Node("factor")
    if tok[0] == "literal":
        factor.val = tok[1]
        tok = next_token()
    elif tok[0] == "id":
        factor.name = tok[1]
        tok = next_token()
        if tok[0] == "left_paren":
            func_call = Node("func_call")
            func_call.name = factor.name
            factor.name = None
            tok, args = parse_opt_func_call(tok)
            for arg in args:
                func_call.add_succ(arg)
            factor.add_succ(func_call)
    elif tok[0] == "left_paren":
        tok = next_token()
        tok, exp = parse_exp(tok)
        factor.add_succ(exp)
        if tok[0] == "right_paren":
            tok = next_token()
        else:
            report_error(tok)
    return tok, factor

def parse_opt_func_call(tok):
    args = []
    if tok[0] == "left_paren":
        tok = next_token()
        tok, args = parse_arg(tok)
        if tok[0] == "right_paren":
            tok = next_token()
        else:
            report_error(tok)
    return tok, args

def parse_exp2(tok):
    exp2 = Node("exp2")
    if tok[0] == "add":
        exp2.name = "add"
        tok = next_token()
        tok, term = parse_term(tok)
        exp2.add_succ(term)
        tok, exp2_2 = parse_exp2(tok)
        exp2.add_succ(exp2_2)
    elif tok[0] == "sub":
        exp2.name = "sub"
        tok = next_token()
        tok, term = parse_term(tok)
        exp2.add_succ(term)
        tok, exp2_2 = parse_exp2(tok)
        exp2.add_succ(exp2_2)
    return tok, exp2

def parse_exp3(tok):
    exp3 = Node("exp3")
    if tok[0] == "mul":
        exp3.name = "mul"
        tok = next_token()
        tok, factor = parse_factor(tok)
        exp3.add_succ(factor)
        tok, exp3_2 = parse_exp3(tok)
        exp3.add_succ(exp3_2)
    elif tok[0] == "div":
        exp3.name = "div"
        tok = next_token()
        tok, factor = parse_factor(tok)
        exp3.add_succ(factor)
        tok, exp3_2 = parse_exp3(tok)
        exp3.add_succ(exp3_2)
    return tok, exp3

################################################################################

# The following functions are used to build the abstract syntax tree from the
# parse tree. Input is a node in the parse tree, output is a node in the ast.
def build_ast(node):
    prog_node = ast.ProgramNode()
    for succ in node.succs:
        func_node = build_func_node(succ)
        prog_node.add_func(func_node)
        prog_node.add_succ(func_node)
    return prog_node

def build_func_node(node):
    func_node = ast.FuncNode()
    func_node.name = node.name
    for succ in node.succs:
        if succ.sym == "param":
            param_node = ast.ParamNode()
            param_node.name = succ.name
            func_node.add_param(param_node)
        else:
            block_node = build_block_node(succ)
            func_node.block = block_node
            func_node.add_succ(block_node)
    return func_node

def build_stmt_node(node):
    if node.sym == "decl":
        stmt_node = build_decl_node(node)
    elif node.sym == "block":
        stmt_node = build_block_node(node)
    elif node.sym == "assignment":
        stmt_node = build_assignment_node(node)
    elif node.sym == "func_call":
        stmt_node = build_func_call_node(node)
    elif node.sym == "if":
        stmt_node = build_if_node(node)
    elif node.sym == "return":
        stmt_node = build_return_node(node)
    return stmt_node

def build_decl_node(node):
    decl_node = ast.DeclNode()
    decl_node.name = node.name
    for opt_assign in node.succs:
        exp_node = build_exp_node(opt_assign)
        decl_node.exp = exp_node
        decl_node.add_succ(exp_node)
    return decl_node

def build_block_node(node):
    block_node = ast.BlockNode()
    for succ in node.succs:
        stmt_node = build_stmt_node(succ)
        block_node.add_stmt(stmt_node)
        block_node.add_succ(stmt_node)
    return block_node

def build_assignment_node(node):
    assignment_node = ast.AssignmentNode()
    assignment_node.name = node.name
    exp_node = build_exp_node(node.succs[0])
    assignment_node.exp = exp_node
    assignment_node.add_succ(exp_node)
    return assignment_node

def build_func_call_node(node):
    func_call_node = ast.FuncCallNode()
    func_call_node.name = node.name
    for arg in node.succs:
        exp_node = build_exp_node(arg.succs[0])
        func_call_node.add_arg(exp_node)
        func_call_node.add_succ(exp_node)
    return func_call_node

def build_if_node(node):
    if_node = ast.IfStmtNode()
    condition = node.succs[0]
    stmt = node.succs[1]
    opt_else = node.succs[2]
    if_node.condition = build_condition_node(condition)
    if_node.add_succ(if_node.condition)
    if_node.stmt = build_stmt_node(stmt)
    if_node.add_succ(if_node.stmt)
    if opt_else.succs:
        if_node.opt_else = build_stmt_node(opt_else.succs[0])
        if_node.add_succ(if_node.opt_else)
    return if_node

def  build_condition_node(node):
    condition_node = ast.ConditionNode()
    condition_node.op1 = build_exp_node(node.succs[0])
    condition_node.add_succ(condition_node.op1)
    if node.name:
        condition_node.operator = node.name
        condition_node.op2 = build_exp_node(node.succs[1])
        condition_node.add_succ(condition_node.op2)
    return condition_node

def build_return_node(node):
    return_node = ast.ReturnStmtNode()
    return_node.exp = build_exp_node(node.succs[0])
    return_node.add_succ(return_node.exp)
    return return_node

# An expression node is either a single value, or an expression.
def build_exp_node(node):
    term = node.succs[0]
    exp2 = node.succs[1]
    if exp2.name:
        exp_node = ast.ExpNode()
        exp_node.is_exp = True
        exp_node.op1 = get_factor(term)
        exp_node.add_succ(exp_node.op1)
        exp_node.operator = exp2.name
        exp_node.op2 = get_term(exp2)
        exp_node.add_succ(exp_node.op2)
    else:
        exp_node = get_factor(term)
    return exp_node

# A factor is the left operand of a term in the parse tree.
def get_factor(node):
    exp_node = ast.ExpNode()
    factor = node.succs[0]
    exp3 = node.succs[1]
    if factor.succs and exp3.name:
        if factor.succs[0].sym == "arg":
            op1 = ast.ExpNode()
            #op1.is_func_call = True
            op1.func_call = build_func_call_node(factor)
            exp_node.op1 = op1
            exp_node.add_succ(op1)
        else:
            op1 = build_exp_node(factor.succs[0])
            exp_node.op1 = op1
            exp_node.add_succ(op1)
        exp_node.is_exp = True
        exp_node.operator = exp3.name
        exp_node.op2 = get_factor(exp3)
        exp_node.add_succ(exp_node.op2)
    elif exp3.name:
        exp_node.is_exp = True
        op1 = ast.ExpNode()
        op1.name = factor.name
        op1.val = factor.val
        exp_node.op1 = op1
        exp_node.add_succ(op1)
        exp_node.operator = exp3.name
        exp_node.op2 = get_factor(exp3)
        exp_node.add_succ(exp_node.op2)
    elif factor.succs:
        if factor.succs[0].sym == "func_call":
            exp_node.func_call = build_func_call_node(factor.succs[0])
            exp_node.add_succ(exp_node.func_call)
        else:
            exp_node = build_exp_node(factor.succs[0])
    elif factor.name:
        exp_node.name = factor.name
    elif factor.val:
        exp_node.val = factor.val
    return exp_node

# A term is the the left operand of an exp2 in the parse tree.
def get_term(node):
    exp_node = ast.ExpNode()
    term = node.succs[0]
    exp2 = node.succs[1]
    if exp2.name:
        exp_node.is_exp = True
        exp_node.op1 = get_factor(term)
        exp_node.add_succ(exp_node.op1)
        exp_node.operator = node.name
        exp_node.op2 = get_term(exp2)
        exp_node.add_succ(exp_node.op2)
    else:
        exp_node = get_factor(term)
    return exp_node

################################################################################

def print_parse_tree(parse_tree):
    while parse_tree:
        node = parse_tree.popleft()
        print(node.sym, '(', node.id, ')')
        print("name: ", node.name)
        print("value: ", node.val)
        print("successors:", end=' ')
        for n in node.succs:
            print(n.sym, '(', n.id ,')',  end=' ')
            if n.name != None or n.val != None or len(n.succs):
                parse_tree.append(n)
        print('\n')

#for r in tokens:
#    print(r)

prog = Node("program")
tok, parse = parse_program(next_token(), Node("program"))

if tok[0] != "eof":
    print("Failed to parse input!")
    sys.exit()

parse_tree = deque()
parse_tree.append(parse)
#print_parse_tree(parse_tree)
prog_ast = build_ast(parse) # The program node of the ast.
#print("---------------------------------------------------")
#prog_ast.print()
#print("---------------------------------------------------")
type_checker.type_check(prog_ast)
#print("---------------------------------------------------")
ir_code = ir_instr.translate_ast(prog_ast)
#ir_instr.print_program()
#print("---------------------------------------------------")
codegen.code_gen(ir_code)
codegen.print_asm_program()

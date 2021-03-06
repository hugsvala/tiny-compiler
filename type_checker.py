###======================================================================###
# Type checker for a small subset of C, in which the only existing type is #
# int and so it might seem like an unnecessary module but it also does     #
# other cool stuff, like making sure that variables are declared before    #
# they are used, correct number of function call arguments and so on.      #
###======================================================================###
from collections import deque
from dataclasses import dataclass
import ir_instr as ir
import sys

# An entry in the function symbol table.
@dataclass
class f_entry:
    name : str
    nbr_param : int

# An entry in the variable symbol table.
@dataclass
class v_entry:
    name : str
    local_index : int
    type : str = "int"

v_table = deque() # Variable symbol table, scopes are dicts.
f_table = dict() # Function symbol table.
f_table["print"] = f_entry("print", 1) # Print function hard-coded in assembly.

# Enter a new scope and put it on the variable symbol table stack.
def enter_scope():
    v_table.appendleft(dict())

# Exit the current scope.
def exit_scope():
    v_table.popleft()

# Check if name is already declared as a function.
def check_ftable_def(name):
    if f_table.get(name):
        report_error("Redeclaration. (func)")

# Check if name is already declared as a variable within the same scope.
def check_vtable_def(name):
    if v_table[0].get(name):
        report_error("Redeclaration. (var)")

# Make sure that functions are declared and that the number of param is correct.
def check_ftable_use(name, nbr_param):
    if f_table.get(name):
        if f_table[name].nbr_param != nbr_param:
            report_error("Wrong number of function arguments.")
    else:
        report_error("Function not declared.")

# Make sure that variables are declared before they are used.
def check_vtable_use(name):
    for v in v_table:
        if v.get(name):
            return v[name].local_index
    report_error("Variable used before declared.")

# Add a function to the fucntion symbol table.
def add_f_entry(name, nbr_param):
    check_ftable_def(name)
    f_table[name] = f_entry(name, nbr_param)

# Add a variable to the current scope. For simplicity we don't allow shared
# names between functions and variables.
def add_v_entry(name, local_index):
    check_ftable_def(name)
    check_vtable_def(name)
    v_table[0][name] = v_entry(name, local_index)

# Note that the parser doesn't currently parse global variables.
def type_check(prog_ast):
    for func in prog_ast.funcs:
        add_f_entry(func.name, len(func.params))
        enter_scope()
        type_check_func(func)
        exit_scope()

# Go through the function and look for defs and uses.
# When we reference a parameter in assembly we do: local_index*8(%rbp)
# The first parameter is 16 bytes away in memory so we start local_index on 2.
def type_check_func(func):
    local_index = 2
    for param in func.params:
        add_v_entry(param.name, local_index)
        local_index += 1
    type_check_block(func, func.block)

# We pass func as an argument so that we can propagate it along to the
# type_check_decl method, and update the nbr_locals used by codegen.
def type_check_stmt(func, stmt):
    if stmt.node_type == "decl_node":
        type_check_decl(func, stmt)
    elif stmt.node_type == "block_node":
        enter_scope()
        type_check_block(func, stmt)
        exit_scope()
    elif stmt.node_type == "assignment_node":
        stmt.local_index = check_vtable_use(stmt.name)
        type_check_exp(stmt.exp)
    elif stmt.node_type == "func_call_node":
        type_check_func_call(stmt)
    elif stmt.node_type == "if_node":
        type_check_if_stmt(func, stmt)
    elif stmt.node_type == "return_node":
        type_check_exp(stmt.exp)

# The calling function make sure to enter a new scope for block, even though
# type_check_block could do it, but this way is easier to scope params.
def type_check_block(func, block):
    for stmt in block.stmts:
        type_check_stmt(func, stmt)

# First make sure that we haven't declared the name earlier in scope.
def type_check_decl(func, decl):
    decl_name = decl.name
    func.nbr_locals += 1
    add_v_entry(decl_name, -func.nbr_locals)
    decl.local_index = -func.nbr_locals
    if decl.exp:
        type_check_exp(decl.exp)

def type_check_func_call(func_call):
    check_ftable_use(func_call.name, len(func_call.args))
    for arg in func_call.args:
        type_check_exp(arg)

def type_check_if_stmt(func, if_stmt):
    condition = if_stmt.condition
    stmt = if_stmt.stmt
    opt_else = if_stmt.opt_else
    type_check_exp(condition.op1)
    if condition.op2:
        type_check_exp(condition.op2)
    if stmt.node_type == "block_node":
        enter_scope()
        type_check_block(func, stmt)
        exit_scope()
    else:
        enter_scope()
        type_check_stmt(func, stmt)
        exit_scope()
    if opt_else:
        if opt_else.node_type == "block_node":
            enter_scope()
            type_check_block(func, opt_else)
            exit_scope()
        else:
            enter_scope()
            type_check_stmt(func, opt_else)
            exit_scope()

def type_check_exp(node):
    if node.name:
        node.local_index = check_vtable_use(node.name)
    elif node.is_exp:
        type_check_exp(node.op1)
        type_check_exp(node.op2)
    elif node.func_call:
        type_check_func_call(node.func_call)

def report_error(str):
    print("Error: ", str)
    sys.exit()


def print_tables():
    print("f_table: ")
    for f in f_table:
        print(f)
    print("---------------")
    print("v_table: ")
    for v in v_table:
        print(v)

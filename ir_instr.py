###======================================================================###
# This module defines the intermediate representation. The IR code is a    #
# form of three address code. Similar to a RISC language.                  #
# A node in the abstract syntax tree is translated to an equivalent        #
# sequence of instructions in the intermediate language.                   #
###======================================================================###
from itertools import count

next_temp = count(0, 1)
next_label = count(0, 1)

# A program is a list of IR instructions.
program = []

# Proivde a new temporary variable.
def new_temp():
    return "t" + str(next(next_temp))

# Provide a new label.
def new_label():
    return "L" + str(next(next_label))

# Instructions have an operand code, 0-2 srcs operands and 1 dest.
# For example: a = b + c;
# Translates into: ADD b, c, t0; mov t0, c
class IRInstr:
    def __init__(self, op, src1, src2, dest):
        self.op = op
        self.src1 = src1
        self.src2 = src2
        self.dest = dest
        self.func_call = None
        self.func_name = None
        self.func_args  = None

    # Returns a string for pretty printing of the IR instruction.
    def instr_str(self):
        padding = ' '
        x = padding.ljust(12 - len(self.op))
        instr_str = self.op + x
        if self.src1:
            instr_str += self.src1 + ", "
        if self.src2:
            instr_str += self.src2 + ", "
        if self.dest:
            instr_str += self.dest
        return instr_str

# The functions used to translate code into an IR are similar to those that
# were used in type checking.
def translate_ast(prog_ast):
    for func in prog_ast.funcs:
        program.append(IRInstr("begin", None, None, func.name))
        translate_block(func.block)
        program.append(IRInstr("end", None, None, func.name))
    return program

def translate_stmt(stmt):
    if stmt.node_type == "decl_node":
        if stmt.exp:
            t = translate_exp(stmt.exp)
            program.append(IRInstr("mov", t, None, stmt.name))
    elif stmt.node_type == "block_node":
        translate_block(stmt)
    elif stmt.node_type == "assignment_node":
        t = translate_exp(stmt.exp)
        program.append(IRInstr("mov", t, None, stmt.name))
    elif stmt.node_type == "func_call_node":
        program.append(translate_func_call(stmt))
    elif stmt.node_type == "if_node":
        translate_if_stmt(stmt)
    elif stmt.node_type == "return_node":
        translate_return_stmt(stmt)

def translate_block(block):
    for stmt in block.stmts:
        translate_stmt(stmt)

# Func call IR instructions look like: CALL f(a,b,c,...)
def translate_func_call(stmt):
    func_call = stmt.name + "("
    for arg in stmt.args:
        t = translate_exp(arg)
        func_call += t + ", "
    func_call = func_call[:-2]
    func_call += ")"
    return IRInstr("CALL", None, None, func_call)

# The instructions directly after the conditional branch is an unconditional
# branch to the end of the if-block.
def translate_if_stmt(stmt):
    begin_if = translate_condition(stmt.condition)
    end_if = new_label()
    b_end_if = IRInstr("b", None, None, end_if)
    program.append(b_end_if)
    label_begin_if = IRInstr("label", None, None, begin_if)
    label_end_if = IRInstr("label", None, None, end_if)
    program.append(label_begin_if)
    translate_stmt(stmt.stmt)
    if stmt.opt_else:
        end_else = new_label()
        b_end_else = IRInstr("b", None, None, end_else)
        label_end_else = IRInstr("label", None, None, end_else)
        program.append(b_end_else)
        program.append(label_end_if)
        translate_stmt(stmt.opt_else)
        program.append(b_end_else)
        program.append(label_end_else)
    else:
        program.append(b_end_if)
        program.append(label_end_if)

def translate_condition(cond):
    label = new_label()
    op1 = translate_exp(cond.op1)
    if cond.op2:
        op2 = translate_exp(cond.op2)
        if cond.operator == "less_than":
            cond_str = "bl"
        elif cond.operator == "less_than_equal":
            cond_str = "ble"
        elif cond.operator == "greater_than":
            cond_str = "bg"
        elif cond.operator == "greater_than_equal":
            cond_str = "bge"
        elif cond.operator == "equals":
            cond_str = "beq"
        elif cond.operator == "not_equal":
            cond_str = "bl"
        cond_instr = IRInstr(cond_str, op1, op2, label)
    else:
        cond_instr = IRInstr("bg", op1, 0, label)
    program.append(cond_instr)
    return label

def translate_return_stmt(stmt):
    t = translate_exp(stmt.exp)
    program.append(IRInstr("ret", None, None, t))

def translate_exp(exp):
    if exp.is_exp:
        t = new_temp()
        op1 = translate_exp(exp.op1)
        op2 = translate_exp(exp.op2)
        program.append(IRInstr(exp.operator, op1, op2, t))
        return t
    elif exp.name:
        exp_str = exp.name
        return exp_str
    elif exp.val:
        exp_str = exp.val
        return exp_str
    elif exp.func_call:
        f = translate_func_call(exp.func_call)
        exp_str = "CALL_" + f.dest
        return exp_str

def print_program():
    for instr in program:
        print(instr.instr_str())
        if instr.op == "end":
            print("")

###======================================================================###
# This module contains the node classes used by the parser to implement    #
# the abstract syntax tree from the parse tree.                            #
###======================================================================###
from itertools import count

# Base class for nodes in the AST.
class ASTNode:
    _node_id = count(0, 1)
    def __init__(self):
        self.id = next(self._node_id)
        self.succs = []

    def add_succ(self, succ):
        self.succs.append(succ)

    def print(self):
        print("Node ID: ", self.id)

# A program is a list of functions.
class ProgramNode(ASTNode):
    def __init__(self):
        super().__init__()
        self.node_type = "prog_node"
        self.funcs = []

    def add_func(self, func):
        self.funcs.append(func)

    def print(self):
        #print("Program node")
        for func in self.funcs:
            func.print()

# Function nodes can be either declarations or definitions. The parser only
# deals with defintions.
class FuncNode(ASTNode):
    def __init__(self):
        super().__init__()
        self.node_type = "func_node"
        self.name = None
        self.params = []
        self.block = None
        self.nbr_locals = 0 # This is used by code gen to allocated stack space.

    def add_param(self, param):
        self.params.append(param)

    def print(self):
        print("Func name: ", self.name)
        for param in self.params:
            param.print()
        if self.block:
            self.block.print()
        print("---Func end---")

# Function parameter.
class ParamNode(ASTNode):
    def __init__(self):
        super().__init__()
        self.node_type = "param_node"
        self.type = "int"   # The front end only deals with int types atm.
        self.name = None

    def print(self):
        print("Param name: ", self.name)

# A block is a section of code (list of stmts) delimited by brackets.
class BlockNode(ASTNode):
    def __init__(self):
        super().__init__()
        self.node_type = "block_node"
        self.stmts = []

    def add_stmt(self, stmt):
        self.stmts.append(stmt)

    def print(self):
        #print("Block node")
        for stmt in self.stmts:
            stmt.print()
            print("--------------")

# Variable declaration with an optional assignment.
class DeclNode(ASTNode):
    def __init__(self):
        super().__init__()
        self.node_type = "decl_node"
        self.name = None
        self.exp = None
        self.local_index = None # Used by code gen as: "-local_index*8(%rbp)".

    def print(self):
        print("Decl name: ", self.name)
        if self.exp:
            self.exp.print()

# Expressions can be single values, in which case op1 is used.
class ExpNode(ASTNode):
    def __init__(self):
        super().__init__()
        self.node_type = "exp_node"
        self.name = None
        self.val = None
        self.is_exp = False  # If false this is single value.
        self.op1 = None
        self.op2 = None
        self.operator = None
        self.func_call = None
        self.local_index = None # Used by code gen as: "-local_index*8(%rbp)".

    def print(self):
        if self.is_exp:
            print("---Exp node---: ", self.operator)
            self.op1.print()
            self.op2.print()
        elif self.func_call:
            self.func_call.print()
        elif self.name:
            print("Operand: ", self.name)
        elif self.val:
            print("Operand: ", self.val)

# Assignment.
class AssignmentNode(ASTNode):
    def __init__(self):
        super().__init__()
        self.node_type = "assignment_node"
        self.name = None
        self.exp = None
        self.local_index = None # Used by code gen as: "-local_index*8(%rbp)".

    def print(self):
        print("Assignment name: ", self.name)
        self.exp.print()

# Function call.
class FuncCallNode(ASTNode):
    def __init__(self):
        super().__init__()
        self.node_type = "func_call_node"
        self.name = None
        self.args = []

    def add_arg(self, arg):
        self.args.append(arg)

    def print(self):
        print("Func call: ", self.name)
        print("Args: ")
        for arg in self.args:
            arg.print()

# If stmt with option else.
class IfStmtNode(ASTNode):
    def __init__(self):
        super().__init__()
        self.node_type = "if_node"
        self.condition = None
        self.stmt = None
        self.opt_else = None

    def print(self):
        print("---If---")
        self.condition.print()
        print("---Then---")
        self.stmt.print()
        if self.opt_else:
            print("---Else---")
            self.opt_else.print()

# Condition of an if statment.
class ConditionNode(ASTNode):
    def __init__(self):
        super().__init__()
        self.node_type = "condition_node"
        self.op1 = None
        self.op2 = None
        self.operator = None

    def print(self):
        if self.operator:
            print("Condition: ", self.operator)
            self.op1.print()
            self.op2.print()
        else:
            print("Condition: ")
            self.op1.print()


# Return statment.
class ReturnStmtNode(ASTNode):
    def __init__(self):
        super().__init__()
        self.node_type = "return_node"
        self.exp = None

    def print(self):
        print("---Return---")
        self.exp.print()

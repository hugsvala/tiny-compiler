###======================================================================###
# Code generation for a very small subset of C. Given a program translated #
# into IR code, the code generator outputs a file in x86-64 assembly.      #
# However(!!!) I wouldn't trust it. For anything but the simplest programs #
# the current codegen is very, very messy. (It does not like recursion.)   #
###======================================================================###

ws = "         " # White space to align instructions in a nice column.
program = []
program.append(".global _start")
program.append(".data")
program.append("buf: .skip 1024") # Buffer for the pring function.
program.append(".text")

def code_gen(ir_code):
    call_print = False
    current_nbr_locals = 0 # Used to avoid seg fault.
    is_main = False # Used to call sys_exit on return from main.
    for i in ir_code:
        if i.op == "begin":
            if i.dest.func_name == "main":
                program.append("_start:")
                is_main = True
            else:
                program.append("\n" + i.dest.func_name + ":")
            program.append(ws + "pushq %rbp")
            program.append(ws + "movq %rsp, %rbp")
            if i.dest.nbr_locals > 0:
                current_nbr_locals = i.dest.nbr_locals
                size = str(8*current_nbr_locals)
                program.append(ws + "subq $" + size + ", %rsp")
        elif i.op == "CALL":
            call_print = gen_call_instr(i, call_print)
        elif (i.op == "bl" or i.op == "ble" or i.op == "bg" or i.op == "bge"
              or i.op == "beq" or i.op == "bne"):
              gen_conditional_branch(i)
        elif i.op == "b":
            program.append(ws + "jmp " + i.dest.name)
        elif i.op == "label":
            program.append(i.dest.name + ":")
        elif i.op == "mov":
            gen_mov(i)
        elif i.op == "add" or i.op == "sub" or i.op == "mul" or i.op == "div":
            gen_arithmetic(i)
        elif i.op == "ret":
            if is_main:
                program.append(ws + "movq $0, %rdi")
                program.append(ws + "movq $60, %rax") # sys_exit
                program.append(ws + "syscall")
            else:
                if i.dest.val:
                    program.append(ws + "movq $" + i.dest.val + ", %rax")
                elif i.dest.func_name:
                    gen_call_operand(i.dest)
                elif i.dest.temp_var:
                    program.append(ws + "popq %rax")
                elif i.dest.name:
                    dest = str(8 * i.dest.local_index)
                    program.append(ws + "movq " + dest + "(%rbp), %rax")
                if current_nbr_locals > 0:
                    program.append(ws + "movq %rbp, %rsp")
                program.append(ws + "popq %rbp")
                program.append(ws + "ret")


    if call_print:
        output_asm_func()

# Generate code for move instructions.
def gen_mov(instr):
    dest = str(8 * instr.dest.local_index)
    if instr.src1.val:
        program.append(ws + "movq $" + instr.src1.val + ", " + dest + "(%rbp)")
    elif instr.src1.func_name:
        gen_call_operand(instr.src1)
        program.append(ws + "movq %rax, " + dest + "(%rbp)")
    elif instr.src1.temp_var:
        program.append(ws + "popq " + dest + "(%rbp)")
    elif instr.src1.name:
        address = str(8 * instr.src1.local_index)
        program.append(ws + "movq " + address + "(%rbp), %rax")
        program.append(ws + "movq %rax, " + dest + "(%rbp)")

def gen_arithmetic(instr):
    src1 = instr.src1
    src2 = instr.src2

    # We want src1 in rax, and src2 in rbx.
    if src1.temp_var and src2.temp_var:
        program.append(ws + "popq %rbx")
        program.append(ws + "popq %rax")
    elif src1.temp_var:
        if src2.val:
            program.append(ws + "movq $" + src2.val + ", %rbx")
            program.append(ws + "popq %rax")
        elif src2.func_name:
            gen_call_operand(src2)
            program.append(ws + "movq %rax, %rbx")
            program.append(ws + "popq %rax")
        elif src2.name:
            address = str(8 * src2.local_index)
            program.append(ws + "movq " + address + "(%rbp), %rbx")
            program.append(ws + "popq %rax")
    elif src2.temp_var:
        if src1.val:
            program.append(ws + "movq $" + src1.val + ", %rax")
            program.append(ws + "popq %rbx")
        elif src1.func_name:
            gen_call_operand(src1)
            program.append(ws + "popq %rbx")
        elif src1.name:
            address = str(8 * src1.local_index)
            program.append(ws + "movq " + address + "(%rbp), %rax")
            program.append(ws + "popq %rbx")
    else:
        if src1.val:
            program.append(ws + "movq $" + src1.val + ", %rax")
        elif src1.func_name:
            gen_call_operand(src1)
        elif src1.name:
            address = str(8 * src1.local_index)
            program.append(ws + "movq " + address + "(%rbp), %rax")

        if src2.val:
            program.append(ws + "movq $" + src2.val + ", %rbx")
        elif src2.func_name:
            program.append(ws + "pushq %rax")
            gen_call_operand(src2)
            program.append(ws + "movq %rax, %rbx")
            program.append(ws + "popq %rax")
        elif src2.name:
            address = str(8 * src2.local_index)
            program.append(ws + "movq " + address + "(%rbp), %rbx")

    if instr.op == "add":
        program.append(ws + "addq %rbx, %rax")
    elif instr.op == "sub":
        program.append(ws + "subq %rbx, %rax")
    elif instr.op == "mul":
        program.append(ws + "imulq %rbx, %rax")
    elif instr.op == "div":
        program.append(ws + "xor %rdx, %rdx")
        program.append(ws + "idivq %rbx")

    program.append(ws + "pushq %rax") # Store the temp on stack.

# Generate code for branch instructions.
def gen_conditional_branch(instr):
    src1 = instr.src1
    src2 = instr.src2

    if src1.temp_var and src2.temp_var:
        program.append(ws + "popq %r9")
        program.append(ws + "popq %r8")

    if src1.val:
        program.append(ws + "movq $" + src1.val + ", %r8")
    elif src1.func_name:
        gen_call_operand(src1)
        program.append(ws + "movq %rax, %r8")
    elif src1.temp_var:
        program.append(ws + "popq %r8")
    elif src1.name:
        address = str(8 * src1.local_index)
        program.append(ws + "movq " + address + "(%rbp), %r8")

    if src2.val:
        program.append(ws + "movq $" + src2.val + ", %r9")
    elif src2.func_name:
        gen_call_operand(src2)
        program.append(ws + "movq %rax, %r9")
    elif src2.temp_var:
        program.append(ws + "popq %r9")
    elif src2.name:
        address = str(8 * src2.local_index)
        program.append(ws + "movq " + address + "(%rbp), %r9")

    program.append(ws + "cmpq %r9, %r8")
    opcode = instr.op
    label = instr.dest.name
    if opcode == "bl":
        program.append(ws + "jl " + label)
    elif opcode == "ble":
        program.append(ws + "jle " + label)
    elif opcode == "bg":
        program.append(ws + "jg " + label)
    elif opcode == "bge":
        program.append(ws + "jge " + label)
    elif opcode == "beq":
        program.append(ws + "je " + label)
    elif opcode == "bne":
        program.append(ws + "jne " + label)

# Generate code for call instructions.
def gen_call_instr(instr, call_print):
    if instr.dest.func_name == "print":
        call_print = True
        arg = instr.dest.args[0]
        if arg.val:
            program.append(ws + "movq $" + arg.val + ", %rax")
            program.append(ws + "pushq %rax")
            program.append(ws + "call print")
            program.append(ws + "addq $8, %rsp")
        elif arg.func_name:
            gen_call_operand(arg)
            program.append(ws + "pushq %rax")
            program.append(ws + "call print")
            program.append(ws + "addq $8, %rsp")
        elif arg.temp_var:
            program.append(ws + "call print")
            program.append(ws + "addq $8, %rsp")
        elif arg.name:
            address = str(8 * arg.local_index)
            program.append(ws + "movq " + address + "(%rbp), %rax")
            program.append(ws + "pushq %rax")
            program.append(ws + "call print")
            program.append(ws + "addq $8, %rsp")
    else:
        for arg in reversed(instr.dest.args):
            if arg.val:
                program.append(ws + "movq $" + arg.val + ", %rax")
                program.append(ws + "pushq %rax")
            elif arg.func_name:
                gen_call_operand(arg)
                program.append(ws + "pushq %rax")
            elif arg.name and not arg.temp_var:
                address = str(8*arg.local_index)
                program.append(ws + "movq " + address + "(%rbp), %rax")
                program.append(ws + "pushq %rax")
        program.append(ws + "call " + instr.dest.func_name)
        if instr.dest.args:
            size = str(8*len(instr.dest.args))
            program.append(ws + "addq $" + size + ", %rsp")
    return call_print

# Generate code for calls that are operands.
def gen_call_operand(op):
    if op.func_name == "print":
        print("Codegen failed. Print is void.")
        sys.exit()
    else:
        for arg in reversed(op.args):
            if arg.val:
                program.append(ws + "movq $" + arg.val + ", %rax")
                program.append(ws + "pushq %rax")
            elif arg.func_name:
                gen_call_operand(arg)
                program.append(ws + "pushq %rax")
            elif arg.name and not arg.temp_var:
                address = str(8*arg.local_index)
                program.append(ws + "movq " + address + "(%rbp), %rax")
                program.append(ws + "pushq %rax")
        program.append(ws + "call " + op.func_name)
        if op.args:
            size = str(8*len(op.args))
            program.append(ws + "addq $" + size + ", %rsp")

# This function add a function written in assembly, which converts an integer
# to a sequence of characters and sends it to sys_write.
def output_asm_func():
    program.append("\nprint:")
    program.append(ws + "pushq %rbp")
    program.append(ws + "movq %rsp, %rbp")
    program.append(ws + "movq 16(%rbp), %rax")
    program.append(ws + "leaq buf(%rip), %rsi")
    program.append(ws + "addq $1023, %rsi") # buf is filled-in lsd first
    program.append(ws + "movb $0x0A, (%rsi)") # ascii code for newline
    program.append(ws + "movq $1, %rcx")
    program.append(ws + "movq $10, %rdi") # in itoa we divide by 10
    program.append(ws + "cmpq $0, %rax")
    program.append(ws + "jge itoa")
    program.append(ws + "negq %rax") # make it positive, will add sign last
    program.append("itoa:")
    program.append(ws + "xor %rdx, %rdx") # clear rdx
    program.append(ws + "idivq %rdi") # reminder is put in rdx
    program.append(ws + "addq $0x30, %rdx") # get the correct ascii code.
    program.append(ws + "decq %rsi")
    program.append(ws + "movb %dl, (%rsi)") # move lower byte of rdx into buf
    program.append(ws + "incq %rcx")
    program.append(ws + "cmpq $0, %rax") # rax holds quotient
    program.append(ws + "jg itoa")
    program.append(ws + "movq 16(%rbp), %rax")
    program.append(ws + "cmpq $0, %rax")
    program.append(ws + "jge print_end")
    program.append(ws + "decq %rsi")
    program.append(ws + "incq %rcx")
    program.append(ws + "movb $0x2D, (%rsi)") # ascii code for minus sign
    program.append("print_end:")
    program.append(ws + "movq $1, %rdi")
    program.append(ws + "movq %rcx, %rdx")
    program.append(ws + "movq $1, %rax") # sys_write
    program.append(ws + "syscall")
    program.append(ws + "popq %rbp")
    program.append(ws + "ret")

def print_asm_program():
    for instr in program:
        print(instr)

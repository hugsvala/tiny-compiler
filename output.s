.global _start
.data
buf: .skip 1024
.text

f:
         pushq %rbp
         movq %rsp, %rbp
         subq $16, %rsp
         movq 16(%rbp), %r8
         movq $2, %r9
         cmpq %r9, %r8
         jl L0
         jmp L1
L0:
         movq 16(%rbp), %rax
         movq %rbp, %rsp
         popq %rbp
         ret
         jmp L2
L1:
         movq 16(%rbp), %rax
         movq $2, %rbx
         subq %rbx, %rax
         pushq %rax
         call f
         addq $8, %rsp
         movq %rax, -8(%rbp)
         movq 16(%rbp), %rax
         movq $1, %rbx
         subq %rbx, %rax
         pushq %rax
         call f
         addq $8, %rsp
         movq %rax, -16(%rbp)
         movq -8(%rbp), %rax
         movq -16(%rbp), %rbx
         addq %rbx, %rax
         pushq %rax
         popq %rax
         movq %rbp, %rsp
         popq %rbp
         ret
         jmp L2
L2:
_start:
         pushq %rbp
         movq %rsp, %rbp
         subq $8, %rsp
         movq $9, %rax
         pushq %rax
         call f
         addq $8, %rsp
         movq %rax, -8(%rbp)
         movq -8(%rbp), %rax
         pushq %rax
         call print
         addq $8, %rsp
         movq $0, %rdi
         movq $60, %rax
         syscall

print:
         pushq %rbp
         movq %rsp, %rbp
         movq 16(%rbp), %rax
         leaq buf(%rip), %rsi
         addq $1023, %rsi
         movb $0x0A, (%rsi)
         movq $1, %rcx
         movq $10, %rdi
         cmpq $0, %rax
         jge itoa
         negq %rax
itoa:
         xor %rdx, %rdx
         idivq %rdi
         addq $0x30, %rdx
         decq %rsi
         movb %dl, (%rsi)
         incq %rcx
         cmpq $0, %rax
         jg itoa
         movq 16(%rbp), %rax
         cmpq $0, %rax
         jge print_end
         decq %rsi
         incq %rcx
         movb $0x2D, (%rsi)
print_end:
         movq $1, %rdi
         movq %rcx, %rdx
         movq $1, %rax
         syscall
         popq %rbp
         ret

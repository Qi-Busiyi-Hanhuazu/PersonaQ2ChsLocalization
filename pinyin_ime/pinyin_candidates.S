/* External table-driven pinyin candidate provider for Persona Q2. */

    .syntax unified
    .arch armv6k
    .arm
    .section .text.pinyin_candidates, "ax", %progbits
    .align 2

    .equ ENGINE_CONTEXT_PTR,    0x0059D29C
    .equ NAME_STATE,            0x0059D2A0
    .equ INPUT_BUFFER,          0x18
    .equ MEMO_DICTIONARY_INDEX, 0x0002F108
    .equ DICTIONARY_SLOTS,      0x0002EC6C
    .equ COUNT_RESUME,          0x001F2B58
    .equ CANDIDATE_RESUME,      0x001F2B18
    .equ PATH_RESUME,           0x0025F278
    .equ PINYIN_DICTIONARY_NAME, 0x002F2018
    .equ BASE_ROM_PREFIX,       0x0025F46C
    .equ UPDATE_ROM_PREFIX,     0x00104564
    .equ PYDB_MAGIC,            0x42445950

    /*
     * The update RomFS is mounted as eom:, while the native dictionaries are
     * loaded from rom:.  Select eom: only for our redirected memo filename so
     * all other iWnn dictionaries keep using the base RomFS.
     */
    .global pinyin_dictionary_path_hook
    .type pinyin_dictionary_path_hook, %function
pinyin_dictionary_path_hook:
    ldr     r2, =PINYIN_DICTIONARY_NAME
    cmp     r1, r2
    ldreq   r2, =UPDATE_ROM_PREFIX
    ldrne   r2, =BASE_ROM_PREFIX
    ldr     pc, =PATH_RESUME

    .size pinyin_dictionary_path_hook, .-pinyin_dictionary_path_hook

    /*
     * Return the appended PYDB header in r0.  The native memo dictionary
     * loader is redirected to njubase2.a in the update RomFS; that file
     * contains a generated minimal NJDC container followed by our own database.  The native slot
     * owns and frees the allocation, so the hook needs no writable global state.
     */
    .type pinyin_db_base, %function
pinyin_db_base:
    ldr     r0, =ENGINE_CONTEXT_PTR
    ldr     r0, [r0]
    cmp     r0, #0
    beq     db_missing
    ldr     r1, =MEMO_DICTIONARY_INDEX
    ldr     r1, [r0, r1]
    add     r1, r1, r1, lsl #3
    add     r0, r0, r1, lsl #2
    ldr     r1, =DICTIONARY_SLOTS
    ldr     r0, [r0, r1]
    cmp     r0, #0
    beq     db_missing

    /* NJDC payload size is big-endian; logical file end = size + 0x48. */
    ldr     r1, [r0, #0x0C]
    rev     r1, r1
    add     r0, r0, r1
    add     r0, r0, #0x48
    ldr     r1, [r0]
    ldr     r2, =PYDB_MAGIC
    cmp     r1, r2
    moveq   pc, lr

db_missing:
    mov     r0, #0
    bx      lr

    .size pinyin_db_base, .-pinyin_db_base

    /*
     * Find an exact pinyin record.  r0 is a CP932 composition string;
     * ASCII and CP932 full-width Latin letters are compared case-insensitively.
     * Returns a record pointer or zero.
     */
    .type pinyin_find, %function
pinyin_find:
    push    {r4, r5, r6, r7, r8, lr}
    mov     r4, r0
    bl      pinyin_db_base
    cmp     r0, #0
    beq     find_no
    ldrh    r6, [r0, #6]
    add     r5, r0, #8

find_record:
    cmp     r6, #0
    beq     find_no
    ldrb    r7, [r5, #0]
    add     r1, r5, #4
    mov     r0, r4
    mov     r8, r7

compare_key:
    cmp     r8, #0
    beq     compare_end
    ldrb    r2, [r1], #1
    ldrb    r3, [r0], #1
    cmp     r3, #0x82
    bne     compare_ascii

    /* CP932 full-width A-Z/a-z. */
    ldrb    r3, [r0], #1
    cmp     r3, #0x60
    blo     compare_fail
    cmp     r3, #0x79
    subls   r3, r3, #0x60
    addls   r3, r3, #'a'
    bls     compare_mapped
    cmp     r3, #0x81
    blo     compare_fail
    cmp     r3, #0x9A
    subls   r3, r3, #0x81
    addls   r3, r3, #'a'
    bhi     compare_fail
    b       compare_mapped

compare_ascii:
    orr     r3, r3, #0x20

compare_mapped:
    cmp     r3, r2
    bne     compare_fail
    subs    r8, r8, #1
    bne     compare_key

compare_end:
    ldrb    r2, [r0]
    cmp     r2, #0
    beq     find_yes

compare_fail:
    ldrh    r0, [r5, #2]
    cmp     r0, #4
    blo     find_no
    add     r5, r5, r0
    subs    r6, r6, #1
    b       find_record

find_yes:
    mov     r0, r5
    pop     {r4, r5, r6, r7, r8, pc}

find_no:
    mov     r0, #0
    pop     {r4, r5, r6, r7, r8, pc}

    .size pinyin_find, .-pinyin_find

    .global pinyin_count_hook
    .type pinyin_count_hook, %function
pinyin_count_hook:
    push    {r0, r1, r2, r3, lr}
    sub     sp, sp, #4
    bl      pinyin_find
    mov     r12, r0
    add     sp, sp, #4
    pop     {r0, r1, r2, r3, lr}
    cmp     r12, #0
    beq     count_fallback
    ldrb    r0, [r12, #1]
    bx      lr

count_fallback:
    /* Reproduce the overwritten instruction, then resume iWnn. */
    ldr     r1, =ENGINE_CONTEXT_PTR
    ldr     pc, =COUNT_RESUME

    .size pinyin_count_hook, .-pinyin_count_hook

    .align 2
    .global pinyin_candidate_hook
    .type pinyin_candidate_hook, %function
pinyin_candidate_hook:
    push    {r0, r1, r2, r3, r4, r5, r6, lr}
    ldr     r3, =NAME_STATE
    ldr     r0, [r3, #INPUT_BUFFER]
    bl      pinyin_find
    cmp     r0, #0
    beq     candidate_restore_fallback

    mov     r4, r0
    ldr     r5, [sp, #4]          /* requested candidate index */
    ldrb    r6, [r4, #1]
    cmp     r5, r6
    bhs     candidate_empty
    ldrb    r6, [r4, #0]
    add     r4, r4, #4
    add     r4, r4, r6            /* first NUL-terminated candidate */

candidate_skip:
    cmp     r5, #0
    beq     candidate_copy_start
candidate_skip_byte:
    ldrb    r6, [r4], #1
    cmp     r6, #0
    bne     candidate_skip_byte
    subs    r5, r5, #1
    bne     candidate_skip

candidate_copy_start:
    ldr     r5, [sp, #0]          /* destination 0x30-byte buffer */
    mov     r6, #0x2F
candidate_copy:
    ldrb    r0, [r4], #1
    strb    r0, [r5], #1
    cmp     r0, #0
    beq     candidate_done
    subs    r6, r6, #1
    bne     candidate_copy
    mov     r0, #0
    strb    r0, [r5]

candidate_done:
    pop     {r0, r1, r2, r3, r4, r5, r6, lr}
    bx      lr

candidate_empty:
    ldr     r5, [sp, #0]
    mov     r0, #0
    strb    r0, [r5]
    b       candidate_done

candidate_restore_fallback:
    pop     {r0, r1, r2, r3, r4, r5, r6, lr}
candidate_fallback:
    /* Reproduce the overwritten instruction, then resume iWnn. */
    ldr     r2, =ENGINE_CONTEXT_PTR
    ldr     pc, =CANDIDATE_RESUME

    .size pinyin_candidate_hook, .-pinyin_candidate_hook

    .ltorg

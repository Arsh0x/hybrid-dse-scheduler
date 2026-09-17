# Instrumentation Route Decision

## Requirements
- x86-64 binaries, including stripped and COTS-style
- Near-compiler-level performance
- Branch-level coverage attribution
- Stable branch IDs across runs (PIE and non-PIE)
- Low overhead so scheduler gains are not erased

## Options

| Option | Overhead | Coverage Quality | Binary-Only | Complexity | Recommended |
|:---|:---:|:---:|:---:|:---:|:---:|
| Always-on DBT (DynamoRIO/Pin) | High | High | ✅ | Low | ❌ |
| Static rewriting (RetroWrite-style) | Low | High | ✅ | Medium | ✅ |
| Static binary coverage patching (AFL++ qemu_mode / FRIDA) | Medium | Medium | ✅ | Low | ⚠️ |
| Compiler-based (source available) | Lowest | Highest | ❌ | Low | Only for source targets |
| Selective/CFG-aware instrumentation (INSTRIM-style) | Low | High | ⚠️ | Medium | ✅ for selective visibility |

## Decision

**Primary route:** Static rewriting for x86-64 PIE binaries (RetroWrite-style), giving near-compiler-level performance and stable branch IDs.

**Secondary route:** AFL++ qemu_mode or FRIDA for quick baseline and for binaries where static rewriting fails.

**Selective visibility:** If overhead becomes a problem, apply CFG-aware selective instrumentation to instrument only a small fraction of blocks while preserving path distinction.

**Branch ID scheme:** build_id (SHA256 of binary) + module-relative branch offset (offset from module base). This is stable across PIE/non-PIE and repeated runs.

## Risks
- Static rewriting may fail on heavily obfuscated or packed binaries. Mitigation: fall back to qemu_mode for those targets.
- Overhead measurement must be included in evaluation (RQ5).

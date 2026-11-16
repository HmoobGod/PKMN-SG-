# R6-10 R3 — Adversarial screening repair for PR115

Source-only security heuristic, not a privacy guarantee. Independent human review of all upload content remains mandatory.

Extends content checks to reject MIME-wrapped standard and URL-safe base64, 64-column hex, spaced hex, xxd/hexdump-style lines, uppercase/spaced `0Xhh` byte arrays, long decimal byte arrays, and split `bytes.fromhex` literals. Keeps R2 name, double-extension, symlink, traversal, size, UTF-8 and compression restrictions. New synthetic tests independently pin control-byte and ZIP compression-ratio rejection.

These checks cannot detect arbitrary obfuscation, deliberate encryption, short fragments, or data disguised as prose/source. Do not rely on this as the sole pre-upload defense. No ROM/save or private capture data included. No merge/release; formal native acceptance 0/20.

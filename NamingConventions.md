# Variable Naming Conventions — SAPIC-Classes protocol-code

Role suffixes: `c` = Client, `s` = Server

## Asymmetric keys

| Variable | Meaning |
|----------|---------|
| `pKc`  | Client public key |
| `pKs`  | Server public key |
| `ltKc` | Client long-term private key |
| `ltKs` | Server long-term private key |

## Symmetric keys

| Variable | Meaning |
|----------|---------|
| `psk` | Shared symmetric key (PSK / session key used directly for enc/dec) |

## Diffie-Hellman

| Variable | Meaning |
|----------|---------|
| `eKc`  | Client ephemeral secret exponent |
| `eKs`  | Server ephemeral secret exponent |
| `ePKc` | Client ephemeral public share (was g^x) |
| `ePKs` | Server ephemeral public share (was g^y) |
| `dhZ`  | Derived shared DH secret |

Static (long-term) DH keys fold into `pKc` / `pKs` / `ltKc` / `ltKs`.

## Nonces

| Variable | Meaning |
|----------|---------|
| `n` | Nonce |

## Messages

| Variable | Meaning |
|----------|---------|
| `m`  | Message (single direction per file) |
| `mC` | Client's message (both directions in file) |
| `mS` | Server's message (both directions in file) |

## Ciphertext

| Variable | Meaning |
|----------|---------|
| `xencC` | Ciphertext sent by Client |
| `xencS` | Ciphertext sent by Server |

## Notes / exceptions

- `HKDF.spthy`: `PRK` and `OKM` are left as-is (RFC 5869 terminology for the
  extract/expand output), distinct from `psk` (the long-term input secret).
- `hashing.spthy`: the received hash digest is named `H` (not part of the
  `xenc` family, since it's a hash output, not a ciphertext).

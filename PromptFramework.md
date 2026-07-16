# SAPIC+ Security-Protocol Prompt Framework

Fill in every `⟨…⟩` placeholder and follow every `[Instruction: …]` note to instantiate this framework for a specific security protocol. The completed text is a prompt to be given to an LLM, which should then produce a full Tamarin Prover model of the protocol written in the SAPIC+ process calculus.

---

## 1. Summary

Write a formal security-protocol model in Tamarin Prover using the SAPIC+ process calculus (applied-pi style `let`/`process` blocks, **not** multiset rewrite rules). The protocol to model is **⟨protocol name and version⟩**, in which ⟨one- or two-sentence informal description of the message flow: who initiates, how many passes/messages, what the protocol is meant to achieve — e.g., authentication, key exchange, payload secrecy⟩.

*[Instruction: Keep the summary to the protocol's essential shape — roles, number of message passes, and the security goal. Do not describe message contents here; that belongs in the Roles section.]*

## 2. Cryptographic setup

* Use the built-in equational theories for ⟨list each required primitive: e.g., asymmetric (public-key) encryption, digital signatures, symmetric encryption, Diffie–Hellman exponentiation, XOR⟩.
* Declare any additional user-defined function symbols: ⟨e.g., a one-argument hash function `h`; a MAC function `mac/2`; a key-derivation function `kdf/2`⟩, together with any user-defined equations they require.
* ⟨If the protocol needs them, state restrictions or global assumptions here: e.g., equality checks, uniqueness of identities, trusted setup, PKI assumptions.⟩

*[Instruction: Only declare primitives the protocol actually uses. Prefer built-in theories over hand-written equations wherever possible.]*

## 3. Roles

Model each protocol role as a separate process definition. For **each** role, specify:

* **Role name and informal identity** (e.g., Initiator (Alice), Responder (Bob), Server (S)) — **parameters:** ⟨the keys and public values this role is instantiated with, e.g., its own private key, its own public key, the peer's public key, shared long-term keys⟩.
* A numbered step-by-step description of the role's behavior. For each step state, in order:
  1. **Role-claim event** — emit an event recording that the party is acting in this role, tagged with its identifying key or name.
  2. **Fresh-value generation** — list every fresh value the role creates (nonces, timestamps, session keys, payloads) and what each is for.
  3. **Message construction** — describe each outgoing message precisely as a tuple: which fields it contains, in what order, and which fields are encrypted, signed, MACed, or hashed, under which keys.
  4. **Message reception and checks** — for each incoming message, describe the pattern-match structure, all decryptions, and all verification steps (signature checks, MAC checks, equality checks). State explicitly which subsequent actions are conditional on successful verification.
  5. **Security-relevant events** — emit the events required by the lemmas (see the instruction block below).
  6. **Send/receive actions** — state exactly when each message is sent and received.

*[Instruction on events — read carefully: every lemma in Section 5 must be expressible purely in terms of events emitted by the processes. Work backwards from the lemma list and insert events at the semantically correct points:*
* *For **secrecy** lemmas: emit a `Secret(...)` event over the secret value (and the identities/keys of the parties who share it) at the point where each honest party considers the value secret.*
* *For **agreement/authentication** lemmas: emit a `Running(peer-view tuple)` event in the role being authenticated **before** it sends the message that convinces its peer, and a `Commit(same-shaped tuple)` event in the authenticating role **only after** all verifications succeed. The tuples must bind the same parameters (role tags, identities, and agreed data) in the same order on both sides.*
* *For **compromise-aware** lemmas: emit `Reveal(pk)` in the key-compromise helper, and `HonestA`/`HonestB` (or per-role equivalents) events at key creation in the top-level process, so lemmas can exclude or condition on compromised parties.*
* *For **executability/sanity** lemmas: ensure the events referenced (typically `Running` and `Commit`, or a dedicated `Finish` event) occur in one complete honest run.*
* *Add any further protocol-specific events (e.g., `SessionKey`, `OutMsg`, `Accept`) only if a lemma or a debugging/sanity check needs them.]*

* **Key-compromise helper** — a process that, given a long-term private key, emits a `Reveal` event on the corresponding public key (or identity) and outputs the private key to the attacker. *(Include one helper per kind of compromisable key.)*

## 4. Top-level process

Describe the overall system composition. Use unbounded replication (`!`) with this nesting:

* For each of unboundedly many ⟨first role⟩ instances: create the role's fresh long-term key(s), publish the corresponding public key(s) on the network, and emit an `Honest⟨RoleTag⟩` event on the public key.
* Nested inside (or in parallel, as the trust model requires), for each of unboundedly many ⟨second role⟩ instances: create its fresh key(s), publish the public part, and emit its `Honest⟨RoleTag⟩` event.
* ⟨Repeat for any further roles (e.g., a trusted server), stating whether they are replicated, unique, or shared across sessions.⟩
* In parallel, allow: compromise of each kind of long-term key (via the key-compromise helpers), and unboundedly many replicated runs of every role, each instantiated with the matching keys.

*[Instruction: The nesting determines which parties can talk to which. Nest a role inside another only if each instance of the inner role is bound to one specific instance of the outer role; otherwise compose them in parallel with a shared key infrastructure.]*

## 5. Lemmas to include

State each lemma informally but precisely, naming the events it quantifies over. Include at least:

1. **Secrecy** — the value flagged by a `Secret` event is never learned by the attacker (`K(...)`), unless one of the involved parties has been compromised (`Reveal`ed). ⟨Adapt to the protocol's secrets: payloads, session keys, etc. Add forward-secrecy variants if relevant.⟩
2. **Injective agreement (⟨authenticating role⟩'s view)** — whenever that role emits `Commit` on some tuple, there is an earlier matching `Running` event by the peer on the same tuple, and no second distinct `Commit` on that tuple (injectivity), unless a party was compromised. ⟨Add a symmetric lemma for the other direction if the protocol claims mutual authentication.⟩
3. **Non-injective agreement (same view)** — as above but without the injectivity/uniqueness condition.
4. **Sanity / executability** — an `exists-trace` lemma showing an honest run is possible: a `Running` and a matching `Commit` on the same tuple (or the protocol's completion events), with no party revealed.
5. ⟨Optional protocol-specific lemmas: key uniqueness, session-key agreement, forward secrecy, non-repudiation, freshness/replay resistance — each stated over events introduced in Section 3.⟩

*[Instruction: Before finalizing, cross-check that every event name used in a lemma is emitted somewhere in Section 3 or 4, with the same arity and argument order. If a lemma needs an event that no process emits, go back and add it at the semantically correct point.]*

## 6. Conclusive sentence

Name the theory something like `⟨PROTOCOL_NAME_IDENTIFIER⟩` (a valid Tamarin identifier). Use consistent role tags ⟨e.g., `'A'`, `'B'`, `'S'`⟩ in all agreement tuples, and keep event names, arities, and argument orders identical between the process definitions and the lemmas.

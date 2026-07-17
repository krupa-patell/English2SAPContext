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
* **Compromise scenario:** ⟨State explicitly whether long-term key compromise is part of the threat model. Choose one: (a) "No key compromise is modeled." or (b) "Long-term ⟨kind of⟩ keys may be compromised."⟩

*[Instruction: Only declare primitives the protocol actually uses. Prefer built-in theories over hand-written equations wherever possible.]*

*[Instruction on the compromise scenario — read carefully: include key-compromise modeling (option (b)) **only if** at least one of the following holds:*
1. *the user has explicitly asked for key compromise, key reveal, corrupted parties, or a compromise-aware threat model; or*
2. *the protocol's nature or its target properties inherently require it — e.g., the property list includes forward secrecy, post-compromise security, key-compromise impersonation resistance, or any lemma whose standard formulation is stated "unless a party is compromised."*

*If neither condition holds, choose option (a): omit the key-compromise helpers, the `Reveal`/`Honest⟨RoleTag⟩` events, and all compromise clauses in the lemmas. Do not add compromise machinery "just in case" — an unused `Reveal` process needlessly enlarges the attacker's capabilities and the proof search space. Record the choice here so the rest of the framework can be instantiated consistently.]*

## 3. Roles

Model each protocol role as a separate process definition. For **each** role, specify:

* **Role name and informal identity** (e.g., Server (S), Client (C)) — **parameters:** ⟨the keys and public values this role is instantiated with, e.g., its own private key, its own public key, the peer's public key, shared long-term keys⟩.
* A numbered step-by-step description of the role's behavior. Cover, in order, whichever of the following the role actually has — this is a checklist of possible step kinds, not a quota to fill:
  1. **Role-claim event** *(only if a lemma in Section 5 quantifies over the role's participation)* — emit an event recording that the party is acting in this role, tagged with its identifying key or name.
  2. **Fresh-value generation** — list every fresh value the role creates (nonces, timestamps, session keys, payloads) and what each is for. Do not add events marking the generation unless a lemma needs them.
  3. **Message construction** — describe each outgoing message. If message consists of multiple values, represent it precisely as a tuple: which fields it contains, in what order, and which fields are encrypted, signed, MACed, or hashed, under which keys.
  4. **Message reception and checks** — for each incoming message, describe the pattern-match structure, all decryptions, and all verification steps (signature checks, MAC checks, equality checks). State explicitly which subsequent actions are conditional on successful verification.
  5. **Security-relevant events** — emit exactly the events the lemma section requires, no more (see the instruction block below).
  6. **Send/receive actions** — state exactly when each message is sent and received.

*[Instruction on scope — read carefully: emit only events that some lemma in Section 5 actually references; work backwards from the (possibly empty) lemma selection, never forwards from this checklist. If the protocol states no security goal beyond executability, restrict events to the completion events the executability lemma needs, and skip role-claim events and fresh-value-generation events entirely. An event no lemma quantifies over is noise: it bloats the model and the proof search without testing anything.]*

If protocol requires the following lemmas to prove the security property, refer to the below:

*[Instruction on events — read carefully: every lemma in Section 5 must be expressible purely in terms of events emitted by the processes. Work backwards from the lemma list and insert events at the semantically correct points:*
* *For **secrecy** lemmas: emit a `Secret(...)` event over the secret value (and the identities/keys of the parties who share it) at the point where each honest party considers the value secret.*
* *For **agreement/authentication** lemmas: emit a `Running(peer-view tuple)` event in the role being authenticated **before** it sends the message that convinces its peer, and a `Commit(same-shaped tuple)` event in the authenticating role **only after** all verifications succeed. The tuples must bind the same parameters (role tags, identities, and agreed data) in the same order on both sides.*
* ***Only if the compromise scenario in Section 2 is option (b):** for **compromise-aware** lemmas, emit `Reveal(pk)` in the key-compromise helper, and `HonestA`/`HonestB` (or per-role equivalents) events at key creation in the top-level process, so lemmas can exclude or condition on compromised parties. If the compromise scenario is option (a), emit none of these events.*
* *For **executability/sanity** lemmas: ensure the events referenced (typically `Running` and `Commit`, or a dedicated `Finish` event) occur in one complete honest run.*
* *Add any further protocol-specific events (e.g., `SessionKey`, `OutMsg`, `Accept`) only if a lemma or a debugging/sanity check needs them.]*

*[Instruction on variable naming — when a role receives an unverified value over the network that stands in for another party's identity or key (e.g., a peer's public key read via `in(...)`), bind it to a name that is NOT also used as that party's own key parameter elsewhere in the theory. Reusing the same identifier (e.g. naming an incoming value `pkB` when `pkB` is also role B's own parameter) can be captured/conflated by the SAPIC+-to-multiset-rewrite translation, producing a "Variable bound twice" wellformedness warning — Tamarin will still run but flags its proof results as untrustworthy. Prefer a name that marks the value as received/unverified (e.g. `peerPk`, `claimedPk`) instead of the genuine owner's canonical name.]*

* **Key-compromise helper** *(include only if the compromise scenario in Section 2 is option (b))* — a process that, given a long-term private key, emits a `Reveal` event on the corresponding public key (or identity) and outputs the private key to the attacker. *(If included, add one helper per kind of compromisable key. If the compromise scenario is option (a), omit this bullet entirely from the instantiated prompt.)*

## 4. Top-level process

Describe the overall system composition. Use unbounded replication (`!`) with this nesting:

* For each of unboundedly many ⟨first role⟩ instances: create the role's fresh long-term key(s) and publish the corresponding public key(s) on the network. ⟨If the compromise scenario is option (b), also emit an `Honest⟨RoleTag⟩` event on the public key; otherwise omit it.⟩
* Nested inside (or in parallel, as the trust model requires), for each of unboundedly many ⟨second role⟩ instances: create its fresh key(s) and publish the public part. ⟨Again, emit its `Honest⟨RoleTag⟩` event only under option (b).⟩
* ⟨Repeat for any further roles (e.g., a trusted server), stating whether they are replicated, unique, or shared across sessions.⟩
* In parallel, allow: unboundedly many replicated runs of every role, each instantiated with the matching keys. ⟨**Only under option (b):** additionally compose, in parallel, compromise of each kind of long-term key via the key-compromise helpers.⟩

*[Instruction: The nesting determines which parties can talk to which. Nest a role inside another only if each instance of the inner role is bound to one specific instance of the outer role; otherwise compose them in parallel with a shared key infrastructure.]*

If protocol requires the following lemmas to prove the security property, refer to the below:

## 5. Lemmas to include

State each lemma informally but precisely, naming the events it quantifies over. Phrase every lemma consistently with the compromise scenario chosen in Section 2: under option (a), state the properties unconditionally and reference no `Reveal` or `Honest` events; under option (b), include the standard compromise exclusions ("unless a party was compromised/`Reveal`ed").

1. **Sanity / executability (mandatory — every protocol)** — an `exists-trace` lemma showing an honest run is possible: a `Running` and a matching `Commit` on the same tuple (or the protocol's completion events)⟨, with no party revealed — option (b) only; under option (a) no such side condition is needed⟩. This is the only lemma required regardless of the protocol's goals.
2. ⟨Selected security properties — from the accompanying property lemma catalog, choose exactly the properties that test the security goals this protocol's description states or implies, and no others. Name each chosen property as in the catalog (e.g. `secrecy`, `injective_agreement`, `perfect_forward_secrecy`, `replay_resistance`) and state it over this protocol's events. Typical mappings: authentication claims → the appropriate level of the authentication hierarchy (aliveness up to injective agreement; add a symmetric lemma per direction for mutual authentication); confidentiality claims → `secrecy`; key establishment → session-key agreement/uniqueness/confirmation as claimed; one-way or timestamped messages → replay resistance or message-origin authenticity. If a chosen property inherently presupposes key compromise (forward secrecy, post-compromise security, key-compromise impersonation resistance), revisit Section 2 and switch the compromise scenario to option (b) before including it.⟩
3. ⟨Optional sanity refinements guarding the chosen properties against vacuity: `secrecy_non_vacuity` when a secrecy lemma is included, `per_phase_reachability` for multi-phase or branching protocols.⟩

*[Instruction: Do not request properties the protocol does not claim — e.g. no agreement lemmas for a protocol with no authentication goal, no key-establishment lemmas when no key is established. Before finalizing, cross-check that every event name used in a lemma is emitted somewhere in Section 3 or 4, with the same arity and argument order. If a lemma needs an event that no process emits, go back and add it at the semantically correct point. In particular, verify the compromise scenario is consistent end-to-end: `Reveal`/`Honest` events, key-compromise helpers, and compromise clauses in lemmas must either all be present (option (b)) or all be absent (option (a)) — never a mixture.]*

## 6. Conclusive sentence

Name the theory something like `⟨PROTOCOL_NAME_IDENTIFIER⟩` (a valid Tamarin identifier). Use consistent role tags ⟨e.g., `'A'`, `'B'`, `'S'`⟩ in all agreement tuples, and keep event names, arities, and argument orders identical between the process definitions and the lemmas.

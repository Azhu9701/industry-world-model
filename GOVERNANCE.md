# WORLD.md Governance

WORLD.md is intended to be an open, vendor-neutral convention.

The goal of governance is not to prevent implementations, forks, or extensions. It is to keep one public canonical specification whose history, compatibility rules, and changes are easy to inspect.

## Canonical project

The current canonical project is:

https://github.com/Azhu9701/industry-world-model

The canonical specification consists of:

- `WORLD.md`
- `SPECIFICATION.md`
- `CONFORMANCE.md`
- `ORIGIN.md`
- `CHANGELOG.md`
- `SPEC-LICENSE.md`
- this governance document

The Industry World Model runtime and robotics pack are reference implementations. They do not have special authority to redefine the portable specification without a specification change.

## How changes happen

Normative WORLD.md changes should:

1. be proposed publicly;
2. explain the real interoperability problem being solved;
3. identify compatibility impact;
4. update the specification and conformance language together when needed;
5. update `CHANGELOG.md`;
6. prefer evidence from real implementations over speculative complexity.

Ordinary implementation changes do not require a specification change.

## Decision principles

Specification decisions should prefer:

1. interoperability over vendor-specific advantage;
2. simplicity over premature abstraction;
3. observable real-world need over hypothetical completeness;
4. explicit uncertainty over fabricated certainty;
5. backward compatibility when it does not block correctness;
6. portable semantics over one implementation's internal schema.

## Maintainers

Current repository maintainers steward the canonical history and merge specification changes.

Maintainer authority is procedural, not semantic ownership of every implementation. A maintainer cannot make a vendor extension canonical merely by using it privately; it must enter the public specification through the same change process.

## Forks and extensions

Forking is allowed and expected.

A fork should not imply that its local changes are part of the canonical WORLD.md specification unless those changes are merged into the canonical project.

Implementations are encouraged to say exactly what they support, for example:

- `WORLD.md v0.1 compatible`
- `WORLD.md v0.1 + ExampleCorp extension`
- `Derived from WORLD.md v0.1; not conformant`

This keeps experimentation open without erasing compatibility boundaries.

## Neutrality

WORLD.md is not tied to AIMAN, OpenAI, Anthropic, Google, a particular model family, or a particular runtime.

AIMAN.World and the Industry World Model work are part of the documented origin of this specification, not a requirement for adoption.

## Future governance

If WORLD.md gains meaningful independent adoption, the preferred direction is broader and eventually neutral governance rather than permanent control by one company or vendor.

Any transfer to a foundation or standards body should preserve:

- the public Git history;
- published version history;
- attribution and provenance;
- compatibility guarantees;
- open contribution rights.

The purpose of neutral governance would be to increase trust in the standard, not to rewrite its origin.

# Decision Packet adapter

This adapter is the bridge from AIMAN Sensor / Kev decisions into the public World Model Contribution Protocol.

It accepts a Decision Packet containing:

- source provenance;
- the decision layer (content_type, is_event, event_type, timeline_worthy, commercialization_stage, source_quality, needs_second_source);
- extracted entities, claims, relations, and an optional event.

It produces an IWM v0.3 Contribution Packet.

## Important boundary

The adapter never converts a model decision into verified truth.

Every generated Claim, Relation, and Event is status=proposed. The original decision fields are retained under contribution.metadata so reviewers can see why the Sensor routed the item into the World Model.

If needs_second_source=true, the adapter adds a needs_second_source review flag rather than blocking the contribution. The contribution can enter review, but it cannot self-promote to verified.

## Run

    python scripts/decision-packet-to-contribution.py \
      examples/robotics/viabot-series-a-decision-packet.json

The Viabot Series A fixture is based on a real 2026-09-17 company announcement. CI requires the adapter output to exactly match the committed real contribution, which makes packet/adapter drift visible immediately.

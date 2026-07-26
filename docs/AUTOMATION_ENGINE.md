# Automation Engine — Sprint 5

Pipeline:

**Measurements → Dynamic Zendure values → EMS Core → Automation policy → Safety gates → Simulated output**

Policy: `grid_zero_discharge_v1`

The first automation policy focuses on controlled discharge toward the configured grid target.

The engine intentionally does not implement real device writes. Future actuator work must remain a separate layer with explicit safety review.

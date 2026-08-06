# v0.5.8 — Config Flow Hotfix

## Symptom

The v0.4.2 setup form displayed all expected selectors but submission could fail with:

`extra keys not allowed @ data[...]`

for every field in the first setup step.

## Correction

The first-step schema is now a single explicit Voluptuous schema whose accepted keys never change.

Suggested/default values are applied with Home Assistant's `add_suggested_values_to_schema`
instead of reconstructing the schema around submitted values.

Battery serial validation is performed after submission rather than chaining a text selector
inside another Voluptuous validator.

## Battery onboarding

Supported battery types:
- AB2000X
- AB3000L
- I2400

Serial numbers must contain exactly five digits and preserve leading zeroes.

## Safety

No real Zendure output-limit write is enabled.

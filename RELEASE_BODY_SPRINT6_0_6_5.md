# Carpiquet EMS v0.6.5-alpha — Entity Mapper Shadow

This build introduces the normalized `systems[]` architecture in parallel with the validated v0.6.4 engine. The mapper is diagnostic/read-only and cannot influence EMS commands. Simulation logs now carry mapper and per-system snapshots so parity can be validated on the real Home Assistant installation before any engine cut-over.

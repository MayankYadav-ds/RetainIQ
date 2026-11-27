# Data storage

Only schemas and this guide belong here in Git. The operator CLI creates ignored raw/, staging/ and processed/ directories as needed. Published version directories contain a manifest, canonical records, protected partitions and aggregate reports. Use the [operator guide](../docs/DATA_ENGINEERING.md) and [evaluation protocol](../docs/EVALUATION_PROTOCOL.md). Both JSON schemas are generated from the runtime Pydantic contracts and tested for drift. Source data retains its own license. The deterministic synthetic test fixture is generated in code.

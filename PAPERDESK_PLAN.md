# Automated paperdesk v1

Research-only. No broker access or live orders.

1. Schedule existing collector hourly and retain manual dispatch.
2. Validate data before processing; ignore unfinished hourly bars.
3. Maintain persistent journal with unique symbol/time/direction IDs.
4. Bootstrap on first run without inventing historical fills.
5. Predefine signals, simulated next-bar entry, stop, target and risk limits.
6. Account for spread, fees, missing bars and adverse stop/target collisions.
7. Restore previous state across workflow runs and publish new state as an artifact.
8. Add tests for duplicates, missing data, gaps, restarts and signal timing.
9. Keep live execution disabled pending separate review and authorization.

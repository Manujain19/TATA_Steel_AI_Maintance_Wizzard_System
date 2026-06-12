# Maintenance SOP Extracts

## Vibration alarm SOP

1. Acknowledge the alarm and capture equipment ID, timestamp, coil ID, speed,
   vibration, temperature, and recent maintenance activity.
2. If vibration is above trip level or paired with abnormal temperature rise,
   reduce load and prepare controlled stop.
3. Inspect lubrication flow, bearing temperature, coupling condition, and
   mechanical looseness.
4. If vibration normalizes after load reduction, continue at restricted speed
   and schedule inspection within 24 hours.
5. If vibration remains high, stop equipment and complete bearing/coupling
   inspection before restart.

## Hydraulic pressure instability SOP

1. Confirm sensor reading from local gauge and control system historian.
2. Check pump, accumulator pressure, valve leakage, and seal condition.
3. If pressure drop affects a critical motion, stop the motion sequence and
   isolate the hydraulic circuit.
4. Review spare availability for seal kit, servo valve, and hose assembly.
5. Record action taken and actual root cause in the digital maintenance log.

## Catastrophic failure warning rule

Generate a critical warning when an equipment item has at least two breached
condition limits and one of the breached limits is tied to a high-criticality
failure mode in the knowledge base. Treat low spare availability or lead time
above 14 days as an escalation factor.


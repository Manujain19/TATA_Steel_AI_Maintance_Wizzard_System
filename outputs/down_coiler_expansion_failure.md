# Maintenance Wizard Report

Generated: 2026-06-06T19:07:35.359043+00:00
Equipment: HRM-COIL-03 - Down Coiler Mandrel
Active alert: MANDREL_EXPANSION_FAIL

## Diagnosis
- Probable fault: MANDREL_EXPANSION_FAIL
- Risk: critical (87.4)
- Urgency: immediate

Root causes:
- Hydraulic valve leakage and worn mandrel segment
- Wrapper roll misalignment

Condition breaches:
- temperature_c: 76.0 breached warn limit 75.0
- vibration_mm_s: 5.4 breached warn limit 4.5
- motor_current_a: 355.0 breached warn limit 320.0
- hydraulic_pressure_bar: 118.0 breached warn limit 120.0

## Prediction
- Health index: 0.0
- Estimated RUL: Immediate intervention
- RUL explanation: Current service age and active condition breaches have exhausted the safe operating window.
- Method: service interval adjusted by current condition breaches

## Recommended Actions
1. Move equipment to restricted operation and prepare a controlled stop window.
2. Inspect wrapper roll alignment, mandrel segment wear, and expansion-drive looseness.
3. Confirm hydraulic pressure locally, inspect valve leakage, and prepare seal kit replacement.
4. Trend motor current against load; inspect mechanical drag and expansion timing.
5. Use prior case FH-005 as reference: Held production, changed valve, planned segment replacement.
6. Procurement action: mandrel segment set has qty=0 and lead_time=28 days; escalate now.
7. Create digital log entry for HRM-COIL-03 with alert MANDREL_EXPANSION_FAIL.

## Traceability
- failure_history / FH-005 (score 12.0): HRM-COIL-03 Down Coiler Mandrel Mandrel expansion system: MANDREL_EXPANSION_FAIL. Symptoms: tail-end slip; high wrapping current; telescopic coil. Root cause: Hydraulic valve leakage and worn mandrel segment. Action: Held production, changed valve, planned segment replacement.
- equipment_manuals / HRM-COIL-03 down coiler mandrel (score 11.0): Criticality: critical Common symptoms: - Coil tail-end slip. - Mandrel expansion fault. - High motor current during wrapping. - Telescopic coil formation. Likely causes: - Mandrel segment wear. - Hydraulic expansion pressure loss. - Wrapper roll misalignment. - Control timing mismatch at tail end. Checks: - Verify mandrel hydraulic pressure during expansion. - Inspect mandrel segment surface condition. - Check wra...
- failure_history / FH-006 (score 10.0): HRM-COIL-03 Down Coiler Mandrel Wrapper roll: WRAPPER_MISALIGN. Symptoms: telescopic coil; wrapper roll vibration. Root cause: Wrapper roll misalignment. Action: Aligned wrapper roll and updated tail-end timing.
- maintenance_sops / Hydraulic pressure instability SOP (score 3.0): 1. Confirm sensor reading from local gauge and control system historian. 2. Check pump, accumulator pressure, valve leakage, and seal condition. 3. If pressure drop affects a critical motion, stop the motion sequence and isolate the hydraulic circuit. 4. Review spare availability for seal kit, servo valve, and hose assembly. 5. Record action taken and actual root cause in the digital maintenance log.
- maintenance_sops / Vibration alarm SOP (score 2.0): 1. Acknowledge the alarm and capture equipment ID, timestamp, coil ID, speed, vibration, temperature, and recent maintenance activity. 2. If vibration is above trip level or paired with abnormal temperature rise, reduce load and prepare controlled stop. 3. Inspect lubrication flow, bearing temperature, coupling condition, and mechanical looseness. 4. If vibration normalizes after load reduction, continue at restri...

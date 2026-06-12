# Maintenance Wizard Report

Generated: 2026-06-06T19:07:35.306130+00:00
Equipment: HRM-ROLL-01 - Finishing Mill Work Roll
Active alert: VIBRATION_HIGH

## Diagnosis
- Probable fault: VIBRATION_HIGH
- Risk: critical (86.4)
- Urgency: immediate

Root causes:
- Bearing wear with low lubrication flow
- Loose chock clamp after roll change

Condition breaches:
- temperature_c: 82.0 breached warn limit 75.0
- vibration_mm_s: 8.1 breached trip limit 7.1
- oil_pressure_bar: 2.1 breached warn limit 2.8
- roll_gap_variation_mm: 0.42 breached trip limit 0.4

## Prediction
- Health index: 0.0
- Estimated RUL: Immediate intervention
- RUL explanation: Current service age and active condition breaches have exhausted the safe operating window.
- Method: service interval adjusted by current condition breaches

## Recommended Actions
1. Move equipment to restricted operation and prepare a controlled stop window.
2. Inspect bearing condition, coupling looseness, and lubrication flow before next campaign.
3. Verify oil pump delivery and clean lubrication filters immediately.
4. Check roll alignment, chock clamp torque, and recent roll-change setup.
5. Use prior case FH-001 as reference: Reduced speed, restored lube flow, replaced bearing in planned stop.
6. Procurement action: bearing seal kit has qty=0 and lead_time=16 days; escalate now.
7. Create digital log entry for HRM-ROLL-01 with alert VIBRATION_HIGH.

## Traceability
- equipment_manuals / HRM-ROLL-01 finishing mill work roll assembly (score 14.0): Criticality: high Common symptoms: - High vibration near the drive-side bearing. - Roll gap variation during high-speed passes. - Surface chatter marks on finished strip. - Rising bearing temperature after coil threading. Likely causes: - Work roll bearing wear or lubrication starvation. - Mill stand misalignment after roll change. - Loose chock clamp or damaged bearing seal. - Process instability from speed misma...
- failure_history / FH-001 (score 13.0): HRM-ROLL-01 Finishing Mill Work Roll Drive-side bearing: VIBRATION_HIGH. Symptoms: drive side vibration; bearing temperature rise; chatter marks. Root cause: Bearing wear with low lubrication flow. Action: Reduced speed, restored lube flow, replaced bearing in planned stop.
- failure_history / FH-002 (score 9.0): HRM-ROLL-01 Finishing Mill Work Roll Chock clamp: ROLL_GAP_UNSTABLE. Symptoms: roll gap variation; strip thickness deviation. Root cause: Loose chock clamp after roll change. Action: Retorqued clamp, checked alignment, monitored next 20 coils.
- maintenance_sops / Vibration alarm SOP (score 6.0): 1. Acknowledge the alarm and capture equipment ID, timestamp, coil ID, speed, vibration, temperature, and recent maintenance activity. 2. If vibration is above trip level or paired with abnormal temperature rise, reduce load and prepare controlled stop. 3. Inspect lubrication flow, bearing temperature, coupling condition, and mechanical looseness. 4. If vibration normalizes after load reduction, continue at restri...
- maintenance_sops / Hydraulic pressure instability SOP (score 4.0): 1. Confirm sensor reading from local gauge and control system historian. 2. Check pump, accumulator pressure, valve leakage, and seal condition. 3. If pressure drop affects a critical motion, stop the motion sequence and isolate the hydraulic circuit. 4. Review spare availability for seal kit, servo valve, and hose assembly. 5. Record action taken and actual root cause in the digital maintenance log.

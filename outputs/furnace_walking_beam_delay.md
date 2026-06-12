# Maintenance Wizard Report

Generated: 2026-06-06T19:07:35.439734+00:00
Equipment: HRM-FURN-02 - Reheating Furnace Walking Beam
Active alert: HYD_PRESS_LOW

## Diagnosis
- Probable fault: HYD_PRESS_LOW
- Risk: high (66.1)
- Urgency: immediate

Root causes:
- Actuator seal leakage
- Position sensor drift

Condition breaches:
- hydraulic_pressure_bar: 92.0 breached trip limit 95.0

## Prediction
- Health index: 29.8
- Estimated RUL: 476 hours
- RUL explanation: Estimated remaining useful life from service age and condition penalties.
- Method: service interval adjusted by current condition breaches

## Recommended Actions
1. Move equipment to restricted operation and prepare a controlled stop window.
2. Confirm hydraulic pressure locally, inspect valve leakage, and prepare seal kit replacement.
3. Use prior case FH-003 as reference: Isolated circuit, changed seal kit, refilled hydraulic oil.
4. Procurement action: servo valve has qty=1 and lead_time=21 days; escalate now.
5. Procurement action: hydraulic seal kit has qty=0 and lead_time=18 days; escalate now.
6. Create digital log entry for HRM-FURN-02 with alert HYD_PRESS_LOW.

## Traceability
- failure_history / FH-003 (score 8.0): HRM-FURN-02 Reheating Furnace Walking Beam Hydraulic actuator: HYD_PRESS_LOW. Symptoms: walking beam delay; hydraulic pressure drop. Root cause: Actuator seal leakage. Action: Isolated circuit, changed seal kit, refilled hydraulic oil.
- failure_history / FH-004 (score 8.0): HRM-FURN-02 Reheating Furnace Walking Beam Position sensor: BEAM_POSITION_ERR. Symptoms: transfer delay; position mismatch. Root cause: Position sensor drift. Action: Recalibrated sensor and cleaned scale near guide.
- equipment_manuals / HRM-FURN-02 reheating furnace walking beam (score 5.0): Criticality: high Common symptoms: - Slab transfer delay. - Hydraulic pressure instability. - Uneven furnace zone temperature. - Walking beam position error. Likely causes: - Hydraulic actuator leakage. - Scale buildup around skid or beam guides. - Furnace zone burner imbalance. - Position sensor drift. Checks: - Compare hydraulic pressure with walking beam travel time. - Inspect skid/beam guide for mechanical obs...
- maintenance_sops / Hydraulic pressure instability SOP (score 3.0): 1. Confirm sensor reading from local gauge and control system historian. 2. Check pump, accumulator pressure, valve leakage, and seal condition. 3. If pressure drop affects a critical motion, stop the motion sequence and isolate the hydraulic circuit. 4. Review spare availability for seal kit, servo valve, and hose assembly. 5. Record action taken and actual root cause in the digital maintenance log.
- maintenance_sops / Catastrophic failure warning rule (score 2.0): Generate a critical warning when an equipment item has at least two breached condition limits and one of the breached limits is tied to a high-criticality failure mode in the knowledge base. Treat low spare availability or lead time above 14 days as an escalation factor.

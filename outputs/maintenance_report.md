# Maintenance Wizard - Tata Steel AI Platform Maintenance Report

AI-Powered Industrial Reliability & Maintenance Intelligence

Generated: 2026-06-12T11:47:22.598351+00:00
Equipment: TSA-RM-MTR-001 - Rolling Mill Drive Motor
Active alert: EARLY_WARNING

## Diagnosis
- Probable fault: winding insulation degradation
- Risk: high (87.4)
- Urgency: immediate

Root causes:
- thermal overload
- rotor eccentricity

Condition breaches:
- vibration_mm_s: 4.97 breached warn limit 4.5
- motor_current_a: 337.8 breached warn limit 320.0
- oil_pressure_bar: 2.5 breached warn limit 2.8
- hydraulic_pressure_bar: 106.7 breached warn limit 120.0

## Prediction
- Health index: 0.0
- Estimated RUL: 1332 hours
- RUL explanation: Uses Rolling Mill Drive Motor digital twin health, rated hours, active sensor anomalies, and asset-specific failure history.
- Method: asset digital twin RUL blended with current condition breaches

## Recommended Actions
1. Move Rolling Mill Drive Motor to restricted operation and prepare a controlled stop window.
2. Investigate winding insulation degradation caused by thermal overload; execute: Perform insulation resistance test.
3. Perform vibration spectrum review, rotor balance check, and motor bearing inspection.
4. Verify oil pump delivery, inspect lubrication circuit restriction, and clean asset-specific filters.
5. Confirm hydraulic pressure locally, inspect pump cavitation, valve leakage, and seal failure paths.
6. Trend motor current against load; inspect mechanical drag and expansion timing.
7. Use prior case FH-0015 as reference: Perform insulation resistance test.
8. Procurement action: cooling fan assembly has qty=0 and lead_time=35 days; escalate now.
9. Procurement action: cooling fan assembly has qty=5 and lead_time=35 days; escalate now.
10. Procurement action: cooling fan assembly has qty=2 and lead_time=35 days; escalate now.
11. Procurement action: cooling fan assembly has qty=0 and lead_time=14 days; escalate now.
12. Procurement action: RTD temperature sensor has qty=0 and lead_time=7 days; escalate now.
13. Create digital log entry for TSA-RM-MTR-001 with alert EARLY_WARNING.

## Traceability
- failure_history / FH-0015 (score 22.0): TSA-RM-MTR-001 Rolling Mill Drive Motor overheating: OVERHEATING. Symptoms: overheating pattern with vibration 4.97 mm/s, pressure 106.7 bar, oil quality 55.6. Root cause: rotor eccentricity. Action: Perform insulation resistance test.
- failure_history / FH-0077 (score 22.0): TSA-RM-MTR-001 Rolling Mill Drive Motor overheating: OVERHEATING. Symptoms: overheating pattern with vibration 4.97 mm/s, pressure 106.7 bar, oil quality 55.6. Root cause: rotor eccentricity. Action: Perform insulation resistance test.
- failure_history / FH-0104 (score 22.0): TSA-RM-MTR-001 Rolling Mill Drive Motor overheating: OVERHEATING. Symptoms: overheating pattern with vibration 4.97 mm/s, pressure 106.7 bar, oil quality 55.6. Root cause: rotor eccentricity. Action: Inspect rotor balance and cooling fan.
- failure_history / FH-0136 (score 22.0): TSA-RM-MTR-001 Rolling Mill Drive Motor overheating: OVERHEATING. Symptoms: overheating pattern with vibration 4.97 mm/s, pressure 106.7 bar, oil quality 55.6. Root cause: rotor eccentricity. Action: Perform insulation resistance test.
- failure_history / FH-0145 (score 22.0): TSA-RM-MTR-001 Rolling Mill Drive Motor overheating: OVERHEATING. Symptoms: overheating pattern with vibration 4.97 mm/s, pressure 106.7 bar, oil quality 55.6. Root cause: rotor eccentricity. Action: Inspect rotor balance and cooling fan.

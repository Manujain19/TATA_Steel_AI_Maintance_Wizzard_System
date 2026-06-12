from __future__ import annotations

import json
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
DATA_DIR = ROOT_DIR / "data"


ASSETS = [
    ("TSA-RM-MTR-001", "Rolling Mill Drive Motor", "Rolling Mill", "Drive Motor", "critical", 74, "high"),
    ("TSA-RM-GBX-002", "Rolling Mill Gearbox", "Rolling Mill", "Gearbox", "critical", 68, "high"),
    ("TSA-RM-HPP-003", "Hydraulic Power Pack", "Rolling Mill", "Hydraulic System", "critical", 59, "critical"),
    ("TSA-BF-BLR-004", "Blast Furnace Blower", "Blast Furnace", "Blower", "critical", 82, "medium"),
    ("TSA-BF-CPM-005", "Blast Furnace Cooling Pump", "Blast Furnace", "Cooling Pump", "critical", 64, "high"),
    ("TSA-BF-HBV-006", "Hot Blast Valve", "Blast Furnace", "Valve", "critical", 71, "high"),
    ("TSA-SMS-APU-007", "Argon Purging Unit", "Steel Melting Shop", "Gas System", "high", 86, "low"),
    ("TSA-SMS-LTC-008", "Ladle Transfer Car", "Steel Melting Shop", "Transfer Car", "critical", 77, "medium"),
    ("TSA-CCM-ROL-009", "Continuous Casting Roller", "Steel Melting Shop", "Caster Roller", "critical", 55, "critical"),
    ("TSA-CKE-EFN-010", "Coke Oven Exhaust Fan", "Coke Oven", "Exhaust Fan", "high", 73, "medium"),
    ("TSA-UTL-GCP-011", "Gas Compressor", "Utilities", "Compressor", "critical", 61, "high"),
    ("TSA-SIN-CDR-012", "Sinter Conveyor Drive", "Sinter Plant", "Conveyor Drive", "high", 79, "medium"),
    ("TSA-SIN-EFN-013", "Sinter Exhaust Fan", "Sinter Plant", "Exhaust Fan", "critical", 66, "high"),
    ("TSA-RMH-CNV-014", "Raw Material Conveyor", "Sinter Plant", "Conveyor", "high", 88, "low"),
    ("TSA-UTL-DCF-015", "Dust Collection Fan", "Utilities", "Dust Collection", "high", 69, "high"),
    ("TSA-UTL-AHU-016", "Air Handling Unit", "Utilities", "Air Handling", "medium", 91, "low"),
    ("TSA-UTL-CTP-017", "Cooling Tower Pump", "Utilities", "Cooling Pump", "high", 76, "medium"),
    ("TSA-UTL-WTP-018", "Water Treatment Pump", "Utilities", "Water Pump", "high", 84, "low"),
    ("TSA-UTL-STG-019", "Steam Turbine Generator", "Utilities", "Steam Turbine", "critical", 62, "high"),
    ("TSA-RM-CNV-020", "Rolling Mill Conveyor System", "Rolling Mill", "Conveyor System", "high", 72, "medium"),
    ("TSA-BF-CHG-021", "Blast Furnace Charging Conveyor", "Blast Furnace", "Conveyor System", "critical", 57, "critical"),
    ("TSA-SMS-EAF-022", "Electric Arc Furnace Transformer", "Steel Melting Shop", "Transformer", "critical", 67, "high"),
    ("TSA-SIN-SCR-023", "Sinter Screen Drive", "Sinter Plant", "Screen Drive", "high", 81, "medium"),
    ("HRM-ROLL-01", "Finishing Mill Work Roll", "Rolling Mill", "Work Roll", "critical", 36, "critical"),
    ("HRM-COIL-03", "Down Coiler Mandrel", "Rolling Mill", "Coiler Mandrel", "critical", 31, "critical"),
]


ASSET_PROFILES = {
    "Drive Motor": {
        "failure_modes": ["winding insulation degradation", "rotor imbalance", "overheating"],
        "root_causes": ["thermal overload", "cooling fan fouling", "rotor eccentricity"],
        "spares": ["motor winding kit", "cooling fan assembly", "RTD temperature sensor", "drive-end bearing"],
        "actions": ["Perform insulation resistance test", "Thermography on stator body", "Inspect rotor balance and cooling fan"],
        "production_tph": 145,
        "repair_cost": 420000,
    },
    "Gearbox": {
        "failure_modes": ["gear wear", "oil contamination", "bearing failure"],
        "root_causes": ["low oil quality", "gear tooth pitting", "bearing race fatigue"],
        "spares": ["gearbox oil filter", "gear set", "bearing kit", "oil analysis kit"],
        "actions": ["Run oil debris analysis", "Borescope gear teeth", "Replace contaminated oil and filters"],
        "production_tph": 155,
        "repair_cost": 680000,
    },
    "Hydraulic System": {
        "failure_modes": ["pressure leak", "seal failure", "pump cavitation"],
        "root_causes": ["actuator seal leakage", "suction restriction", "servo valve internal leakage"],
        "spares": ["hydraulic seal kit", "servo valve", "pump cartridge", "pressure transmitter"],
        "actions": ["Pressure decay test", "Inspect suction strainer", "Replace leaking seal and validate servo valve"],
        "production_tph": 132,
        "repair_cost": 360000,
    },
    "Blower": {
        "failure_modes": ["impeller imbalance", "bearing temperature rise", "surge instability"],
        "root_causes": ["dust deposition on impeller", "bearing lubrication degradation", "inlet guide vane drift"],
        "spares": ["blower bearing kit", "impeller cleaning kit", "inlet guide actuator", "vibration probe"],
        "actions": ["Balance impeller", "Inspect bearing lubrication", "Validate inlet guide vane control"],
        "production_tph": 118,
        "repair_cost": 520000,
    },
    "Cooling Pump": {
        "failure_modes": ["pump cavitation", "seal leakage", "low flow"],
        "root_causes": ["blocked suction strainer", "mechanical seal wear", "impeller erosion"],
        "spares": ["mechanical seal", "impeller set", "pump bearing kit", "flow transmitter"],
        "actions": ["Check suction pressure", "Inspect mechanical seal", "Verify cooling-water flow"],
        "production_tph": 108,
        "repair_cost": 260000,
    },
    "Valve": {
        "failure_modes": ["valve sticking", "actuator leakage", "position drift"],
        "root_causes": ["scale buildup", "actuator seal damage", "positioner calibration drift"],
        "spares": ["valve actuator kit", "positioner", "seal set", "valve seat ring"],
        "actions": ["Stroke-test valve", "Inspect actuator leakage", "Recalibrate positioner"],
        "production_tph": 126,
        "repair_cost": 300000,
    },
    "Gas System": {
        "failure_modes": ["low argon flow", "control valve drift", "line restriction"],
        "root_causes": ["regulator drift", "flow-meter fouling", "line moisture ingress"],
        "spares": ["argon regulator", "flow meter", "control valve kit", "purge hose"],
        "actions": ["Validate flow meter", "Check regulator setting", "Inspect purge line restriction"],
        "production_tph": 86,
        "repair_cost": 180000,
    },
    "Transfer Car": {
        "failure_modes": ["drive chain wear", "wheel bearing failure", "position encoder fault"],
        "root_causes": ["rail misalignment", "bearing fatigue", "encoder contamination"],
        "spares": ["wheel bearing", "drive chain", "position encoder", "traction motor brush kit"],
        "actions": ["Inspect rails and wheels", "Check encoder feedback", "Verify traction current"],
        "production_tph": 97,
        "repair_cost": 340000,
    },
    "Caster Roller": {
        "failure_modes": ["roller bearing seizure", "cooling blockage", "surface scoring"],
        "root_causes": ["bearing water ingress", "spray nozzle blockage", "roll shell fatigue"],
        "spares": ["caster roller bearing", "spray nozzle set", "roller shell", "rotary union kit"],
        "actions": ["Inspect roller rotation", "Check spray cooling", "Replace damaged bearing assembly"],
        "production_tph": 138,
        "repair_cost": 610000,
    },
    "Exhaust Fan": {
        "failure_modes": ["fan imbalance", "belt slip", "bearing degradation"],
        "root_causes": ["dust buildup", "pulley misalignment", "lubrication starvation"],
        "spares": ["fan bearing kit", "drive belt set", "vibration sensor", "fan blade set"],
        "actions": ["Clean fan rotor", "Align belt drive", "Inspect fan bearings"],
        "production_tph": 92,
        "repair_cost": 240000,
    },
    "Compressor": {
        "failure_modes": ["compressor surge", "oil carryover", "bearing wear"],
        "root_causes": ["inlet filter restriction", "separator saturation", "thrust bearing wear"],
        "spares": ["compressor bearing", "oil separator", "inlet filter", "pressure control valve"],
        "actions": ["Inspect inlet filter", "Check separator differential pressure", "Trend discharge pressure"],
        "production_tph": 102,
        "repair_cost": 480000,
    },
    "Conveyor Drive": {
        "failure_modes": ["gear coupling wear", "belt overload", "motor overload"],
        "root_causes": ["misalignment", "material buildup", "coupling backlash"],
        "spares": ["gear coupling", "drive bearing", "belt scraper", "motor overload relay"],
        "actions": ["Inspect coupling alignment", "Check belt loading", "Clear material buildup"],
        "production_tph": 76,
        "repair_cost": 210000,
    },
    "Conveyor": {
        "failure_modes": ["idler seizure", "belt tracking fault", "pulley lagging wear"],
        "root_causes": ["idler bearing contamination", "skewed pulley", "material carryback"],
        "spares": ["idler roller", "belt fastener kit", "pulley lagging", "tracking sensor"],
        "actions": ["Inspect idlers", "Align belt tracking", "Clean carryback points"],
        "production_tph": 70,
        "repair_cost": 160000,
    },
    "Dust Collection": {
        "failure_modes": ["baghouse restriction", "fan vibration", "low suction"],
        "root_causes": ["filter bag blinding", "fan imbalance", "duct leakage"],
        "spares": ["filter bag set", "fan bearing", "differential pressure sensor", "duct damper actuator"],
        "actions": ["Check baghouse differential pressure", "Inspect fan rotor", "Seal duct leakage"],
        "production_tph": 64,
        "repair_cost": 220000,
    },
    "Air Handling": {
        "failure_modes": ["filter choking", "fan belt wear", "low airflow"],
        "root_causes": ["filter loading", "belt tension loss", "damper position drift"],
        "spares": ["air filter set", "fan belt", "damper actuator", "airflow sensor"],
        "actions": ["Replace filters", "Check fan belt tension", "Validate damper position"],
        "production_tph": 42,
        "repair_cost": 95000,
    },
    "Water Pump": {
        "failure_modes": ["low discharge pressure", "seal wear", "pump bearing noise"],
        "root_causes": ["impeller wear", "seal face damage", "bearing contamination"],
        "spares": ["mechanical seal", "pump bearing", "impeller set", "pressure transmitter"],
        "actions": ["Inspect discharge pressure", "Check seal leakage", "Verify bearing vibration"],
        "production_tph": 58,
        "repair_cost": 150000,
    },
    "Steam Turbine": {
        "failure_modes": ["blade vibration", "bearing oil contamination", "steam seal leakage"],
        "root_causes": ["rotor imbalance", "oil varnish formation", "gland seal wear"],
        "spares": ["turbine bearing", "steam seal kit", "governor valve kit", "oil purifier filter"],
        "actions": ["Trend shaft vibration", "Analyze turbine oil", "Inspect steam seal leakage"],
        "production_tph": 120,
        "repair_cost": 980000,
    },
    "Conveyor System": {
        "failure_modes": ["belt misalignment", "drive pulley wear", "idler seizure"],
        "root_causes": ["tracking drift", "pulley lagging wear", "idler bearing contamination"],
        "spares": ["belt fastener kit", "drive pulley lagging", "idler roller set", "tracking switch"],
        "actions": ["Inspect belt tracking", "Check pulley lagging", "Replace seized idlers"],
        "production_tph": 84,
        "repair_cost": 230000,
    },
    "Transformer": {
        "failure_modes": ["winding hot spot", "oil dielectric degradation", "tap changer wear"],
        "root_causes": ["overload heating", "moisture ingress", "tap contact erosion"],
        "spares": ["transformer oil filter", "temperature relay", "tap changer contact kit", "bushing gasket"],
        "actions": ["Run dissolved gas analysis", "Check winding temperature", "Inspect tap changer operation"],
        "production_tph": 142,
        "repair_cost": 1250000,
    },
    "Screen Drive": {
        "failure_modes": ["screen vibration imbalance", "exciter bearing wear", "deck clogging"],
        "root_causes": ["uneven material loading", "bearing fatigue", "screen aperture blinding"],
        "spares": ["exciter bearing", "screen deck panel", "vibration isolator", "drive coupling"],
        "actions": ["Inspect screen exciter", "Check deck clogging", "Balance screen drive"],
        "production_tph": 73,
        "repair_cost": 280000,
    },
    "Work Roll": {
        "failure_modes": ["bearing degradation", "roll-gap instability", "chatter vibration"],
        "root_causes": ["bearing lubrication loss", "chock looseness", "roll surface wear"],
        "spares": ["work roll bearing", "bearing seal kit", "chock clamp set", "lubrication flow sensor"],
        "actions": ["Inspect work-roll bearing", "Retorque chock clamp", "Restore lubrication flow"],
        "production_tph": 170,
        "repair_cost": 550000,
    },
    "Coiler Mandrel": {
        "failure_modes": ["mandrel expansion failure", "hydraulic valve leakage", "wrapper roll misalignment"],
        "root_causes": ["worn mandrel segment", "expansion valve leakage", "wrapper roll alignment drift"],
        "spares": ["mandrel segment set", "hydraulic expansion valve", "wrapper roll bearing", "position sensor"],
        "actions": ["Inspect mandrel segments", "Test expansion valve leakage", "Align wrapper roll"],
        "production_tph": 165,
        "repair_cost": 720000,
    },
}


def profile_for(asset: dict) -> dict:
    return ASSET_PROFILES.get(asset["type"], ASSET_PROFILES.get("Water Pump"))


FAILURE_MODES = [
    ("Bearing Overheating", "High vibration", "Bearing failure", "Inspect bearing, restore lubrication, replace seal kit"),
    ("Gearbox Degradation", "Low oil quality", "Gear tooth wear", "Oil analysis, borescope inspection, gearbox overhaul"),
    ("Motor Winding Risk", "High temperature", "Insulation breakdown", "Thermal scan, load reduction, winding resistance test"),
    ("Hydraulic Instability", "Pressure fluctuation", "Valve leakage or seal failure", "Pressure test, valve inspection, seal replacement"),
    ("Fan Imbalance", "High vibration", "Rotor imbalance", "Balance rotor, inspect foundation and coupling"),
    ("Pump Cavitation", "Low flow", "Cavitation and impeller wear", "Check suction, strainers, and impeller clearance"),
]


def risk_to_status(risk: str) -> str:
    return {
        "critical": "Immediate Intervention",
        "high": "Restricted Operation",
        "medium": "Watchlist",
        "low": "Available",
    }.get(risk, "Watchlist")


def build_equipment(now: datetime) -> list[dict]:
    records = []
    for index, (asset_id, name, area, asset_type, criticality, health, risk) in enumerate(ASSETS):
        rated = 50000 + index * 1800
        profile = ASSET_PROFILES.get(asset_type, ASSET_PROFILES["Water Pump"])
        records.append(
            {
                "id": asset_id,
                "name": name,
                "area": area,
                "type": asset_type,
                "criticality": criticality,
                "health_score": health,
                "risk_level": risk,
                "rated_hours": rated,
                "running_hours": max(1000, rated - max(50, int(health * 18 - (80 if risk == "critical" else 0)))),
                "status": risk_to_status(risk),
                "last_maintenance": (now - timedelta(days=18 + index * 4)).date().isoformat(),
                "rul_hours": max(0, int(health * 18 - (80 if risk == "critical" else 0))),
                "mtbf": 320 + health * 6,
                "mttr": round(3.2 + (100 - health) / 18, 1),
                "failure_modes": profile["failure_modes"],
                "root_causes": profile["root_causes"],
                "recommended_actions": profile["actions"],
                "production_tph": profile["production_tph"],
                "base_repair_cost_inr": profile["repair_cost"],
            }
        )
    return records


def build_sensor_ranges() -> dict:
    return {
        "temperature": {"normal": [45, 75], "warning": 82, "critical": 92, "unit": "C"},
        "vibration": {"normal": [1.1, 4.0], "warning": 5.2, "critical": 7.1, "unit": "mm/s"},
        "pressure": {"normal": [105, 155], "warning_low": 95, "critical_low": 80, "unit": "bar"},
        "flow": {"normal": [120, 260], "warning_low": 95, "critical_low": 70, "unit": "m3/h"},
        "oil_quality": {"normal": [72, 100], "warning_low": 55, "critical_low": 40, "unit": "index"},
        "current": {"normal": [110, 340], "warning": 370, "critical": 420, "unit": "A"},
        "utilization": {"normal": [55, 92], "warning": 96, "critical": 99, "unit": "%"},
        "energy_consumption": {"normal": [80, 310], "warning": 360, "critical": 420, "unit": "kWh"},
    }


def risk_profile(asset: dict) -> dict:
    risk = asset["risk_level"]
    vibration = random.uniform(1.4, 3.9)
    oil_quality = random.uniform(70, 94)
    temperature = random.uniform(48, 74)
    pressure = random.uniform(110, 150)
    flow = random.uniform(130, 245)
    current = random.uniform(130, 330)
    profile = profile_for(asset)
    mode_text = " ".join(profile["failure_modes"]).lower()
    if "gear" in mode_text:
        oil_quality -= 20
        vibration += 0.9
    if "hydraulic" in mode_text or "pressure" in mode_text or "pump" in mode_text:
        pressure -= 24
        flow -= 18
    if "winding" in mode_text or "overheating" in mode_text:
        temperature += 14
        current += 35
    if "fan" in mode_text or "bearing" in mode_text:
        vibration += 1.15
    if risk == "critical":
        vibration += random.uniform(2.0, 4.2)
        pressure -= random.uniform(18, 42)
        current += random.uniform(38, 92)
        temperature += random.uniform(7, 18)
        oil_quality -= random.uniform(16, 38)
    elif risk == "high":
        vibration += random.uniform(0.8, 2.2)
        pressure -= random.uniform(7, 22)
        current += random.uniform(15, 46)
        temperature += random.uniform(4, 10)
        oil_quality -= random.uniform(8, 22)
    elif risk == "medium":
        vibration += random.uniform(0.2, 1.0)
        pressure -= random.uniform(0, 10)
        current += random.uniform(0, 22)
    return {
        "temperature": round(temperature, 1),
        "vibration": round(vibration, 2),
        "pressure": round(max(62, pressure), 1),
        "flow": round(max(65, flow - (20 if risk in {"critical", "high"} else 0)), 1),
        "oil_quality": round(max(24, oil_quality), 1),
        "current": round(current, 1),
        "utilization": round(random.uniform(63, 98), 1),
        "energy_consumption": round(random.uniform(120, 410), 1),
    }


def failure_mode_for(sensor: dict, asset: dict) -> str:
    profile = profile_for(asset)
    modes = profile["failure_modes"]
    if "Gearbox" in asset["type"] or "gear" in " ".join(modes):
        if sensor["oil_quality"] <= 62:
            return "oil contamination"
        if sensor["vibration"] >= 5.2:
            return "bearing failure"
        return "gear wear"
    if "Hydraulic" in asset["type"]:
        if sensor["pressure"] <= 95:
            return "pressure leak"
        if sensor["flow"] <= 95:
            return "pump cavitation"
        return "seal failure"
    if "Drive Motor" in asset["type"]:
        if sensor["temperature"] >= 82:
            return "winding insulation degradation"
        if sensor["vibration"] >= 5.2:
            return "rotor imbalance"
        return "overheating"
    if sensor["vibration"] >= 5.2:
        return modes[0]
    if sensor["oil_quality"] <= 55 or "Gearbox" in asset["name"]:
        return modes[min(1, len(modes) - 1)]
    if sensor["temperature"] >= 82 or "Motor" in asset["name"]:
        return modes[min(2, len(modes) - 1)]
    if sensor["pressure"] <= 95 or "Hydraulic" in asset["type"]:
        return modes[0]
    return random.choice(modes)


def build_sensor_data(equipment: list[dict], now: datetime) -> tuple[list[dict], list[dict]]:
    latest = []
    full = []
    for asset in equipment:
        base = risk_profile(asset)
        for index in range(50):
            ts = now - timedelta(minutes=(49 - index) * 10)
            drift = index / 49
            row = {
                "timestamp": ts.isoformat(timespec="seconds"),
                "equipment_id": asset["id"],
                "asset_name": asset["name"],
                "area": asset["area"],
                "temperature": round(base["temperature"] + random.uniform(-2.2, 2.2) + drift * (2 if asset["risk_level"] in {"critical", "high"} else 0.4), 1),
                "vibration": round(base["vibration"] + random.uniform(-0.25, 0.35) + drift * (0.55 if asset["risk_level"] == "critical" else 0.12), 2),
                "pressure": round(base["pressure"] + random.uniform(-4.5, 4.5) - drift * (4 if asset["risk_level"] in {"critical", "high"} else 0.6), 1),
                "flow": round(base["flow"] + random.uniform(-8, 8), 1),
                "oil_quality": round(max(20, base["oil_quality"] + random.uniform(-2.8, 1.4) - drift * (2.5 if asset["risk_level"] in {"critical", "high"} else 0.4)), 1),
                "current": round(base["current"] + random.uniform(-9, 11) + drift * (9 if asset["risk_level"] == "critical" else 2), 1),
                "utilization": round(base["utilization"] + random.uniform(-3.0, 2.5), 1),
                "energy_consumption": round(base["energy_consumption"] + random.uniform(-20, 24), 1),
            }
            row["failure_signal"] = failure_mode_for(row, asset)
            full.append(row)
        latest.append(full[-1])
    return latest, full


def build_failure_reports(equipment: list[dict], sensor_latest: list[dict], now: datetime) -> list[dict]:
    reports = []
    sensor_map = {row["equipment_id"]: row for row in sensor_latest}
    for idx in range(150):
        asset = random.choice(equipment)
        sensor = sensor_map[asset["id"]]
        failure = failure_mode_for(sensor, asset)
        profile = profile_for(asset)
        root_cause = profile["root_causes"][profile["failure_modes"].index(failure)] if failure in profile["failure_modes"] else random.choice(profile["root_causes"])
        severity = asset["risk_level"] if idx < 55 else random.choice(["medium", "high", asset["risk_level"]])
        reports.append(
            {
                "record_id": f"TSA-FR-{idx + 1:04d}",
                "equipment_id": asset["id"],
                "asset_name": asset["name"],
                "area": asset["area"],
                "failure_mode": failure,
                "detected_at": (now - timedelta(days=random.randint(1, 420), hours=random.randint(0, 22))).isoformat(timespec="seconds"),
                "severity": severity,
                "symptoms": f"{failure} pattern with vibration {sensor['vibration']} mm/s, pressure {sensor['pressure']} bar, oil quality {sensor['oil_quality']}",
                "root_cause": root_cause,
                "corrective_action": random.choice(profile["actions"]),
                "downtime_minutes": random.randint(45, 520) + int((100 - asset["health_score"]) * 2),
            }
        )
    return reports


def build_maintenance_logs(equipment: list[dict], now: datetime) -> list[dict]:
    rows = []
    for idx in range(300):
        asset = random.choice(equipment)
        profile = profile_for(asset)
        action = random.choice(profile["actions"] + ["Preventive inspection", "Condition verification"])
        rows.append(
            {
                "log_id": f"TSA-ML-{idx + 1:04d}",
                "equipment_id": asset["id"],
                "asset_name": asset["name"],
                "area": asset["area"],
                "date": (now - timedelta(days=random.randint(1, 520))).date().isoformat(),
                "action": action,
                "technician": random.choice(["A. Sharma", "R. Iyer", "S. Khan", "P. Verma", "N. Rao"]),
                "duration_hours": round(random.uniform(1.2, 9.5), 1),
                "finding": random.choice(profile["root_causes"] + ["Normal", "Repeat failure watchlisted"]),
                "compliance_status": random.choice(["Closed", "Closed", "Verified", "Follow-up Required"]),
            }
        )
    return rows


def build_spares(equipment: list[dict]) -> list[dict]:
    rows = []
    for idx in range(100):
        asset = random.choice(equipment)
        profile = profile_for(asset)
        critical = asset["risk_level"] in {"critical", "high"} or random.random() > 0.72
        rows.append(
            {
                "part_id": f"TSA-SP-{idx + 1:04d}",
                "equipment_id": asset["id"],
                "asset_name": asset["name"],
                "part_name": random.choice(profile["spares"]),
                "current_stock": random.choice([0, 0, 1, 2, 3, 5, 8]) if critical else random.randint(2, 12),
                "min_stock": random.randint(1, 4),
                "lead_time_days": random.choice([5, 7, 10, 14, 18, 21, 28, 35]) if critical else random.choice([3, 5, 7, 10]),
                "criticality": asset["criticality"],
                "estimated_cost_inr": random.randint(18000, 380000),
                "preferred_vendor": random.choice(["Tata Approved OEM", "Danieli Service", "SMS Group Service", "ABB Motion", "Local Emergency Vendor"]),
            }
        )
    return rows


def build_work_orders(equipment: list[dict], now: datetime) -> list[dict]:
    statuses = ["Open", "Assigned", "In Progress", "Completed", "Closed"]
    return [
        {
            "work_order_id": f"TSA-WO-{idx + 1:04d}",
            "equipment_id": (asset := random.choice(equipment))["id"],
            "asset_name": asset["name"],
            "area": asset["area"],
            "priority": "P1" if asset["risk_level"] == "critical" else "P2" if asset["risk_level"] == "high" else "P3",
            "status": random.choice(statuses),
            "created_at": (now - timedelta(days=random.randint(0, 120), hours=random.randint(0, 22))).isoformat(timespec="seconds"),
            "planned_duration_hours": round(random.uniform(2.0, 10.0), 1),
            "estimated_cost_inr": int(profile_for(asset)["repair_cost"] * random.uniform(0.65, 1.45)),
            "assigned_team": random.choice(["Mechanical Maintenance", "Electrical Maintenance", "Hydraulics Team", "Utilities Maintenance"]),
            "safety_permit": "Required" if asset["risk_level"] in {"critical", "high"} else "Review",
        }
        for idx in range(100)
    ]


def main() -> None:
    random.seed(42)
    now = datetime.now().replace(microsecond=0)
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    equipment = build_equipment(now)
    sensor_latest, sensor_full = build_sensor_data(equipment, now)
    payloads = {
        "equipment.json": equipment,
        "failure_modes.json": build_failure_modes(equipment),
        "failure_reports.json": build_failure_reports(equipment, sensor_latest, now),
        "maintenance_logs.json": build_maintenance_logs(equipment, now),
        "sensor_data.json": sensor_latest,
        "sensor_data_full.json": sensor_full,
        "sensor_ranges.json": build_sensor_ranges(),
        "spare_parts.json": build_spares(equipment),
        "work_orders.json": build_work_orders(equipment, now),
    }
    for name, payload in payloads.items():
        (DATA_DIR / name).write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_reasoning_csvs(equipment, sensor_latest, payloads["spare_parts.json"], payloads["failure_reports.json"], now)
    print("Generated enterprise Tata Steel maintenance data:")
    for name, payload in payloads.items():
        print(f"- data/{name}: {len(payload) if isinstance(payload, list) else len(payload.keys())} records")


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def build_failure_modes(equipment: list[dict]) -> list[dict]:
    rows = []
    for asset in equipment:
        profile = profile_for(asset)
        for index, mode in enumerate(profile["failure_modes"]):
            rows.append(
                {
                    "equipment_id": asset["id"],
                    "asset_name": asset["name"],
                    "area": asset["area"],
                    "asset_type": asset["type"],
                    "failure_mode": mode,
                    "likely_root_cause": profile["root_causes"][index % len(profile["root_causes"])],
                    "recommended_action": profile["actions"][index % len(profile["actions"])],
                    "primary_spare": profile["spares"][index % len(profile["spares"])],
                    "production_tph": profile["production_tph"],
                    "base_repair_cost_inr": profile["repair_cost"],
                }
            )
    return rows


def alert_for_sensor(row: dict, asset: dict) -> str:
    asset_type = asset.get("type", "")
    if asset_type == "Hydraulic System" and row["pressure"] <= 110:
        return "HYD_PRESS_LOW"
    if asset_type == "Gearbox" and row["oil_quality"] <= 62:
        return "OIL_CONTAMINATION"
    if asset_type == "Drive Motor" and (row["temperature"] >= 82 or row["current"] >= 360):
        return "MOTOR_THERMAL_RISK"
    if row["vibration"] >= 5.2:
        return "VIBRATION_HIGH"
    if row["oil_quality"] <= 55:
        return "OIL_QUALITY_LOW"
    if row["temperature"] >= 82:
        return "TEMP_HIGH"
    if row["pressure"] <= 95:
        return "HYD_PRESS_LOW"
    if asset["risk_level"] == "critical":
        return "CRITICAL_DEGRADATION"
    if asset["risk_level"] == "high":
        return "EARLY_WARNING"
    return "NORMAL_WATCH"


def write_reasoning_csvs(equipment: list[dict], sensor_latest: list[dict], spares: list[dict], failures: list[dict], now: datetime) -> None:
    asset_map = {item["id"]: item for item in equipment}
    sensor_rows = []
    for row in sensor_latest:
        asset = asset_map[row["equipment_id"]]
        sensor_rows.append(
            {
                "equipment_id": asset["id"],
                "equipment_name": asset["name"],
                "timestamp": row["timestamp"],
                "temperature_c": row["temperature"],
                "vibration_mm_s": row["vibration"],
                "motor_current_a": row["current"],
                "oil_pressure_bar": round(max(1.2, row["oil_quality"] / 22), 1),
                "hydraulic_pressure_bar": row["pressure"],
                "roll_gap_variation_mm": round(0.05 + max(0, row["vibration"] - 3.5) / 12, 2),
                "speed_mpm": 0 if "Furnace" in asset["name"] else random.randint(580, 980),
                "operating_hours_since_service": max(80, asset["rated_hours"] - asset["rul_hours"]),
                "anomaly_alert": alert_for_sensor(row, asset),
            }
        )
    write_csv(
        DATA_DIR / "sensor_snapshot.csv",
        sensor_rows,
        [
            "equipment_id",
            "equipment_name",
            "timestamp",
            "temperature_c",
            "vibration_mm_s",
            "motor_current_a",
            "oil_pressure_bar",
            "hydraulic_pressure_bar",
            "roll_gap_variation_mm",
            "speed_mpm",
            "operating_hours_since_service",
            "anomaly_alert",
        ],
    )

    spare_rows = [
        {
            "equipment_id": row["equipment_id"],
            "part": row["part_name"],
            "available_qty": row["current_stock"],
            "lead_time_days": row["lead_time_days"],
            "criticality": row["criticality"],
        }
        for row in spares
    ]
    write_csv(DATA_DIR / "spares_inventory.csv", spare_rows, ["equipment_id", "part", "available_qty", "lead_time_days", "criticality"])

    history_rows = [
        {
            "record_id": row["record_id"].replace("TSA-FR", "FH"),
            "equipment_id": row["equipment_id"],
            "equipment_name": row["asset_name"],
            "component": row["failure_mode"],
            "fault_message": row["failure_mode"].upper().replace(" ", "_"),
            "symptoms": row["symptoms"],
            "root_cause": row["root_cause"],
            "action_taken": row["corrective_action"],
            "downtime_minutes": row["downtime_minutes"],
            "severity": row["severity"],
            "days_since_overhaul": random.randint(20, 260),
        }
        for row in failures[:180]
    ]
    write_csv(
        DATA_DIR / "failure_history.csv",
        history_rows,
        [
            "record_id",
            "equipment_id",
            "equipment_name",
            "component",
            "fault_message",
            "symptoms",
            "root_cause",
            "action_taken",
            "downtime_minutes",
            "severity",
            "days_since_overhaul",
        ],
    )


if __name__ == "__main__":
    main()

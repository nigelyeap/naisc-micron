"""Generate all synthetic semiconductor log files."""

import json
import random
import datetime
import csv
import struct
import os

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
random.seed(42)


# ============================================================
# 1. VENDOR A - JSON Sensor Trace
# ============================================================
def gen_vendor_a():
    random.seed(42)
    base_time = datetime.datetime(2025, 1, 15, 8, 0, 0)

    sensors_def = [
        {"SensorID": "SEN-PRES-001", "Unit": "Pa", "base": 0.9, "noise": 0.05, "spike": 3.5},
        {"SensorID": "SEN-TEMP-001", "Unit": "C", "base": 85.0, "noise": 1.5, "spike": 145.0},
        {"SensorID": "SEN-RFPW-001", "Unit": "W", "base": 300.0, "noise": 5.0, "spike": 520.0},
        {"SensorID": "SEN-GASF-001", "Unit": "sccm", "base": 50.0, "noise": 1.0, "spike": 12.0},
    ]

    anomaly_indices = set(random.sample(range(60), 5))

    sensor_data = []
    for s in sensors_def:
        measurements = []
        for i in range(60):
            t = base_time + datetime.timedelta(seconds=i * 30)
            ts = t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{random.randint(0,999):03d}Z"
            if i in anomaly_indices:
                val = round(s["spike"] + random.uniform(-0.5, 0.5), 3)
            else:
                val = round(s["base"] + random.uniform(-s["noise"], s["noise"]), 3)
            measurements.append({"DateTime": ts, "Value": val})
        sensor_data.append({
            "SensorID": s["SensorID"],
            "Unit": s["Unit"],
            "SamplingRateMs": 30000,
            "Measurements": measurements,
        })

    alarms = []
    alarm_codes = [
        "ALM-4201: Chamber pressure excursion",
        "ALM-4305: Temperature limit exceeded",
        "ALM-4410: RF power anomaly",
        "ALM-4102: Gas flow deviation",
    ]
    for idx, ai in enumerate(sorted(anomaly_indices)):
        t = base_time + datetime.timedelta(seconds=ai * 30)
        ts = t.strftime("%Y-%m-%dT%H:%M:%S.") + f"{random.randint(0,999):03d}Z"
        alarms.append({
            "AlarmID": f"A-{1001 + idx}",
            "AlarmCode": alarm_codes[idx % len(alarm_codes)],
            "Severity": random.choice(["Warning", "Critical"]),
            "DateTime": ts,
            "Acknowledged": random.choice([True, False]),
        })

    control_state_events = [
        {"EventID": "EVT-0001", "Text": "ControlJob CJ-2025-0115-001 created", "DateTime": "2025-01-15T08:00:00.000Z"},
        {"EventID": "EVT-0002", "Text": "ProcessJob PJ-001 queued for Module PM1", "DateTime": "2025-01-15T08:00:05.120Z"},
        {"EventID": "EVT-0003", "Text": "Wafer W-001 loaded into PM1", "DateTime": "2025-01-15T08:00:12.450Z"},
        {"EventID": "EVT-0004", "Text": "Recipe RCP_DRY_ETCH_01 step 1 started", "DateTime": "2025-01-15T08:00:15.000Z"},
        {"EventID": "EVT-0005", "Text": "Recipe RCP_DRY_ETCH_01 step 1 completed", "DateTime": "2025-01-15T08:10:00.000Z"},
        {"EventID": "EVT-0006", "Text": "Recipe RCP_DRY_ETCH_01 step 2 started", "DateTime": "2025-01-15T08:10:02.000Z"},
        {"EventID": "EVT-0007", "Text": "Alarm triggered: Chamber pressure excursion", "DateTime": "2025-01-15T08:14:30.500Z"},
        {"EventID": "EVT-0008", "Text": "Recipe RCP_DRY_ETCH_01 step 2 completed", "DateTime": "2025-01-15T08:20:00.000Z"},
        {"EventID": "EVT-0009", "Text": "Wafer W-001 unloaded from PM1", "DateTime": "2025-01-15T08:20:15.300Z"},
        {"EventID": "EVT-0010", "Text": "ProcessJob PJ-001 completed successfully", "DateTime": "2025-01-15T08:20:20.000Z"},
        {"EventID": "EVT-0011", "Text": "ProcessJob PJ-002 queued for Module PM2", "DateTime": "2025-01-15T08:20:25.000Z"},
        {"EventID": "EVT-0012", "Text": "Wafer W-002 loaded into PM2", "DateTime": "2025-01-15T08:20:35.100Z"},
        {"EventID": "EVT-0013", "Text": "Recipe RCP_DRY_ETCH_01 step 1 started on PM2", "DateTime": "2025-01-15T08:20:40.000Z"},
        {"EventID": "EVT-0014", "Text": "Recipe RCP_DRY_ETCH_01 step 1 completed on PM2", "DateTime": "2025-01-15T08:30:00.000Z"},
        {"EventID": "EVT-0015", "Text": "ControlJob CJ-2025-0115-001 completed", "DateTime": "2025-01-15T08:30:20.000Z"},
    ]

    errors = [
        {"ErrorID": "ERR-0001", "ErrorCode": "E-5001", "Text": "RF generator momentary overcurrent detected", "DateTime": "2025-01-15T08:14:30.510Z", "Recoverable": True},
        {"ErrorID": "ERR-0002", "ErrorCode": "E-5020", "Text": "Throttle valve response lag >50ms", "DateTime": "2025-01-15T08:17:45.200Z", "Recoverable": True},
    ]

    doc = {
        "ControlJob": {
            "ControlJobID": "CJ-2025-0115-001",
            "EquipmentID": "ETCH-TOOL-001",
            "EquipmentType": "DryEtchReactor",
            "LotID": "LOT-2025-A1042",
            "StartTime": "2025-01-15T08:00:00.000Z",
            "EndTime": "2025-01-15T08:30:20.000Z",
            "Status": "Completed",
            "ProcessJobs": [
                {
                    "ProcessJobID": "PJ-001",
                    "RecipeName": "RCP_DRY_ETCH_01",
                    "RecipeVersion": "3.2.1",
                    "ModuleProcessReports": [
                        {
                            "Keys": {"ModuleID": "PM1", "RecipeStepID": "STEP-01", "WaferID": "W-001"},
                            "StartTime": "2025-01-15T08:00:15.000Z",
                            "EndTime": "2025-01-15T08:10:00.000Z",
                            "Result": "Completed",
                            "Parameters": {"TargetPressure_Pa": 0.9, "TargetTemp_C": 85.0, "RFPower_W": 300, "GasFlow_sccm": 50.0, "EtchGas": "CF4/O2"},
                        },
                        {
                            "Keys": {"ModuleID": "PM1", "RecipeStepID": "STEP-02", "WaferID": "W-001"},
                            "StartTime": "2025-01-15T08:10:02.000Z",
                            "EndTime": "2025-01-15T08:20:00.000Z",
                            "Result": "CompletedWithWarnings",
                            "Parameters": {"TargetPressure_Pa": 1.2, "TargetTemp_C": 90.0, "RFPower_W": 350, "GasFlow_sccm": 55.0, "EtchGas": "CF4/O2/Ar"},
                        },
                    ],
                },
                {
                    "ProcessJobID": "PJ-002",
                    "RecipeName": "RCP_DRY_ETCH_01",
                    "RecipeVersion": "3.2.1",
                    "ModuleProcessReports": [
                        {
                            "Keys": {"ModuleID": "PM2", "RecipeStepID": "STEP-01", "WaferID": "W-002"},
                            "StartTime": "2025-01-15T08:20:40.000Z",
                            "EndTime": "2025-01-15T08:30:00.000Z",
                            "Result": "Completed",
                            "Parameters": {"TargetPressure_Pa": 0.9, "TargetTemp_C": 85.0, "RFPower_W": 300, "GasFlow_sccm": 50.0, "EtchGas": "CF4/O2"},
                        }
                    ],
                },
            ],
            "Events": {
                "ControlStateEvents": control_state_events,
                "Alarms": alarms,
                "Errors": errors,
            },
            "SensorData": sensor_data,
        }
    }

    path = os.path.join(OUT_DIR, "vendor_a_sensor_trace.json")
    with open(path, "w") as f:
        json.dump(doc, f, indent=2)
    lines = json.dumps(doc, indent=2).count("\n") + 1
    print(f"  vendor_a_sensor_trace.json: {lines} lines")


# ============================================================
# 2. VENDOR B - JSON Sensor Trace
# ============================================================
def gen_vendor_b():
    random.seed(99)
    base_time = datetime.datetime(2025, 1, 15, 9, 0, 0)
    anomaly_indices = set(random.sample(range(55), 5))

    sensor_defs = [
        {"Name": "ChamberPressure", "Keys": {"SensorID": "PRES-PM3-01", "Location": "PM3-MainChamber"}, "Unit": "Pa", "base": 1.1, "noise": 0.04, "spike": 4.2},
        {"Name": "SubstrateTemperature", "Keys": {"SensorID": "TEMP-PM3-01", "Location": "PM3-ESC"}, "Unit": "degC", "base": 80.0, "noise": 1.2, "spike": 138.0},
        {"Name": "RFForwardPower", "Keys": {"SensorID": "RFPW-PM3-01", "Location": "PM3-TopElectrode"}, "Unit": "Watt", "base": 250.0, "noise": 4.0, "spike": 480.0},
        {"Name": "BiasRFPower", "Keys": {"SensorID": "BRFP-PM3-01", "Location": "PM3-BottomElectrode"}, "Unit": "Watt", "base": 100.0, "noise": 2.0, "spike": 210.0},
        {"Name": "ProcessGasFlow_CF4", "Keys": {"SensorID": "GAS-PM3-CF4", "Location": "PM3-GasBox"}, "Unit": "sccm", "base": 45.0, "noise": 0.8, "spike": 8.0},
    ]

    traces = []
    for s in sensor_defs:
        readings = []
        for i in range(55):
            t = base_time + datetime.timedelta(seconds=i * 20)
            ts = t.strftime("%d-%b-%Y %H:%M:%S") + f".{random.randint(0,999):03d}"
            if i in anomaly_indices:
                val = round(s["spike"] + random.uniform(-0.3, 0.3), 4)
            else:
                val = round(s["base"] + random.uniform(-s["noise"], s["noise"]), 4)
            readings.append({"Timestamp": ts, "Reading": val})
        traces.append({
            "Name": s["Name"],
            "Keys": s["Keys"],
            "UnitOfMeasure": s["Unit"],
            "SampleInterval_ms": 20000,
            "DataPoints": readings,
        })

    alarms_list = []
    alarm_map = {
        0: {"Code": "PRS-EXCURSION-001", "Description": "Chamber pressure outside tolerance band"},
        1: {"Code": "TMP-OVERLIMIT-003", "Description": "Substrate temperature exceeded high limit"},
        2: {"Code": "RF-REFLECT-005", "Description": "RF reflected power > 10% of forward"},
        3: {"Code": "GAS-DEVIATION-002", "Description": "Process gas flow deviation > 5 sccm"},
        4: {"Code": "BIAS-SPIKE-004", "Description": "Bias RF power transient detected"},
    }
    for idx, ai in enumerate(sorted(anomaly_indices)):
        t = base_time + datetime.timedelta(seconds=ai * 20)
        ts = t.strftime("%d-%b-%Y %H:%M:%S") + f".{random.randint(0,999):03d}"
        a = alarm_map[idx % 5]
        cleared_ts = None
        if random.random() > 0.3:
            cleared_ts = (t + datetime.timedelta(seconds=random.randint(5, 30))).strftime("%d-%b-%Y %H:%M:%S") + ".000"
        alarms_list.append({
            "Name": a["Code"],
            "Description": a["Description"],
            "Level": random.choice(["WARNING", "CRITICAL"]),
            "Timestamp": ts,
            "Cleared": cleared_ts is not None,
            "ClearedTimestamp": cleared_ts,
        })

    doc = {
        "ToolTrace": {
            "ToolInfo": {
                "ToolName": "ETCH-TOOL-003",
                "ToolType": "ConductorEtch",
                "FabID": "FAB-WEST-02",
                "ToolSoftwareVersion": "7.4.1-build.2281",
            },
            "RunInfo": {
                "RunID": "RUN-20250115-093000-PM3",
                "LotID": "LOT-2025-B2087",
                "WaferSlot": 5,
                "WaferID": "WFR-B2087-05",
                "CarrierID": "FOUP-1122",
                "Recipe": {
                    "RecipeName": "COND_ETCH_45NM_V2",
                    "RecipeRevision": "2.1.0",
                    "Steps": [
                        {"StepNumber": 1, "StepName": "Stabilize", "Duration_s": 30, "Parameters": {"Pressure_Pa": 1.1, "Temp_C": 80, "RF_W": 0, "Gas_CF4_sccm": 45}},
                        {"StepNumber": 2, "StepName": "MainEtch", "Duration_s": 120, "Parameters": {"Pressure_Pa": 1.1, "Temp_C": 80, "RF_W": 250, "BiasRF_W": 100, "Gas_CF4_sccm": 45}},
                        {"StepNumber": 3, "StepName": "OverEtch", "Duration_s": 60, "Parameters": {"Pressure_Pa": 0.8, "Temp_C": 80, "RF_W": 200, "BiasRF_W": 80, "Gas_CF4_sccm": 40}},
                        {"StepNumber": 4, "StepName": "Purge", "Duration_s": 20, "Parameters": {"Pressure_Pa": 5.0, "Temp_C": 80, "RF_W": 0, "Gas_N2_sccm": 200}},
                    ],
                },
                "StartTimestamp": "15-Jan-2025 09:00:00.000",
                "EndTimestamp": "15-Jan-2025 09:18:20.000",
                "Outcome": "COMPLETED_WITH_WARNINGS",
            },
            "SensorTraces": traces,
            "AlarmLog": alarms_list,
            "SystemMessages": [
                {"Timestamp": "15-Jan-2025 09:00:00.100", "Source": "ProcessController", "Level": "INFO", "Message": "Run RUN-20250115-093000-PM3 initiated"},
                {"Timestamp": "15-Jan-2025 09:00:01.200", "Source": "GasBox", "Level": "INFO", "Message": "CF4 MFC opened to 45.0 sccm setpoint"},
                {"Timestamp": "15-Jan-2025 09:00:30.050", "Source": "ProcessController", "Level": "INFO", "Message": "Step 1 (Stabilize) completed"},
                {"Timestamp": "15-Jan-2025 09:00:30.100", "Source": "RFGenerator", "Level": "INFO", "Message": "RF forward power ramping to 250W"},
                {"Timestamp": "15-Jan-2025 09:02:30.500", "Source": "ProcessController", "Level": "INFO", "Message": "Step 2 (MainEtch) completed"},
                {"Timestamp": "15-Jan-2025 09:04:30.000", "Source": "ProcessController", "Level": "INFO", "Message": "Step 3 (OverEtch) completed"},
                {"Timestamp": "15-Jan-2025 09:05:00.000", "Source": "VacuumSystem", "Level": "INFO", "Message": "Venting to N2 purge pressure"},
                {"Timestamp": "15-Jan-2025 09:05:20.000", "Source": "ProcessController", "Level": "INFO", "Message": "Step 4 (Purge) completed. Run finished."},
            ],
        }
    }

    path = os.path.join(OUT_DIR, "vendor_b_sensor_trace.json")
    with open(path, "w") as f:
        json.dump(doc, f, indent=2)
    lines = json.dumps(doc, indent=2).count("\n") + 1
    print(f"  vendor_b_sensor_trace.json: {lines} lines")


# ============================================================
# 3. XML - EUV Dose Recipe
# ============================================================
def gen_euv_xml():
    import xml.etree.ElementTree as ET
    from xml.dom import minidom

    random.seed(77)

    root = ET.Element("ADELdr:Recipe")
    root.set("xmlns:ADELdr", "http://www.adel.com/schemas/dr")
    root.set("xmlns:xsi", "http://www.w3.org/2001/XMLSchema-instance")

    header = ET.SubElement(root, "Header")
    for tag, val in [
        ("Title", "EUV_DOSE_PROFILE_7NM_V3"),
        ("MachineID", "EUV-SCN-002"),
        ("CustomerName", "ACME Semiconductor"),
        ("MachineType", "TWINSCAN NXE:3600D"),
        ("SoftwareRelease", "SW-2024.11.3-HF2"),
        ("CreatedBy", "ProcessEngineer_JSmith"),
        ("CreateTime", "2025-01-10T14:30:00Z"),
        ("DocumentId", "DOC-2025-EUV-00342"),
        ("DocumentType", "DoseRecipe"),
        ("DocumentTypeVersion", "3.1"),
    ]:
        ET.SubElement(header, tag).text = val

    ET.SubElement(root, "RecipeName").text = "EUV_DOSE_7NM_LAYER4"
    ET.SubElement(root, "ApprovedBy").text = "SrProcessEngineer_KWong"
    ET.SubElement(root, "ExpirationTime").text = "2025-07-10T14:30:00Z"
    ET.SubElement(root, "TargetMachineID").text = "EUV-SCN-002"

    slit_list = ET.SubElement(root, "SlitProfileList")
    for i in range(6):
        slit = ET.SubElement(slit_list, "SlitProfileElement")
        slit.set("Index", str(i))
        slit.set("Name", f"SlitZone_{i + 1}")
        slit.set("Width_mm", str(round(4.4 + i * 0.2, 1)))
        slit.set("Position_mm", str(round(-11.0 + i * 4.4, 1)))
        legendre = ET.SubElement(slit, "LegendreCoefficientList")
        coeffs = [round(random.gauss(0, 0.002), 6) for _ in range(7)]
        coeffs[0] = round(1.0 + random.gauss(0, 0.005), 6)
        for ci, c in enumerate(coeffs):
            sp = ET.SubElement(legendre, "SetPoint")
            sp.set("Order", str(ci))
            sp.set("Value", str(c))

    dose_list = ET.SubElement(root, "DoseProfileList")
    for field_y in range(-5, 6):
        dose_elem = ET.SubElement(dose_list, "DoseProfileElement")
        dose_elem.set("FieldPositionY_mm", str(field_y * 2.6))
        dose_elem.set("TargetDose_mJ_cm2", str(round(33.0 + random.gauss(0, 0.3), 2)))
        dose_elem.set("DoseUniformity_percent", str(round(random.uniform(0.15, 0.45), 3)))
        ic = ET.SubElement(dose_elem, "IntensityCorrection")
        for scan_pos in range(8):
            pt = ET.SubElement(ic, "CorrectionPoint")
            pt.set("ScanPosition_mm", str(round(-14.0 + scan_pos * 4.0, 1)))
            pt.set("CorrectionFactor", str(round(1.0 + random.gauss(0, 0.003), 6)))

    xml_str = minidom.parseString(ET.tostring(root, encoding="unicode")).toprettyxml(indent="  ")
    path = os.path.join(OUT_DIR, "euv_dose_recipe.xml")
    with open(path, "w") as f:
        f.write(xml_str)
    print(f"  euv_dose_recipe.xml written")


# ============================================================
# 4. CSV - Sensor Readings
# ============================================================
def gen_csv():
    random.seed(55)
    base_time = datetime.datetime(2025, 1, 15, 6, 0, 0)
    chambers = ["C1", "C2", "C3", "C4"]
    tool_ids = ["ETCH-001", "ETCH-002"]

    # Nominal ranges per chamber
    chamber_profiles = {
        "C1": {"pressure": 0.9, "temp": 85.0, "rf": 300, "gas": 50.0},
        "C2": {"pressure": 1.2, "temp": 90.0, "rf": 350, "gas": 55.0},
        "C3": {"pressure": 0.7, "temp": 78.0, "rf": 250, "gas": 42.0},
        "C4": {"pressure": 1.5, "temp": 95.0, "rf": 400, "gas": 60.0},
    }

    rows = []
    for i in range(220):
        t = base_time + datetime.timedelta(seconds=i * 30)
        chamber = random.choice(chambers)
        tool = random.choice(tool_ids)
        prof = chamber_profiles[chamber]
        is_anomaly = random.random() < 0.07

        if is_anomaly:
            anomaly_type = random.choice(["pressure_drop", "temp_spike", "rf_fault", "gas_leak"])
            if anomaly_type == "pressure_drop":
                pressure = round(prof["pressure"] * random.uniform(0.1, 0.3), 4)
                temp = round(prof["temp"] + random.uniform(-1, 1), 2)
                rf = round(prof["rf"] + random.uniform(-3, 3), 1)
                gas = round(prof["gas"] + random.uniform(-0.5, 0.5), 2)
                status = "ALARM_PRESSURE"
            elif anomaly_type == "temp_spike":
                pressure = round(prof["pressure"] + random.uniform(-0.03, 0.03), 4)
                temp = round(prof["temp"] + random.uniform(40, 70), 2)
                rf = round(prof["rf"] + random.uniform(-3, 3), 1)
                gas = round(prof["gas"] + random.uniform(-0.5, 0.5), 2)
                status = "ALARM_TEMP"
            elif anomaly_type == "rf_fault":
                pressure = round(prof["pressure"] + random.uniform(-0.03, 0.03), 4)
                temp = round(prof["temp"] + random.uniform(-1, 1), 2)
                rf = round(prof["rf"] * random.uniform(1.5, 2.0), 1)
                gas = round(prof["gas"] + random.uniform(-0.5, 0.5), 2)
                status = "ALARM_RF"
            else:
                pressure = round(prof["pressure"] + random.uniform(-0.03, 0.03), 4)
                temp = round(prof["temp"] + random.uniform(-1, 1), 2)
                rf = round(prof["rf"] + random.uniform(-3, 3), 1)
                gas = round(prof["gas"] * random.uniform(0.1, 0.3), 2)
                status = "ALARM_GAS"
            vacuum = "FAULT"
        else:
            pressure = round(prof["pressure"] + random.uniform(-0.05, 0.05), 4)
            temp = round(prof["temp"] + random.uniform(-2, 2), 2)
            rf = round(prof["rf"] + random.uniform(-5, 5), 1)
            gas = round(prof["gas"] + random.uniform(-1, 1), 2)
            status = "OK"
            vacuum = "NORMAL"

        rows.append({
            "timestamp": t.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "chamber": chamber,
            "tool_id": tool,
            "pressure_Pa": pressure,
            "temperature_C": temp,
            "rf_power_W": rf,
            "gas_flow_sccm": gas,
            "vacuum_level": vacuum,
            "status": status,
        })

    path = os.path.join(OUT_DIR, "sensor_readings.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "chamber", "tool_id", "pressure_Pa", "temperature_C", "rf_power_W", "gas_flow_sccm", "vacuum_level", "status"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"  sensor_readings.csv: {len(rows)} rows")


# ============================================================
# 5. Plain Text Event Log (EUV Scanner Style)
# ============================================================
def gen_event_log():
    random.seed(33)
    base_time = datetime.datetime(2025, 1, 15, 0, 0, 0)
    machine = "MCH0001"
    release = "VER2024.11"

    event_templates = [
        ("SYSTEM EVENT", "ER-4102", "DEFAULT", "Log file 'ER/ER_event_log_m#{machine}_{date}_{time}' is created..."),
        ("SYSTEM EVENT", "ER-4100", "DEFAULT", "System initialization sequence started"),
        ("SYSTEM EVENT", "WH-1001", "DEFAULT", "Wafer handler initialized, home position confirmed"),
        ("SYSTEM EVENT", "IL-2010", "DEFAULT", "Illuminator source power at {power}W, status nominal"),
        ("SYSTEM EVENT", "ST-3001", "DEFAULT", "Stage calibration check passed, offset X={xoff}nm Y={yoff}nm"),
        ("SYSTEM EVENT", "RR-5001", "DEFAULT", "Reticle {reticle} loaded to reticle stage"),
        ("SYSTEM EVENT", "EX-6001", "DEFAULT", "Exposure start: lot={lot} wafer={wafer} field={field}"),
        ("SYSTEM EVENT", "EX-6002", "DEFAULT", "Exposure complete: dose={dose}mJ/cm2 focus={focus}nm"),
        ("SYSTEM EVENT", "AL-7001", "DEFAULT", "Alignment mark detected at X={ax}um Y={ay}um"),
        ("SYSTEM WARNING", "TH-8010", "WARNING", "Thermal drift detected: delta={delta}mK above threshold"),
        ("SYSTEM WARNING", "PR-8020", "WARNING", "Pressure fluctuation in chamber: {pval}Pa (limit: 0.05Pa)"),
        ("SYSTEM WARNING", "IL-8030", "WARNING", "Source power instability: {pinstab}% variation"),
        ("SYSTEM EVENT", "WH-1002", "DEFAULT", "Wafer {wafer} unloaded to cassette slot {slot}"),
        ("SYSTEM EVENT", "EX-6010", "DEFAULT", "Lot {lot} processing complete, {wcount} wafers exposed"),
        ("DEACTIVATE", "DA-9001", "DEFAULT", "Module {module} deactivated for scheduled maintenance"),
        ("SYSTEM EVENT", "ER-4103", "DEFAULT", "Log file 'ER/ER_event_log_m#{machine}_{date}_{time}' is closed"),
    ]

    erlo_files = ["ERLOlogfile.cpp", "ERLOsystem.cpp", "ERLOwafer.cpp", "ERLOexpose.cpp", "ERLOalign.cpp", "ERLOtherm.cpp"]
    erlo_ids = [20703, 20704, 31002, 41005, 51201, 60100, 70300, 80010]

    lines = []
    lots = ["LOT-A1042", "LOT-A1043", "LOT-B2087"]
    reticles = ["RTL-NXE-001", "RTL-NXE-002", "RTL-NXE-003"]
    wafer_num = 1

    for i in range(55):
        t = base_time + datetime.timedelta(minutes=i * 25 + random.randint(0, 5), seconds=random.randint(0, 59))
        ts_date = t.strftime("%m/%d/%Y")
        ts_time = t.strftime("%H:%M:%S") + f".{random.randint(0, 9999):04d}"

        tmpl = random.choice(event_templates)
        event_type = tmpl[0]
        event_code = tmpl[1]
        event_level = tmpl[2]

        lot = random.choice(lots)
        wafer = f"W-{wafer_num:03d}"
        wafer_num = (wafer_num % 25) + 1

        msg = tmpl[3].format(
            machine=machine,
            date=t.strftime("%Y%m%d"),
            time=t.strftime("%H%M%S"),
            power=round(250 + random.uniform(-2, 2), 1),
            xoff=round(random.uniform(-0.5, 0.5), 3),
            yoff=round(random.uniform(-0.5, 0.5), 3),
            reticle=random.choice(reticles),
            lot=lot,
            wafer=wafer,
            field=f"F{random.randint(1, 80):02d}",
            dose=round(33.0 + random.uniform(-0.5, 0.5), 2),
            focus=round(random.uniform(-20, 20), 1),
            ax=round(random.uniform(-500, 500), 2),
            ay=round(random.uniform(-500, 500), 2),
            delta=round(random.uniform(1, 15), 2),
            pval=round(random.uniform(0.051, 0.12), 4),
            pinstab=round(random.uniform(0.5, 3.0), 2),
            wcount=random.randint(20, 25),
            module=random.choice(["WaferHandler", "Illuminator", "ReticleStage", "WaferStage"]),
            slot=random.randint(1, 25),
        )

        erlo = random.choice(erlo_files)
        erlo_id = random.choice(erlo_ids)
        line_no = random.randint(100, 900)

        header_line = f"{ts_date}  {ts_time}  Machine:{machine}  (Rel:{release}, ERLO [{erlo_id}], {erlo}, ?.?, {line_no})"
        body_line = f"{event_type}: {event_code} {event_level}"

        lines.append(header_line)
        lines.append(body_line)
        lines.append(msg)
        lines.append("")

    path = os.path.join(OUT_DIR, "event_log.txt")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    print(f"  event_log.txt: {len(lines)} lines, {i+1} entries")


# ============================================================
# 6. Syslog Format
# ============================================================
def gen_syslog():
    random.seed(21)
    base_time = datetime.datetime(2025, 1, 15, 6, 0, 0)

    # facility=16 (local0), severity: 6=info, 4=warning, 3=error, 2=critical
    # PRI = facility*8 + severity
    hosts = ["ETCH-TOOL-001", "ETCH-TOOL-002", "EUV-SCN-001"]
    processes = [
        ("process_controller", 1234),
        ("gas_system", 2345),
        ("vacuum_ctrl", 3456),
        ("rf_generator", 4567),
        ("wafer_handler", 5678),
        ("thermal_mgr", 6789),
    ]

    chambers = ["C1", "C2", "C3", "C4"]
    recipes = ["RCP_0001", "RCP_0002", "RCP_DRY_ETCH_01", "COND_ETCH_45NM_V2"]

    msg_templates_info = [
        "Chamber {c} recipe {r} step {step} started, pressure={p}Pa temp={t}C",
        "Chamber {c} recipe {r} step {step} completed successfully",
        "Wafer {w} loaded into chamber {c}, carrier FOUP-{foup}",
        "Wafer {w} unloaded from chamber {c}, processing time {pt}s",
        "Gas line {gl} flow stabilized at {gf} sccm",
        "RF power ramp complete: forward={rf}W reflected={rr}W",
        "Vacuum pump {vp} base pressure reached: {bp} Pa",
        "Temperature setpoint {ts}C reached in chamber {c}",
        "Endpoint detection signal triggered at {ep}s into step {step}",
        "Lot {lot} wafer {wn}/25 processing started",
    ]
    msg_templates_warn = [
        "Chamber {c} pressure deviation: {pd}Pa from setpoint (threshold: 0.1Pa)",
        "RF reflected power elevated: {rr}W ({rrp}% of forward)",
        "Thermal drift in chamber {c}: {td}C above nominal",
        "Gas flow {gl} fluctuation: {gfv} sccm deviation",
        "Vacuum pump {vp} vibration level elevated: {vib} mm/s",
    ]
    msg_templates_err = [
        "Chamber {c} pressure excursion: {pe}Pa (limit: 2.0Pa) - recipe paused",
        "RF generator fault: overcurrent detected at {oc}A",
        "Gas leak detected on line {gl}: {leak} sccm unaccounted flow",
        "Wafer handler position error: {whe}mm from expected",
    ]
    msg_templates_crit = [
        "EMERGENCY STOP triggered on chamber {c} - all processes aborted",
        "Chamber {c} temperature runaway: {tr}C (safety limit: 150C)",
        "Vacuum integrity failure in chamber {c}: pressure rising at {pr} Pa/s",
    ]

    lines = []
    for i in range(110):
        t = base_time + datetime.timedelta(seconds=i * 45 + random.randint(0, 20))
        ts = t.strftime("%Y-%m-%dT%H:%M:%S") + f".{random.randint(0,999):03d}Z"

        host = random.choice(hosts)
        proc_name, proc_pid = random.choice(processes)
        c = random.choice(chambers)
        r = random.choice(recipes)

        roll = random.random()
        if roll < 0.65:
            severity = 6
            tmpl = random.choice(msg_templates_info)
        elif roll < 0.85:
            severity = 4
            tmpl = random.choice(msg_templates_warn)
        elif roll < 0.95:
            severity = 3
            tmpl = random.choice(msg_templates_err)
        else:
            severity = 2
            tmpl = random.choice(msg_templates_crit)

        pri = 16 * 8 + severity

        msg = tmpl.format(
            c=c, r=r, step=random.randint(1, 5),
            p=round(random.uniform(0.7, 1.5), 2),
            t=round(random.uniform(75, 100), 1),
            w=f"WFR-{random.randint(1000,9999):04d}",
            foup=f"{random.randint(1000,1999)}",
            pt=random.randint(180, 600),
            gl=f"GL-{random.randint(1,8)}",
            gf=round(random.uniform(30, 65), 1),
            rf=round(random.uniform(200, 450), 0),
            rr=round(random.uniform(1, 50), 1),
            vp=f"VP-{random.randint(1,4)}",
            bp=round(random.uniform(0.001, 0.01), 4),
            ts=round(random.uniform(75, 100), 1),
            ep=round(random.uniform(30, 180), 1),
            lot=f"LOT-{random.choice(['A','B','C'])}{random.randint(1000,9999)}",
            wn=random.randint(1, 25),
            pd=round(random.uniform(0.11, 0.5), 3),
            rrp=round(random.uniform(10, 25), 1),
            td=round(random.uniform(2, 10), 2),
            gfv=round(random.uniform(2, 8), 2),
            vib=round(random.uniform(5, 15), 1),
            pe=round(random.uniform(2.1, 5.0), 2),
            oc=round(random.uniform(12, 20), 1),
            leak=round(random.uniform(0.5, 5), 2),
            whe=round(random.uniform(0.5, 3), 2),
            tr=round(random.uniform(151, 180), 1),
            pr=round(random.uniform(0.1, 1.0), 3),
        )

        line = f"<{pri}>{ts} {host} {proc_name}[{proc_pid}]: {msg}"
        lines.append(line)

    path = os.path.join(OUT_DIR, "syslog_equipment.log")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  syslog_equipment.log: {len(lines)} entries")


# ============================================================
# 7. Key-Value Process Log
# ============================================================
def gen_kv_log():
    random.seed(66)
    base_time = datetime.datetime(2025, 1, 15, 8, 0, 0)

    events = ["RECIPE_START", "STEP_COMPLETE", "SENSOR_READ", "WAFER_LOAD", "WAFER_UNLOAD", "ALARM", "RECIPE_END", "IDLE", "PUMP_DOWN", "GAS_STABILIZE"]
    chambers = ["C1", "C2", "C3", "C4"]
    tools = ["ETCH-001", "ETCH-002"]
    recipes = ["RCP_0001", "RCP_0002", "RCP_DRY_ETCH_01"]
    statuses = ["OK", "OK", "OK", "OK", "OK", "WARNING", "ERROR"]

    lines = []
    step = 0
    for i in range(110):
        t = base_time + datetime.timedelta(seconds=i * 25 + random.randint(0, 10))
        ts = t.strftime("%Y-%m-%dT%H:%M:%SZ")
        tool = random.choice(tools)
        chamber = random.choice(chambers)
        event = random.choice(events)
        recipe = random.choice(recipes)
        status = random.choice(statuses)

        is_anomaly = random.random() < 0.08
        if is_anomaly:
            event = "ALARM"
            status = random.choice(["WARNING", "ERROR", "CRITICAL"])

        pressure = round(random.uniform(0.7, 1.5), 3) if not is_anomaly else round(random.uniform(3.0, 6.0), 3)
        temp = round(random.uniform(75, 100), 1) if not is_anomaly else round(random.uniform(140, 180), 1)
        rf = round(random.uniform(200, 400), 0)
        gas = round(random.uniform(30, 60), 1) if not is_anomaly else round(random.uniform(2, 10), 1)

        if event == "RECIPE_START":
            step = 1
        elif event == "STEP_COMPLETE":
            step += 1
        elif event == "RECIPE_END":
            step = 0

        parts = [
            f"timestamp={ts}",
            f"tool_id={tool}",
            f"module={chamber}",
            f"event={event}",
            f"recipe={recipe}",
            f"step={step}",
            f"pressure={pressure}",
            f"temp={temp}",
            f"rf_power={int(rf)}",
            f"gas_flow={gas}",
            f"status={status}",
        ]

        if event == "ALARM":
            alarm_codes = ["ALM-PRES-001", "ALM-TEMP-003", "ALM-RF-005", "ALM-GAS-002"]
            parts.append(f"alarm_code={random.choice(alarm_codes)}")
            parts.append(f"alarm_text=\"{'Pressure excursion' if 'PRES' in parts[-1] else 'Sensor limit exceeded'}\"")

        if event in ("WAFER_LOAD", "WAFER_UNLOAD"):
            parts.append(f"wafer_id=WFR-{random.randint(1000,9999)}")
            parts.append(f"slot={random.randint(1,25)}")

        lines.append(" ".join(parts))

    path = os.path.join(OUT_DIR, "kv_process_log.log")
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
    print(f"  kv_process_log.log: {len(lines)} entries")


# ============================================================
# 8. Vendor C - Parquet Sensor Trace (Dry Etch Tool)
# ============================================================
def gen_parquet():
    try:
        import pyarrow as pa          # type: ignore
        import pyarrow.parquet as pq  # type: ignore
    except ImportError:
        print("  vendor_c_sensor_trace.parquet SKIPPED (pyarrow not installed)")
        return

    random.seed(77)
    base_time = datetime.datetime(2025, 1, 15, 8, 0, 0)

    # Vendor C uses different field names and a flat per-sample row layout
    rows = []
    anomaly_indices = set(random.sample(range(80), 6))

    for i in range(80):
        t = base_time + datetime.timedelta(seconds=i * 30)
        is_anomaly = i in anomaly_indices

        rows.append({
            "Timestamp":      t.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
            "EquipmentID":    "ETCH-003",
            "ChamberID":      random.choice(["CH-A", "CH-B"]),
            "PressureBar":    round((0.9 if not is_anomaly else 3.2) + random.uniform(-0.05, 0.05), 4),
            "TempCelsius":    round((85.0 if not is_anomaly else 148.0) + random.uniform(-1.5, 1.5), 2),
            "RFPowerWatt":    round((300.0 if not is_anomaly else 510.0) + random.uniform(-5, 5), 1),
            "GasFlowCCM":     round((50.0 if not is_anomaly else 11.0) + random.uniform(-1, 1), 2),
            "ProcessStep":    random.randint(1, 4),
            "AlarmCode":      random.choice(["ALM-5001", "ALM-5002", "ALM-5003", ""]) if is_anomaly else "",
            "Severity":       random.choice(["WARNING", "CRITICAL"]) if is_anomaly else "INFO",
        })

    table = pa.Table.from_pylist(rows)
    path = os.path.join(OUT_DIR, "vendor_c_sensor_trace.parquet")
    pq.write_table(table, path)
    print(f"  vendor_c_sensor_trace.parquet: {len(rows)} rows")


# ============================================================
# 9. Binary Diagnostic Dump
# ============================================================
def gen_binary():
    random.seed(88)
    data = bytearray()

    # Magic header: "SEMIBIN\x00"
    data.extend(b"SEMIBIN\x00")

    # Version: 2 bytes (major.minor)
    data.extend(struct.pack(">BB", 2, 5))

    # Tool ID: 16 bytes, null-padded ASCII
    tool_id = b"ETCH-TOOL-001\x00\x00\x00"
    data.extend(tool_id)

    # Timestamp block marker: 0xFE 0x01
    data.extend(b"\xfe\x01")
    # Unix timestamp as uint32 BE: 2025-01-15T08:00:00Z = 1736928000
    data.extend(struct.pack(">I", 1736928000))
    # Duration in seconds as uint16 BE
    data.extend(struct.pack(">H", 3600))

    # Chamber config block: marker 0xFE 0x02
    data.extend(b"\xfe\x02")
    # Number of chambers: uint8
    data.extend(struct.pack(">B", 4))
    for ch_idx in range(4):
        # Chamber ID: 4 bytes ASCII
        ch_name = f"C{ch_idx+1}\x00\x00".encode()
        data.extend(ch_name[:4])
        # Status byte: 0x01=active, 0x00=inactive
        data.extend(struct.pack(">B", 1 if ch_idx < 3 else 0))

    # Sensor data block: marker 0xFE 0x03
    data.extend(b"\xfe\x03")
    # Number of sensors: uint8
    num_sensors = 4
    data.extend(struct.pack(">B", num_sensors))

    sensor_names = [b"PRES", b"TEMP", b"RFPW", b"GASF"]
    bases = [0.9, 85.0, 300.0, 50.0]
    noises = [0.05, 1.5, 5.0, 1.0]

    for si in range(num_sensors):
        # Sensor header: 4 bytes name
        data.extend(sensor_names[si])
        # Number of readings: uint16 BE
        num_readings = 60
        data.extend(struct.pack(">H", num_readings))
        # Each reading: uint16 timestamp_offset (seconds from base) + float32 value
        for ri in range(num_readings):
            t_offset = ri * 60  # 1 reading per minute
            is_anomaly = random.random() < 0.07
            if is_anomaly:
                val = bases[si] * random.uniform(1.5, 2.5)
            else:
                val = bases[si] + random.uniform(-noises[si], noises[si])
            data.extend(struct.pack(">H", t_offset))
            data.extend(struct.pack(">f", val))

    # Alarm block: marker 0xFE 0x04
    data.extend(b"\xfe\x04")
    # Number of alarms: uint8
    num_alarms = 5
    data.extend(struct.pack(">B", num_alarms))
    for ai in range(num_alarms):
        # Alarm code: uint16
        data.extend(struct.pack(">H", 4200 + ai))
        # Timestamp offset: uint16
        data.extend(struct.pack(">H", random.randint(100, 3500)))
        # Severity: uint8 (1=info, 2=warning, 3=error, 4=critical)
        data.extend(struct.pack(">B", random.choice([2, 3, 4])))

    # Checksum block: marker 0xFE 0xFF
    data.extend(b"\xfe\xff")
    # Simple checksum: sum of all previous bytes mod 2^32
    checksum = sum(data) % (2**32)
    data.extend(struct.pack(">I", checksum))

    # End marker
    data.extend(b"ENDBIN\x00\x00")

    # Pad to ~2KB
    while len(data) < 2048:
        data.extend(struct.pack(">B", random.randint(0, 255)))

    path = os.path.join(OUT_DIR, "binary_diagnostic.bin")
    with open(path, "wb") as f:
        f.write(bytes(data[:2048]))
    print(f"  binary_diagnostic.bin: {len(data[:2048])} bytes")


# ============================================================
# Run all generators
# ============================================================
if __name__ == "__main__":
    print("Generating synthetic semiconductor logs...")
    gen_vendor_a()
    gen_vendor_b()
    gen_euv_xml()
    gen_csv()
    gen_event_log()
    gen_syslog()
    gen_kv_log()
    gen_parquet()
    gen_binary()
    print("Done!")

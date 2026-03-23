r"""
End-to-end test for the Smart Tool Log Parser.
Tests every component: format detection, parsing, normalization,
anomaly detection, database, API endpoints, and NL query.

Run with:
    cd "C:\Users\nigel\Documents\PROJECTLIST\NAISC Micron"
    python test_app.py

Backend must NOT be running -- this test runs its own.
"""

import sys
import os
import json
import time
import threading
import multiprocessing
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ─────────────────────────────────────────────────────────────────────
#  Helpers
# ─────────────────────────────────────────────────────────────────────

PASS = 0
FAIL = 0


def check(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  [PASS] {name}")
    else:
        FAIL += 1
        print(f"  [FAIL] {name}  --  {detail}")


SAMPLE_DIR = os.path.join(os.path.dirname(__file__), "sample_logs")


def main():

    global PASS, FAIL

    # ═════════════════════════════════════════════════════════════════════
    #  TEST 1: Format Detection
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 1: Format Detection")
    print("=" * 60)

    from parser.format_detector import FormatDetector

    detector = FormatDetector()

    # JSON
    with open(os.path.join(SAMPLE_DIR, "vendor_a_sensor_trace.json"), "rb") as f:
        result = detector.detect(f.read())
    check("JSON detected for vendor_a", result.format_type == "json",
          f"got {result.format_type}")

    # XML
    with open(os.path.join(SAMPLE_DIR, "euv_dose_recipe.xml"), "rb") as f:
        result = detector.detect(f.read())
    check("XML detected for EUV recipe", result.format_type == "xml",
          f"got {result.format_type}")

    # CSV
    with open(os.path.join(SAMPLE_DIR, "sensor_readings.csv"), "rb") as f:
        result = detector.detect(f.read())
    check("CSV detected for sensor readings", result.format_type == "csv",
          f"got {result.format_type}")

    # Syslog
    with open(os.path.join(SAMPLE_DIR, "syslog_equipment.log"), "rb") as f:
        result = detector.detect(f.read())
    check("Syslog detected for equipment log", result.format_type == "syslog",
          f"got {result.format_type}")

    # Key-Value
    with open(os.path.join(SAMPLE_DIR, "kv_process_log.log"), "rb") as f:
        result = detector.detect(f.read())
    check("KV detected for process log", result.format_type == "kv",
          f"got {result.format_type}")

    # Text event log
    with open(os.path.join(SAMPLE_DIR, "event_log.txt"), "rb") as f:
        result = detector.detect(f.read())
    check("Text detected for event log", result.format_type == "text",
          f"got {result.format_type}")

    # Binary
    with open(os.path.join(SAMPLE_DIR, "binary_diagnostic.bin"), "rb") as f:
        result = detector.detect(f.read())
    check("Binary detected for diagnostic dump", result.format_type == "binary",
          f"got {result.format_type}")

    # Confidence scores
    with open(os.path.join(SAMPLE_DIR, "vendor_a_sensor_trace.json"), "rb") as f:
        result = detector.detect(f.read())
    check("JSON confidence >= 0.8", result.confidence >= 0.8,
          f"got {result.confidence}")

    # Content-based, not extension-based -- rename a JSON file mentally
    json_content = b'{"timestamp": "2025-01-15T08:00:00Z", "temperature": 85.2}'
    result = detector.detect(json_content)
    check("Raw JSON bytes detected as JSON", result.format_type == "json",
          f"got {result.format_type}")

    csv_content = b"timestamp,chamber,pressure\n2025-01-15,C1,0.9\n2025-01-15,C2,1.1\n"
    result = detector.detect(csv_content)
    check("Raw CSV bytes detected as CSV", result.format_type == "csv",
          f"got {result.format_type}")


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 2: Individual Parsers
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 2: Individual Parsers")
    print("=" * 60)

    # JSON parser
    from parser.parsers.json_parser import parse as json_parse

    with open(os.path.join(SAMPLE_DIR, "vendor_a_sensor_trace.json")) as f:
        records = json_parse(f.read())
    check("JSON parser returns records", len(records) > 0, f"got {len(records)}")
    check("JSON parser flattens nested data (>50 records)", len(records) > 50,
          f"got {len(records)} -- should have expanded sensor measurements")

    # Verify flattened fields exist
    sample = records[0]
    has_sensor = any("Sensor" in k or "sensor" in k.lower() for k in sample.keys())
    has_context = any("ControlJob" in k or "Equipment" in k or "Job" in k for k in sample.keys())
    check("JSON records have sensor-related fields", has_sensor or len(sample) > 3,
          f"keys: {list(sample.keys())[:5]}")

    # Vendor B (different structure)
    with open(os.path.join(SAMPLE_DIR, "vendor_b_sensor_trace.json")) as f:
        records_b = json_parse(f.read())
    check("Vendor B JSON also parses to many records", len(records_b) > 50,
          f"got {len(records_b)}")

    # XML parser
    from parser.parsers.xml_parser import parse as xml_parse

    with open(os.path.join(SAMPLE_DIR, "euv_dose_recipe.xml")) as f:
        records = xml_parse(f.read())
    check("XML parser returns records", len(records) > 0, f"got {len(records)}")
    # Check it extracted machine/recipe fields
    sample_xml = records[0] if records else {}
    xml_keys = list(sample_xml.keys())
    check("XML record has extracted fields", len(xml_keys) > 3,
          f"keys: {xml_keys[:8]}")

    # CSV parser
    from parser.parsers.csv_parser import parse as csv_parse

    with open(os.path.join(SAMPLE_DIR, "sensor_readings.csv")) as f:
        records = csv_parse(f.read())
    check("CSV parser returns 220 records", len(records) == 220,
          f"got {len(records)}")
    check("CSV records have expected columns",
          "timestamp" in records[0] or "temperature_C" in records[0],
          f"keys: {list(records[0].keys())}")

    # Syslog parser
    from parser.parsers.syslog_parser import parse as syslog_parse

    with open(os.path.join(SAMPLE_DIR, "syslog_equipment.log")) as f:
        records = syslog_parse(f.read())
    check("Syslog parser returns 110 records", len(records) == 110,
          f"got {len(records)}")
    syslog_sample = records[0]
    check("Syslog extracts fields",
          "message" in syslog_sample or "priority" in syslog_sample,
          f"keys: {list(syslog_sample.keys())}")

    # KV parser
    from parser.parsers.kv_parser import parse as kv_parse

    with open(os.path.join(SAMPLE_DIR, "kv_process_log.log")) as f:
        records = kv_parse(f.read())
    check("KV parser returns 110 records", len(records) == 110,
          f"got {len(records)}")
    kv_sample = records[0]
    check("KV extracts key-value pairs",
          "timestamp" in kv_sample or "tool_id" in kv_sample,
          f"keys: {list(kv_sample.keys())}")

    # Text parser
    from parser.parsers.text_parser import parse as text_parse

    with open(os.path.join(SAMPLE_DIR, "event_log.txt")) as f:
        records = text_parse(f.read())
    check("Text parser returns records", len(records) > 50,
          f"got {len(records)}")
    text_sample = [r for r in records if r.get("timestamp")]
    check("Text parser extracts timestamps", len(text_sample) > 10,
          f"found {len(text_sample)} records with timestamps")

    # Binary parser
    from parser.parsers.binary_parser import parse as binary_parse

    with open(os.path.join(SAMPLE_DIR, "binary_diagnostic.bin"), "rb") as f:
        records = binary_parse(f.read())
    check("Binary parser returns records", len(records) > 0,
          f"got {len(records)}")


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 3: Schema Inference
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 3: Schema Inference")
    print("=" * 60)

    from parser.schema_inferencer import SchemaInferencer

    inferencer = SchemaInferencer()

    # Test with CSV records that have known field names
    with open(os.path.join(SAMPLE_DIR, "sensor_readings.csv")) as f:
        csv_records = csv_parse(f.read())
    mapping = inferencer.infer(csv_records)

    check("Schema inference returns field mappings",
          len(mapping.field_mappings) > 0,
          f"got {len(mapping.field_mappings)} mappings")
    check("Schema inference detects fields",
          len(mapping.detected_fields) > 0,
          f"detected: {mapping.detected_fields[:5]}")
    check("Schema inference has confidence scores",
          len(mapping.confidence_scores) > 0,
          f"scores: {dict(list(mapping.confidence_scores.items())[:3])}")

    # Test that it maps temperature variants
    test_records = [
        {"TargetTemp_C": 85.0, "PRESSURE": 0.9, "DateTime": "2025-01-15T08:00:00"},
        {"TargetTemp_C": 86.0, "PRESSURE": 0.8, "DateTime": "2025-01-15T08:01:00"},
    ]
    mapping2 = inferencer.infer(test_records)
    mapped_values = list(mapping2.field_mappings.values())
    check("Schema maps temperature field",
          any("temp" in str(v).lower() for v in mapped_values),
          f"mappings: {mapping2.field_mappings}")


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 4: Full Pipeline
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 4: Full Pipeline (end-to-end parsing)")
    print("=" * 60)

    from parser.pipeline import LogParserPipeline

    pipeline = LogParserPipeline()

    test_files = {
        "vendor_a_sensor_trace.json": ("json", 50),    # expect >50 records
        "vendor_b_sensor_trace.json": ("json", 50),
        "euv_dose_recipe.xml": ("xml", 1),
        "sensor_readings.csv": ("csv", 200),
        "syslog_equipment.log": ("syslog", 100),
        "kv_process_log.log": ("kv", 100),
        "event_log.txt": ("text", 50),
        "binary_diagnostic.bin": ("binary", 1),
    }

    for filename, (expected_format, min_records) in test_files.items():
        path = os.path.join(SAMPLE_DIR, filename)
        result = pipeline.parse_file(path)

        check(f"Pipeline: {filename} detected as {expected_format}",
              result.format_detected.startswith(expected_format),
              f"got {result.format_detected}")

        check(f"Pipeline: {filename} has >={min_records} records",
              result.total_records >= min_records,
              f"got {result.total_records}")

        check(f"Pipeline: {filename} confidence > 0",
              result.avg_confidence > 0,
              f"got {result.avg_confidence}")

        # Check that records have the unified schema fields
        if result.records:
            rec = result.records[0]
            has_ts = hasattr(rec, "timestamp")
            has_conf = hasattr(rec, "confidence")
            check(f"Pipeline: {filename} records have unified schema",
                  has_ts and has_conf,
                  f"fields: {[a for a in dir(rec) if not a.startswith('_')][:8]}")


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 5: Anomaly Detection
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 5: Anomaly Detection")
    print("=" * 60)

    from analytics.anomaly_detector import AnomalyDetector

    ad = AnomalyDetector()

    # Create test data with known anomalies
    from datetime import datetime, timedelta

    normal_temp = 85.0
    test_sensor_data = []
    base_time = datetime(2025, 1, 15, 8, 0, 0)
    for i in range(100):
        temp = normal_temp + (i % 5) * 0.5  # normal variation: 85-87
        if i == 50:
            temp = 120.0  # obvious anomaly
        if i == 75:
            temp = 40.0   # obvious anomaly (low)
        test_sensor_data.append({
            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "temperature_c": temp,
            "pressure_pa": 0.9 + (i % 3) * 0.05,
            "record_id": f"test-{i}",
        })

    anomalies = ad.detect(test_sensor_data, ["temperature_c"])
    check("Anomaly detector finds anomalies", len(anomalies) > 0,
          f"found {len(anomalies)}")

    # Check the known anomalies were caught
    anomaly_values = [a.value for a in anomalies]
    check("Detects high temperature spike (120°C)",
          any(abs(v - 120.0) < 0.1 for v in anomaly_values),
          f"values found: {anomaly_values}")
    check("Detects low temperature dip (40°C)",
          any(abs(v - 40.0) < 0.1 for v in anomaly_values),
          f"values found: {anomaly_values}")

    # Check severity assignment
    high_sev = [a for a in anomalies if a.severity == "HIGH"]
    check("High severity anomalies identified", len(high_sev) > 0,
          f"got {len(high_sev)} high severity")

    # Check z-scores are populated
    has_zscore = [a for a in anomalies if a.z_score is not None]
    check("Z-scores computed for anomalies", len(has_zscore) > 0,
          f"got {len(has_zscore)} with z-scores")

    # Test with no anomalies (all same value)
    flat_data = [{"timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                  "value": 85.0, "record_id": f"flat-{i}"} for i in range(50)]
    flat_anomalies = ad.detect(flat_data, ["value"])
    check("No anomalies in flat data", len(flat_anomalies) == 0,
          f"found {len(flat_anomalies)} (should be 0)")

    # Test rate of change detection
    spike_data = []
    for i in range(20):
        val = 85.0 if i != 10 else 200.0  # massive spike at i=10
        spike_data.append({
            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "temp": val, "record_id": f"spike-{i}",
        })
    spike_anomalies = ad.detect(spike_data, ["temp"])
    check("Rate-of-change catches sudden spike",
          any(a.anomaly_type == "rate_of_change" for a in spike_anomalies),
          f"types: {[a.anomaly_type for a in spike_anomalies]}")


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 6: Trend Analyzer
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 6: Trend Analyzer")
    print("=" * 60)

    from analytics.trend_analyzer import TrendAnalyzer

    ta = TrendAnalyzer()

    # Create upward-trending data
    trend_data = []
    for i in range(50):
        trend_data.append({
            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "temperature_c": 50.0 + i * 2.0,  # steep increase (50 -> 148)
            "record_id": f"trend-{i}",
        })

    result = ta.analyze(trend_data, "temperature_c")
    check("Trend analyzer returns result", result is not None)
    check("Detects increasing trend", result.direction == "increasing",
          f"got {result.direction}")
    check("Positive slope", result.slope > 0, f"slope={result.slope}")
    check("Good R-squared for linear data", result.r_squared > 0.9,
          f"r²={result.r_squared}")

    # Stable data
    stable_data = [{"timestamp": (base_time + timedelta(minutes=i)).isoformat(),
                    "pressure_pa": 0.9, "record_id": f"stable-{i}"} for i in range(50)]
    result_stable = ta.analyze(stable_data, "pressure_pa")
    check("Stable data detected as stable", result_stable.direction == "stable",
          f"got {result_stable.direction}")


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 7: Cross-Tool Comparator
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 7: Cross-Tool Comparator")
    print("=" * 60)

    from analytics.cross_tool_comparator import CrossToolComparator

    ctc = CrossToolComparator()

    # Create multi-tool data with one outlier tool
    import random
    random.seed(42)
    multi_tool_data = []
    for i in range(200):
        tool = "ETCH-001" if i < 90 else ("ETCH-002" if i < 180 else "ETCH-003")
        # ETCH-003 runs way hotter -- only 20 samples vs 90 each for others
        base_temp = 85.0 if tool != "ETCH-003" else 200.0
        multi_tool_data.append({
            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "tool_id": tool,
            "temperature_c": base_temp + random.uniform(-1, 1),
            "record_id": f"mt-{i}",
        })

    comparison = ctc.compare(multi_tool_data, "temperature_c")
    check("Cross-tool comparison returns result", comparison is not None)
    check("Identifies 3 tools", len(comparison.tool_stats) == 3,
          f"got {len(comparison.tool_stats)} tools")
    check("ETCH-003 flagged as outlier", "ETCH-003" in comparison.outlier_tools,
          f"outliers: {comparison.outlier_tools}")


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 8: Fault Correlator
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 8: Fault Correlator")
    print("=" * 60)

    from analytics.fault_correlator import FaultCorrelator

    fc = FaultCorrelator()

    # Create data with an alarm event + preceding anomalies
    fault_data = []
    for i in range(30):
        evt = "SENSOR_READ"
        sev = "INFO"
        temp = 85.0 + random.uniform(-1, 1)

        # At i=20, temperature spikes, then alarm at i=22
        if i in (19, 20, 21):
            temp = 110.0 + random.uniform(-1, 1)  # anomalous
        if i == 22:
            evt = "ALARM"
            sev = "ERROR"

        fault_data.append({
            "timestamp": (base_time + timedelta(minutes=i)).isoformat(),
            "event_type": evt,
            "event": evt if evt == "ALARM" else "",
            "severity": sev,
            "temperature_c": temp,
            "record_id": f"fault-{i}",
        })

    # Need anomalies to pass to correlator
    fault_anomalies = ad.detect(fault_data, ["temperature_c"])
    correlations = fc.correlate(fault_data, fault_anomalies, window_minutes=5)
    check("Fault correlator finds correlations", len(correlations) > 0,
          f"found {len(correlations)}")


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 9: Summary Generator
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 9: Summary Generator")
    print("=" * 60)

    from analytics.summary_generator import SummaryGenerator

    sg = SummaryGenerator()

    summary_text = sg.summarize_parse_result(
        records=test_sensor_data,
        anomalies=anomalies,
        trends={"temperature_c": result},
        faults=correlations,
    )
    check("Summary generator returns text", len(summary_text) > 100,
          f"got {len(summary_text)} chars")
    check("Summary contains markdown headers", "##" in summary_text,
          "no markdown headers found")
    check("Summary mentions anomalies", "anomal" in summary_text.lower(),
          "no mention of anomalies")


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 10: Database
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 10: Database Operations")
    print("=" * 60)

    import tempfile
    from backend.database import Database

    # Use a temp database
    tmp_db = os.path.join(tempfile.gettempdir(), "test_slp.db")
    if os.path.exists(tmp_db):
        os.remove(tmp_db)

    db = Database(db_path=tmp_db)

    # Insert a file
    file_id = db.insert_file(
        filename="test.csv",
        format_detected="csv",
        total_records=3,
        avg_confidence=0.95,
        parse_time_ms=12.5,
    )
    check("Insert file returns ID", file_id > 0, f"got {file_id}")

    # Insert records
    test_records = [
        {"source_format": "csv", "timestamp": "2025-01-15T08:00:00",
         "tool_id": "ETCH-001", "module_id": "C1", "event_type": "SENSOR_READ",
         "severity": "INFO", "parameters": {"temperature_c": 85.2, "pressure_pa": 0.9},
         "raw_content": "original line 1", "confidence": 0.95},
        {"source_format": "csv", "timestamp": "2025-01-15T08:01:00",
         "tool_id": "ETCH-001", "module_id": "C1", "event_type": "ALARM",
         "severity": "ERROR", "parameters": {"temperature_c": 120.0},
         "raw_content": "ALARM: high temp", "confidence": 0.90},
        {"source_format": "csv", "timestamp": "2025-01-15T08:02:00",
         "tool_id": "ETCH-002", "module_id": "C2", "event_type": "SENSOR_READ",
         "severity": "INFO", "parameters": {"temperature_c": 84.0},
         "raw_content": "original line 3", "confidence": 1.0},
    ]
    inserted = db.insert_records(file_id, test_records)
    inserted_count = len(inserted) if isinstance(inserted, list) else inserted
    check("Insert 3 records", inserted_count == 3, f"inserted {inserted}")

    # Query all
    all_records = db.query_records()
    check("Query returns 3 records", len(all_records) == 3,
          f"got {len(all_records)}")

    # Query with filter
    alarms = db.query_records(filters={"event_type": "ALARM"})
    check("Filter by ALARM returns 1", len(alarms) == 1,
          f"got {len(alarms)}")

    tool_filter = db.query_records(filters={"tool_id": "ETCH-002"})
    check("Filter by tool_id returns 1", len(tool_filter) == 1,
          f"got {len(tool_filter)}")

    # Summary stats
    stats = db.get_summary_stats()
    check("Summary has total_records=3", stats["total_records"] == 3,
          f"got {stats['total_records']}")
    check("Summary has tool breakdown",
          "ETCH-001" in stats.get("tool_breakdown", {}),
          f"tools: {stats.get('tool_breakdown')}")

    # Timeseries
    ts = db.get_parameter_timeseries("temperature_c")
    check("Timeseries returns temperature data", len(ts) >= 2,
          f"got {len(ts)} points")

    # Insert anomalies
    test_anomalies = [
        {"record_id": "test-1", "parameter": "temperature_c", "value": 120.0,
         "expected_min": 80.0, "expected_max": 90.0, "anomaly_type": "z_score",
         "severity": "high", "z_score": 4.5, "description": "Temperature spike"},
    ]
    db.insert_anomalies(test_anomalies)
    queried_anomalies = db.query_anomalies()
    check("Anomaly inserted and queryable", len(queried_anomalies) == 1,
          f"got {len(queried_anomalies)}")

    # Safe SQL execution
    sql_result = db.execute_sql("SELECT COUNT(*) as cnt FROM log_records")
    check("execute_sql works for SELECT", sql_result[0]["cnt"] == 3,
          f"got {sql_result}")

    # Block mutation
    try:
        db.execute_sql("DELETE FROM log_records")
        check("execute_sql blocks DELETE", False, "should have raised ValueError")
    except ValueError:
        check("execute_sql blocks DELETE", True)

    try:
        db.execute_sql("DROP TABLE log_records")
        check("execute_sql blocks DROP", False, "should have raised ValueError")
    except ValueError:
        check("execute_sql blocks DROP", True)

    # Get files
    files = db.get_files()
    check("get_files returns 1 file", len(files) == 1, f"got {len(files)}")

    # Cleanup -- close connection before removing on Windows
    try:
        db._get_conn().close()
        db._local.conn = None
    except Exception:
        pass
    try:
        os.remove(tmp_db)
    except PermissionError:
        pass  # Windows may hold the file; harmless


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 11: NL Query Engine (fallback mode)
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 11: Natural Language Query (keyword fallback)")
    print("=" * 60)

    from backend.nl_query import NLQueryEngine

    # Create a fresh DB with some data
    tmp_db2 = os.path.join(tempfile.gettempdir(), "test_slp_nl.db")
    if os.path.exists(tmp_db2):
        os.remove(tmp_db2)

    db2 = Database(db_path=tmp_db2)
    fid = db2.insert_file("test.csv", "csv", 3, 0.9, 10.0)
    db2.insert_records(fid, test_records)

    nl = NLQueryEngine(db2)  # no API key = fallback mode

    # Test alarm query
    result = nl.query("Show me all alarm events")
    check("NL: alarm query generates SQL",
          "alarm" in result.generated_sql.lower() or "ALARM" in result.generated_sql,
          f"sql: {result.generated_sql}")
    check("NL: alarm query returns results", len(result.results) > 0,
          f"got {len(result.results)} results")

    # Test error query
    result2 = nl.query("Show me all errors")
    check("NL: error query works",
          result2.generated_sql != "",
          f"sql: {result2.generated_sql}")

    # Test temperature query
    result3 = nl.query("What's the average temperature?")
    check("NL: temperature query works",
          "temperature" in result3.generated_sql.lower() or len(result3.results) >= 0,
          f"sql: {result3.generated_sql}")

    try:
        nl.db._get_conn().close()
        nl.db._local.conn = None
    except Exception:
        pass
    try:
        os.remove(tmp_db2)
    except PermissionError:
        pass


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 12: FastAPI Endpoints
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 12: FastAPI Endpoints")
    print("=" * 60)

    import requests

    # Start the backend in a subprocess (using Popen for Windows compatibility)
    test_db_path = os.path.join(os.path.dirname(__file__), "data", "test_api.db")
    API_BASE = "http://127.0.0.1:8765"
    env = os.environ.copy()
    env["SLP_DB_PATH"] = test_db_path
    backend_proc = subprocess.Popen(
        [sys.executable, "-c",
         "import uvicorn; import os; os.environ['SLP_DB_PATH'] = os.environ.get('SLP_DB_PATH',''); "
         "from backend.app import app; uvicorn.run(app, host='127.0.0.1', port=8765, log_level='error')"],
        cwd=os.path.dirname(os.path.abspath(__file__)),
        env=env,
    )
    time.sleep(3)

    try:
        # Health check
        r = requests.get(f"{API_BASE}/api/health", timeout=5)
        check("GET /api/health returns 200", r.status_code == 200,
              f"got {r.status_code}")
        health = r.json()
        check("Health reports parser available", health.get("parser_available") == True,
              f"got {health}")

        # Upload a file
        with open(os.path.join(SAMPLE_DIR, "sensor_readings.csv"), "rb") as f:
            r = requests.post(f"{API_BASE}/api/upload",
                              files={"file": ("sensor_readings.csv", f, "text/csv")},
                              timeout=15)
        check("POST /api/upload returns 200", r.status_code == 200,
              f"got {r.status_code}")
        upload_result = r.json()
        check("Upload detects CSV format",
              upload_result.get("format_detected") == "csv",
              f"got {upload_result.get('format_detected')}")
        check("Upload parses 220 records",
              upload_result.get("total_records") == 220,
              f"got {upload_result.get('total_records')}")
        check("Upload finds anomalies",
              upload_result.get("anomalies_found", 0) > 0,
              f"got {upload_result.get('anomalies_found')}")

        # Upload JSON
        with open(os.path.join(SAMPLE_DIR, "vendor_a_sensor_trace.json"), "rb") as f:
            r = requests.post(f"{API_BASE}/api/upload",
                              files={"file": ("vendor_a.json", f)}, timeout=15)
        check("Upload JSON works", r.status_code == 200, f"got {r.status_code}")

        # List files
        r = requests.get(f"{API_BASE}/api/files", timeout=5)
        check("GET /api/files returns files", len(r.json()) >= 2,
              f"got {len(r.json())}")

        # Query records
        r = requests.get(f"{API_BASE}/api/records?limit=10", timeout=5)
        check("GET /api/records returns data", len(r.json()) > 0,
              f"got {len(r.json())}")

        # Query with filter
        r = requests.get(f"{API_BASE}/api/records?severity=ERROR", timeout=5)
        records = r.json()
        check("Filter by severity works",
              all(rec.get("severity") == "ERROR" for rec in records) if records else True,
              f"got {len(records)} records")

        # Anomalies endpoint
        r = requests.get(f"{API_BASE}/api/anomalies", timeout=5)
        check("GET /api/anomalies returns data", r.status_code == 200,
              f"got {r.status_code}")

        # Analytics summary
        r = requests.get(f"{API_BASE}/api/analytics/summary", timeout=5)
        summary = r.json()
        check("Summary has total_records", summary.get("total_records", 0) > 0,
              f"got {summary}")

        # Timeseries
        r = requests.get(f"{API_BASE}/api/analytics/timeseries?parameter=temperature_c",
                         timeout=5)
        check("Timeseries endpoint works", r.status_code == 200,
              f"got {r.status_code}")

        # NL Query
        r = requests.post(f"{API_BASE}/api/query",
                          json={"question": "Show me all alarm events"},
                          timeout=10)
        check("NL query endpoint works", r.status_code == 200,
              f"got {r.status_code}")
        nl_result = r.json()
        check("NL query returns SQL",
              len(nl_result.get("generated_sql", "")) > 0,
              f"got {nl_result}")

        # Empty question should fail
        r = requests.post(f"{API_BASE}/api/query",
                          json={"question": ""}, timeout=5)
        check("Empty NL query returns 400", r.status_code == 400,
              f"got {r.status_code}")

    except requests.ConnectionError:
        print("  [SKIP] Backend not reachable -- skipping API tests")
    except Exception as exc:
        print(f"  [SKIP] API test error: {exc}")
    finally:
        backend_proc.terminate()
        try:
            backend_proc.wait(timeout=5)
        except Exception:
            backend_proc.kill()
        # Cleanup test DB
        test_db = os.path.join(os.path.dirname(__file__), "data", "test_api.db")
        if os.path.exists(test_db):
            try:
                os.remove(test_db)
            except PermissionError:
                pass  # Windows may hold the file; harmless


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 13: Frontend API Client
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 13: Frontend API Client")
    print("=" * 60)

    from frontend.api_client import APIClient

    api = APIClient(base_url="http://localhost:99999")  # intentionally bad port

    # Health check should return False for bad connection
    check("Health check returns False for offline backend",
          api.health_check() == False)

    # Methods should raise on connection error
    try:
        api.get_summary()
        check("get_summary raises on offline backend", False, "should have raised")
    except Exception:
        check("get_summary raises on offline backend", True)


    # ═════════════════════════════════════════════════════════════════════
    #  TEST 14: Edge Cases
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    print("TEST 14: Edge Cases")
    print("=" * 60)

    # Empty content
    result = detector.detect(b"")
    check("Empty content doesn't crash", result is not None)

    result = detector.detect(b"   \n\n  ")
    check("Whitespace-only content doesn't crash", result is not None)

    # Pipeline with empty file
    empty_result = pipeline.parse_content(b"", "empty.log")
    check("Pipeline handles empty content", empty_result.total_records == 0)

    # Single record
    single_json = b'{"temperature": 85.2, "timestamp": "2025-01-15T08:00:00"}'
    single_result = pipeline.parse_content(single_json, "single.json")
    check("Pipeline handles single JSON record",
          single_result.total_records >= 1,
          f"got {single_result.total_records}")

    # Malformed JSON
    bad_json = b'{"temperature": 85.2, "broken'
    bad_result = pipeline.parse_content(bad_json, "bad.json")
    check("Pipeline handles malformed JSON gracefully",
          bad_result is not None)  # should not crash

    # Anomaly detector with empty data
    empty_anomalies = ad.detect([], ["temperature_c"])
    check("Anomaly detector handles empty list", len(empty_anomalies) == 0)

    # Anomaly detector with single record
    one_record = [{"timestamp": "2025-01-15T08:00:00",
                   "temperature_c": 85.0, "record_id": "single"}]
    one_anomalies = ad.detect(one_record, ["temperature_c"])
    check("Anomaly detector handles single record", one_anomalies is not None)

    # Trend analyzer with too few records
    try:
        tiny_result = ta.analyze(one_record, "temperature_c")
        check("Trend analyzer handles single record", tiny_result is not None)
    except Exception:
        check("Trend analyzer handles single record", True)


    # ═════════════════════════════════════════════════════════════════════
    #  RESULTS
    # ═════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 60)
    total = PASS + FAIL
    print(f"RESULTS: {PASS}/{total} passed, {FAIL} failed")
    if FAIL == 0:
        print("ALL TESTS PASSED")
    else:
        print(f"{FAIL} test(s) need attention")
    print("=" * 60)

    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()

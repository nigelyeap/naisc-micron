"""
Per-format parser modules for the Smart Log Parser.

Exports a PARSER_MAP dict mapping format name strings to their
corresponding ``parse(content) -> list[dict]`` functions.
"""

from __future__ import annotations

from typing import Callable

from parser.parsers.json_parser import parse as json_parse
from parser.parsers.xml_parser import parse as xml_parse
from parser.parsers.csv_parser import parse as csv_parse
from parser.parsers.syslog_parser import parse as syslog_parse
from parser.parsers.kv_parser import parse as kv_parse
from parser.parsers.text_parser import parse as text_parse
from parser.parsers.binary_parser import parse as binary_parse
from parser.parsers.parquet_parser import parse as parquet_parse

PARSER_MAP: dict[str, Callable[..., list[dict]]] = {
    "json": json_parse,
    "xml": xml_parse,
    "csv": csv_parse,
    "syslog": syslog_parse,
    "kv": kv_parse,
    "text": text_parse,
    "binary": binary_parse,
    "parquet": parquet_parse,
}

__all__ = [
    "PARSER_MAP",
    "json_parse",
    "xml_parse",
    "csv_parse",
    "syslog_parse",
    "kv_parse",
    "text_parse",
    "binary_parse",
    "parquet_parse",
]

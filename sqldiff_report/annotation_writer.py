"""Write annotation output to stdout or a file."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from sqldiff_report.annotation_engine import Annotation
from sqldiff_report.annotation_formatter import format_annotations_text, format_annotations_dict


@dataclass
class AnnotationWriteOptions:
    fmt: str = "text"          # "text" or "json"
    colour: bool = True
    output_path: Optional[Path] = None


def write_annotations(
    annotations: List[Annotation],
    options: AnnotationWriteOptions,
) -> None:
    """Serialise *annotations* and write to stdout or *options.output_path*."""
    if options.fmt == "json":
        payload = json.dumps(format_annotations_dict(annotations), indent=2)
    else:
        payload = format_annotations_text(annotations, colour=options.colour and options.output_path is None)

    if options.output_path is not None:
        options.output_path.write_text(payload, encoding="utf-8")
    else:
        print(payload)

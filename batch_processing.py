import csv
import time
from pathlib import Path
from typing import Dict, Iterator, List

from cryptography.fernet import Fernet

from pii import protect_record


def read_batches(path: Path, batch_size: int) -> Iterator[List[Dict[str, str]]]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        batch = []
        for record in reader:
            batch.append(record)
            if len(batch) == batch_size:
                yield batch
                batch = []
        if batch:
            yield batch


def protect_csv(input_path: Path, output_path: Path, key_path: Path, batch_size: int = 1000) -> Dict[str, float]:
    if key_path.exists():
        cipher = Fernet(key_path.read_bytes())
    else:
        key_path.parent.mkdir(parents=True, exist_ok=True)
        key_path.write_bytes(Fernet.generate_key())
        cipher = Fernet(key_path.read_bytes())

    output_path.parent.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    rows_processed = 0
    pii_values = 0

    with output_path.open("w", newline="", encoding="utf-8") as destination:
        writer = None
        for batch in read_batches(input_path, batch_size):
            protected_batch = []
            for record in batch:
                protected, fields = protect_record(record, cipher)
                protected_batch.append(protected)
                pii_values += len(fields)
            rows_processed += len(protected_batch)
            if writer is None:
                writer = csv.DictWriter(destination, fieldnames=list(protected_batch[0]))
                writer.writeheader()
            writer.writerows(protected_batch)

    elapsed = time.perf_counter() - started
    return {
        "rows_processed": rows_processed,
        "pii_values_detected": pii_values,
        "seconds": round(elapsed, 6),
        "rows_per_second": round(rows_processed / elapsed, 2) if elapsed else 0,
    }

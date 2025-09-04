import argparse
import json
import os
import sys
import time
from copy import deepcopy
from typing import Any, Dict, List, Tuple


def parse_args(argv: List[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Generate dummy records by cloning a sample object from a JSON file and "
            "overriding specified fields with unique values."
        )
    )
    parser.add_argument(
        "input_json",
        help=(
            "Path to input JSON file. The file may contain a single object or an array of objects. "
            "Output will always be an array."
        ),
    )
    parser.add_argument(
        "unique_fields",
        help=(
            "Comma-separated list of field paths to make unique (e.g., 'id, info.name'). "
            "Use dot notation for nested fields."
        ),
    )
    parser.add_argument(
        "remove_fields",
        help=(
            "Comma-separated list of field paths to remove before export (e.g., 'sensitive, info.secret'). "
            "Use dot notation for nested fields."
        ),
    )
    parser.add_argument(
        "count",
        type=int,
        help="Number of dummy records to generate and append.",
    )
    return parser.parse_args(argv)


def load_json(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_array(data: Any) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Ensures the returned container is a list of dicts (objects).
    Returns (array_data, sample_object)

    - If data is a dict, treat it as [data]. Sample is data.
    - If data is a list:
        - If empty: use {} as sample.
        - If elements are not dicts, raise an error.
    """
    if isinstance(data, dict):
        return [data], data
    if isinstance(data, list):
        if not data:
            return [], {}
        first = data[0]
        if not isinstance(first, dict):
            raise ValueError("Input array must contain JSON objects (dicts) as elements.")
        return data, first
    raise ValueError("Input JSON must be an object or an array of objects.")


def parse_unique_fields(s: str) -> List[str]:
    parts = [p.strip() for p in s.split(",")]
    return [p for p in parts if p]


def set_by_path(obj: Dict[str, Any], path: str, value: Any) -> None:
    keys = path.split(".")
    cur: Dict[str, Any] = obj
    for k in keys[:-1]:
        nxt = cur.get(k)
        if not isinstance(nxt, dict):
            nxt = {}
            cur[k] = nxt
        cur = nxt
    cur[keys[-1]] = value


def remove_by_path(obj: Dict[str, Any], path: str) -> None:
    """Safely remove a nested key specified by dot notation. If any segment is missing, do nothing."""
    if not path:
        return
    keys = path.split(".")
    cur: Any = obj
    for k in keys[:-1]:
        if not isinstance(cur, dict):
            return
        if k not in cur:
            return
        cur = cur[k]
    if isinstance(cur, dict):
        cur.pop(keys[-1], None)


def generate_unique_value(base_ts: int, field_path: str, index: int) -> str:
    return f"{base_ts}-{field_path}-{index}"


def generate_records(sample: Dict[str, Any], unique_paths: List[str], count: int) -> List[Dict[str, Any]]:
    base_ts = int(time.time() * 1000)
    out: List[Dict[str, Any]] = []
    for i in range(1, count + 1):
        item = deepcopy(sample)
        for p in unique_paths:
            set_by_path(item, p, generate_unique_value(base_ts, p, i))
        out.append(item)
    return out


def main(argv: List[str]) -> int:
    args = parse_args(argv)

    input_path = args.input_json
    unique_fields_arg = args.unique_fields
    remove_fields_arg = args.remove_fields
    count = args.count

    if not os.path.isfile(input_path):
        print(f"[ERROR] Input file not found: {input_path}")
        return 1

    if count is None or count <= 0:
        print("[ERROR] 'count' must be a positive integer.")
        return 1

    unique_paths = parse_unique_fields(unique_fields_arg)
    if not unique_paths:
        print("[ERROR] Provide at least one unique field path (comma-separated). Example: id, info.name")
        return 1

    # Parse fields to remove (can be empty list)
    remove_paths = parse_unique_fields(remove_fields_arg)

    try:
        data = load_json(input_path)
    except Exception as e:
        print(f"[ERROR] Failed to load JSON from {input_path}: {e}")
        return 1

    try:
        arr, sample = ensure_array(data)
    except Exception as e:
        print(f"[ERROR] {e}")
        return 1

    generated = generate_records(sample, unique_paths, count)

    final_array: List[Dict[str, Any]] = []
    # Copy the original list (if data was an object, arr has one element)
    if isinstance(arr, list):
        final_array = list(arr)
    else:
        final_array = [arr]

    final_array.extend(generated)

    # Remove specified fields from all records before export
    if remove_paths:
        for obj in final_array:
            if isinstance(obj, dict):
                for p in remove_paths:
                    remove_by_path(obj, p)

    # Output path in the same directory as input
    base_ts = int(time.time() * 1000)
    out_name = f"{base_ts}-dummy-{count}.json"
    out_dir = os.path.dirname(os.path.abspath(input_path))
    out_path = os.path.join(out_dir, out_name)

    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(final_array, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[ERROR] Failed to write output JSON to {out_path}: {e}")
        return 1

    print("[INFO] Generation completed.")
    print(f"[INFO] Input: {input_path}")
    print(f"[INFO] Unique fields: {', '.join(unique_paths)}")
    print(f"[INFO] Removed fields: {', '.join(remove_paths) if remove_paths else '(none)'}")
    print(f"[INFO] Generated records: {count}")
    print(f"[INFO] Output: {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

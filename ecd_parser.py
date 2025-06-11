"""ECD Parser

This script validates opening balances (I155) against closing balances by cost center (I355)
and inserts X935 correction records when differences are found.
"""

import argparse
from typing import Dict, List, Tuple


def parse_decimal(value: str) -> float:
    """Convert a decimal number that uses comma as decimal separator."""
    value = value.strip().replace('.', '').replace(',', '.')
    try:
        return float(value)
    except ValueError:
        return 0.0


def format_decimal(value: float) -> str:
    """Format number to SPED decimal format using comma."""
    return f"{value:.2f}".replace('.', ',')


def parse_ecd_file(path: str) -> Tuple[Dict[str, float], Dict[str, Dict[str, float]]]:
    """Read ECD file and collect balances for I155 and I355 records."""
    i155: Dict[str, float] = {}
    i355: Dict[str, Dict[str, float]] = {}

    with open(path, 'r', encoding='latin1') as f:
        for line in f:
            parts = line.rstrip('\n').split('|')
            if len(parts) < 9:
                continue
            reg = parts[1]
            if reg == 'I155':
                account = parts[2]
                value = parse_decimal(parts[8])
                i155[account] = i155.get(account, 0.0) + value
            elif reg == 'I355':
                account = parts[2]
                cost_center = parts[4]
                value = parse_decimal(parts[8])
                cc_map = i355.setdefault(account, {})
                cc_map[cost_center] = cc_map.get(cost_center, 0.0) + value
    return i155, i355


def compute_differences(i155: Dict[str, float], i355: Dict[str, Dict[str, float]]) -> Dict[str, float]:
    """Return accounts where opening balance differs from sum of cost center balances."""
    diffs: Dict[str, float] = {}
    for account, opening in i155.items():
        closing_total = sum(i355.get(account, {}).values())
        diff = round(opening - closing_total, 2)
        if abs(diff) > 0:
            diffs[account] = diff
    return diffs


def generate_x935_records(differences: Dict[str, float]) -> List[str]:
    """Create X935 records for each difference."""
    records = []
    for account, diff in differences.items():
        records.append(f"|X935|{account}|{format_decimal(diff)}|\n")
    return records


def write_corrected_file(input_path: str, output_path: str, x935_records: List[str]) -> None:
    """Copy input file to output inserting X935 records before X990."""
    with open(input_path, 'r', encoding='latin1') as src, open(output_path, 'w', encoding='latin1') as dst:
        for line in src:
            parts = line.rstrip('\n').split('|')
            if len(parts) > 1 and parts[1] == 'X990':
                for rec in x935_records:
                    dst.write(rec)
                dst.write(line)
            else:
                dst.write(line)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate ECD balances and insert X935 corrections")
    parser.add_argument('--input', required=True, help='Input ECD file')
    parser.add_argument('--output', required=True, help='Output corrected ECD file')
    args = parser.parse_args()

    i155, i355 = parse_ecd_file(args.input)
    diffs = compute_differences(i155, i355)
    x935_records = generate_x935_records(diffs)
    write_corrected_file(args.input, args.output, x935_records)

    if x935_records:
        print(f"Inserted {len(x935_records)} X935 record(s) into {args.output}")
    else:
        print("No differences found. File copied without modifications.")


if __name__ == '__main__':
    main()

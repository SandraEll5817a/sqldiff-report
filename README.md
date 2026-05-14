# sqldiff-report

> Generates human-readable schema diff reports between two database snapshots to simplify migration reviews.

---

## Installation

```bash
pip install sqldiff-report
```

Or install from source:

```bash
git clone https://github.com/yourname/sqldiff-report.git
cd sqldiff-report
pip install .
```

---

## Usage

Compare two database snapshots and generate a diff report:

```bash
sqldiff-report --before snapshot_v1.sql --after snapshot_v2.sql --output report.md
```

You can also use it programmatically:

```python
from sqldiff_report import generate_report

report = generate_report(before="snapshot_v1.sql", after="snapshot_v2.sql")
print(report)
```

The output includes a summary of:
- **Added** tables, columns, and indexes
- **Removed** tables, columns, and indexes
- **Modified** column types, constraints, and defaults

### Supported Formats

| Format | Flag |
|--------|------|
| Markdown | `--format md` |
| Plain text | `--format txt` |
| HTML | `--format html` |

---

## Example Output

```
## Schema Diff Report

### Added Tables
- `user_sessions`

### Modified Tables
- `users`
  - Column `email`: NOT NULL constraint added
  - Column `created_at`: default changed to `NOW()`
```

---

## License

This project is licensed under the [MIT License](LICENSE).
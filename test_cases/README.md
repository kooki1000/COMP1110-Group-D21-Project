# Test Cases

These tests check the final transport-advisor behaviour against the main report scenarios and a small set of invalid-input cases.

Run from the project root:

```bash
python test_cases/tester.py
```

Files:

- `route_test_cases.csv`: expected top-ranked routes for the report scenarios.
- `invalid_query_test_cases.csv`: validation checks for incomplete or invalid route searches.
- `tester.py`: executes the tests against the current project data.

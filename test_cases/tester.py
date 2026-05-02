from pathlib import Path
import csv
import sys

ROOT = Path(__file__).resolve().parents[1]
TEST_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from journey_finder import find_all_journeys
from network_loader import load_network
from scorer import rank_journeys
from validator import validate_journey_results, validate_query


def rows(name):
    with open(TEST_DIR / name, newline='', encoding='utf-8-sig') as file:
        return list(csv.DictReader(file))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def run_route_tests(stops, graph):
    for row in rows('route_test_cases.csv'):
        journeys = find_all_journeys(graph, row['origin_id'], row['destination_id'], max_depth=8)
        result = validate_journey_results(journeys, row['origin_id'], row['destination_id'], stops)
        require(result.ok, f"{row['test_id']}: {result.error}")
        ranked = rank_journeys(journeys, row['preference'], stops, top_n=5)
        require(ranked, f"{row['test_id']}: no route returned")
        top = ranked[0]
        expected_stop_ids = row['expected_stop_ids'].split('>')
        require(top['total_duration'] == int(row['expected_duration']), f"{row['test_id']}: duration mismatch")
        require(top['total_cost'] == float(row['expected_cost']), f"{row['test_id']}: cost mismatch")
        require(top['num_segments'] == int(row['expected_segments']), f"{row['test_id']}: segment count mismatch")
        require(top['stop_ids'] == expected_stop_ids, f"{row['test_id']}: stop sequence mismatch")
        print(f"[PASS] {row['test_id']} | {top['total_duration']} min | HK${top['total_cost']:.0f} | {top['num_segments']} segments | {' > '.join(top['stop_ids'])}")


def run_invalid_query_tests(stops, graph):
    for row in rows('invalid_query_test_cases.csv'):
        result = validate_query(row['origin_id'], row['destination_id'], row['preference'], stops, graph)
        require(not result.ok, f"{row['test_id']}: invalid search passed")
        require(row['expected_error_contains'].lower() in result.error.lower(), f"{row['test_id']}: wrong error message")
        print(f"[PASS] {row['test_id']} | {result.error}")


def run_data_tests(stops, segments, graph):
    stop_ids = set(stops)
    require(len(stops) == 21, f"expected 21 stops, got {len(stops)}")
    require(len(segments) == 66, f"expected 66 segments, got {len(segments)}")
    for segment in segments:
        require(segment['from_stop_id'] in stop_ids, f"unknown from_stop_id: {segment}")
        require(segment['to_stop_id'] in stop_ids, f"unknown to_stop_id: {segment}")
        require(segment['duration'] >= 0, f"negative duration: {segment}")
        require(segment['cost'] >= 0, f"negative cost: {segment}")
    unreachable = []
    for origin in stops:
        for destination in stops:
            if origin == destination:
                continue
            if not find_all_journeys(graph, origin, destination, max_depth=8):
                unreachable.append((origin, destination))
    require(not unreachable, f"unreachable stop pairs: {unreachable}")
    print('[PASS] DATA | 21 stops | 66 directed segments | all stop pairs reachable')


def main():
    stops, segments, graph = load_network(ROOT / 'data' / 'stops.csv', ROOT / 'data' / 'segments.csv')
    run_data_tests(stops, segments, graph)
    run_route_tests(stops, graph)
    run_invalid_query_tests(stops, graph)
    print('\nAll test cases passed.')


if __name__ == '__main__':
    main()

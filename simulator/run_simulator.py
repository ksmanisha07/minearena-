import argparse
from simulator import run_scenario

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--patient",
        default="P-001",
        help="Patient ID"
    )
    parser.add_argument(
        "--scenario",
        default="stable_recovery",
        help="Scenario name"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=5,
        help="Seconds between readings"
    )

    args = parser.parse_args()

    run_scenario(
        args.scenario,
        args.patient,
        args.interval,
    )
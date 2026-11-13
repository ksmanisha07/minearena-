
import time
import pandas as pd
from simulator import send_reading

BIDMC_FILE = "data/bidmc_01_Numerics.csv"
PATIENT_ID = "P-004"
SPEED_MULTIPLIER = 10


def replay_bidmc_data():
    df = pd.read_csv(BIDMC_FILE)

    required_columns = [
        "HR",
        "SpO2",
        "RESP",
    ]

    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"Missing required column: {column}")

    print(f"Replaying {len(df)} BIDMC readings for {PATIENT_ID}")

    for index, row in df.iterrows():
        heart_rate = row.get("HR")
        spo2 = row.get("SpO2")
        respiratory_rate = row.get("RESP")

        if pd.notna(heart_rate):
            send_reading("heart_rate", float(heart_rate), PATIENT_ID)

        if pd.notna(spo2):
            send_reading("spo2", float(spo2), PATIENT_ID)

        if pd.notna(respiratory_rate):
            send_reading(
                "respiratory_rate",
                float(respiratory_rate),
                PATIENT_ID,
            )

        time.sleep(1 / SPEED_MULTIPLIER)


if __name__ == "__main__":
    replay_bidmc_data()
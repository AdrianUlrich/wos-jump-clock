from importlib.resources import files

import pandas as pd
import re

from src import time_conversions
from src.data.constants import *
from src.data.constants import POSSIBLE_BUILDINGS

REQUIRED_COLUMNS = [
    COLUMN_BUILDING, COLUMN_LEVEL, COLUMN_MEAT, COLUMN_WOOD, COLUMN_COAL, COLUMN_IRON, COLUMN_CRYSTAL, COLUMN_RFC,
    COLUMN_DURATION, COLUMN_SVS, COLUMN_MINUTES
]
DURATION_PATTERN = re.compile(r'^(\d+d )?(\d+h )?(\d+m)?$')


# Function to validate duration format
def validate_duration(duration):
    return bool(DURATION_PATTERN.match(duration))


def main():
    # Load the data
    data = pd.read_csv(str(files('src').joinpath('data/data.csv')))
    
    # Check if all required columns are present
    missing_columns = [col for col in REQUIRED_COLUMNS if col not in data.columns]
    if missing_columns:
        print(f"Missing columns: {', '.join(missing_columns)}")
    else:
        print("All required columns are present.")
    
    # Validate the duration format for each row
    invalid_durations = data[~data[COLUMN_DURATION].apply(validate_duration)]
    if not invalid_durations.empty:
        print("Rows with invalid duration format:")
        print(invalid_durations)
    else:
        print("All durations are in the correct format.")
    
    # Check that the duration in minutes is correct
    calculated_minutes = data[COLUMN_DURATION].apply(time_conversions.to_minutes)
    if not data[COLUMN_MINUTES].equals(calculated_minutes):
        print("Duration in minutes is incorrect.")
    else:
        print("Duration in minutes is correct.")
        
    # Check that the building names are correct
    invalid_buildings = data[~data[COLUMN_BUILDING].isin(POSSIBLE_BUILDINGS)]
    if not invalid_buildings.empty:
        print("Rows with invalid building names:")
        print(invalid_buildings)
    else:
        print("All building names are correct.")


if __name__ == '__main__':
    main()

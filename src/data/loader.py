"""Load and inspect household energy data from OPSD."""

import pandas as pd

HOUSEHOLD_DATA_URL = (
    "https://data.open-power-system-data.org/"
    "household_data/2020-04-15/"
    "household_data_15min_singleindex.csv"
)

TIMESTAMP_COLUMNS = [
    "utc_timestamp",
    "cet_cest_timestamp",
]

METADATA_COLUMNS = [
    *TIMESTAMP_COLUMNS,
    "interpolated",
]

SAMPLE_SIZE = 1_000


def load_household_data(
        nrows: int | None = SAMPLE_SIZE,
) -> pd.DataFrame:
    """Load household energy data from OPSD.

    Args:
        nrows: Number of rows to load. Use None to load the full dataset.

    Returns:
        A DataFrame containing timestamps and energy measurements.

    Raises:
        ValueError: If the expected UTC timestamp column is missing.
        pd.errors.ParserError: If the CSV cannot be parsed.
        OSError: If a local file operation fails.
    """
    dataframe = pd.read_csv(HOUSEHOLD_DATA_URL, nrows=nrows)

    if "utc_timestamp" not in dataframe.columns:
        raise ValueError(
            "The OPSD dataset does not contain 'utc_timestamp'."
        )

    dataframe["utc_timestamp"] = pd.to_datetime(
        dataframe["utc_timestamp"],
        utc=True,
        errors="coerce",
    )

    return dataframe


def get_measurement_columns(dataframe: pd.DataFrame) -> list[str]:
    """Return columns that contain energy measurements."""
    return [
        column
        for column in dataframe.columns
        if column not in METADATA_COLUMNS
    ]


def print_data_summary(dataframe: pd.DataFrame) -> None:
    """Print a summary of the loaded energy dataset."""
    measurement_columns = get_measurement_columns(dataframe)

    print("\nDataset shape:", dataframe.shape)
    print("\nColumn names:")
    print(dataframe.columns.tolist())

    print("\nFirst five rows:")
    print(dataframe.head().to_string(index=False))

    print("\nSummary statistics:")
    print(dataframe[measurement_columns].describe().to_string())

    print("\nColumns with the most missing values:")
    print(
        dataframe.isna()
        .sum()
        .sort_values(ascending=False)
        .head(10)
        .to_string()
    )

    print("\nFirst timestamp:", dataframe["utc_timestamp"].min())
    print("Last timestamp:", dataframe["utc_timestamp"].max())

    rows_with_data = dataframe.loc[
        dataframe[measurement_columns].notna().any(axis=1)
    ]

    print("\nFirst rows containing measurements:")
    if rows_with_data.empty:
        print("No measurement values were found in this sample.")
    else:
        columns_to_display = [
            "utc_timestamp",
            *measurement_columns[:5],
        ]
        print(
            rows_with_data[columns_to_display]
            .head(10)
            .to_string(index=False)
        )


if __name__ == "__main__":
    try:
        household_dataframe = load_household_data()
        print_data_summary(household_dataframe)
    except (ValueError, OSError, pd.errors.ParserError) as error:
        print(f"Error loading or inspecting the dataset: {error}")
    except Exception as error:
        print(f"Unexpected error: {error}")
        raise

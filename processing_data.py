import pandas as pd
import numpy as np


def __rename_competition(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "Competition": "competition",
            "Category": "category",
            "Clubs": "clubs",
            "Total:\nP": "MP",
            "W": "Win",
            "D": "Draw",
            "L": "Loses",
            "GF|⌀": "GF",
            "GA|⌀": "GA",
            "G|⌀": "G",
            "ΔG|⌀": "GD",
            "⌀ Rating": "Rating",
            "StdDev\nin %": "StdDev",
        },
        inplace=False,
    )

    return df


def __split_competition_avg(df: pd.DataFrame) -> pd.DataFrame:
    df["GF_avg"] = df["GF"].str.partition("|")[2].str.strip()
    df["GF"] = df["GF"].str.partition("|")[0].str.strip()
    df["GA_avg"] = df["GA"].str.partition("|")[2].str.strip()
    df["GA"] = df["GA"].str.partition("|")[0].str.strip()
    df["G_avg"] = df["G"].str.partition("|")[2].str.strip()
    df["G"] = df["G"].str.partition("|")[0].str.strip()
    df["GD_avg"] = df["GD"].str.partition("|")[2].str.strip()
    df["GD"] = df["GD"].str.partition("|")[0].str.strip()

    return df


def transform_competition_data(columns, rows, country: str, season: str):
    df = pd.DataFrame(rows, columns=columns)
    df = __rename_competition(df)
    df = __split_competition_avg(df)
    df = df.replace("", None)
    df["country"] = country
    df["season"] = season.partition("-")[0]

    return df


# ----------------------------------------------------------------------------------------------#
def __rename_raking_col(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "#": "Nr",
            "Club": "team",
            "Form (last 6)": "form1",
            "Rating": "rating",
            "Record:\nSeason": "season_record",
            "All time": "all_time",
            "+/-:\n1M": "month_dff",
            "1Y": "year_diff",
            "Season-to-date +/-:\nTotal": "total",
        },
        inplace=False,
    )
    col_to_changes = {
        3: "form2",
        4: "form3",
        5: "form4",
        6: "form5",
        7: "form6",
    }
    for index, new_name in col_to_changes.items():
        df.columns.values[index] = new_name

    return df


def transform_raking_data(columns, rows, country: str) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=columns)
    df = __rename_raking_col(df)
    df = df.replace("", None)
    df["country"] = country

    return df


# ----------------------------------------------------------------------------------------------------#
def __rename_matches_col(df: pd.DataFrame) -> pd.DataFrame:
    df = df.rename(
        columns={
            "Date": "date",
            "Competition": "competition",
            "Home": "home_team",
            "Result": "result",
            "Probabilities:\nH": "home_prb",
            "D": "draw_prb",
            "A": "away_prb",
            "Away": "away_team",
        },
        inplace=False,
    )

    df.columns.values[3] = "home_elo_changed"
    df.columns.values[9] = "away_elo_changed"

    return df


def __replace_empty_with_none(value):
    return None if value == "" else value


def __check_info(value):
    return None if value == "Info" else value


def __split_goals(df: pd.DataFrame) -> pd.DataFrame:
    df["result"] = df["result"].apply(lambda x: __check_info(x))
    df["home_goals"] = df["result"].str.partition("-")[0].str.strip()
    df["away_goals"] = df["result"].str.partition("-")[2].str.strip()

    return df


def __add_match_result(df: pd.DataFrame) -> pd.DataFrame:
    df["match_result"] = np.where(
        df["result"].isna(),
        None,
        np.where(
            df["home_goals"] > df["away_goals"],
            "home_win",
            np.where(df["home_goals"] < df["away_goals"], "away_win", "draw"),
        ),
    )

    return df


def transform_matches_data(columns, rows, country: str) -> pd.DataFrame:
    df = pd.DataFrame(rows, columns=columns)
    df["Date"] = df["Date"].apply(lambda x: __replace_empty_with_none(x))
    df["Date"] = df["Date"].ffill()
    df = df.drop(columns=df.columns[df.columns == ""])
    df = __rename_matches_col(df)
    df = __split_goals(df)
    df = __add_match_result(df)
    df = df.replace("", None)
    df["country"] = country

    return df

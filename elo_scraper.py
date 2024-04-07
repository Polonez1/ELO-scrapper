from playwright.sync_api import Playwright, sync_playwright, expect

import processing_data
import json
import pandas as pd
import function_log as log
import sql_integration as SQL
import time


class EloParser:
    def __init__(self, current_season: str, history_seasons: dict):
        self.sql_engine = SQL.EloDataLoad()

        self.url: str = "http://elofootball.com/"
        self.country_hrefs: dict = {}
        self.season_hrefs: dict = {}
        self.competition_data: dict = {}
        self.ranking_data: dict = {}
        self.matches_data: dict = {}
        self.history_seasons: dict = history_seasons
        self.current_season: str = current_season
        self.output_path = "./output/"

    def __get_season_string(self) -> str:
        season = (
            self.page.get_by_role("heading", name="Selected season:")
            .inner_text()
            .partition("Selected season:")[2]
            .strip()
        )
        return season

    def __append_data(
        self, df: pd.DataFrame, append_dict: dict, country: str, season: str
    ):
        json_data = df.to_json(orient="records", indent=1)
        json_data = json.loads(json_data)
        append_dict[country] = {}
        append_dict[country][season] = {}
        append_dict[country][season] = json_data

    def __season_hrefs_collector(self, country: str):
        dropdown_menus = self.page.query_selector_all(".dropdown-menu")
        country_hrefs_box = dropdown_menus[1]
        self.season_hrefs[country] = {}
        if country_hrefs_box:
            hrefs_element = country_hrefs_box.query_selector_all("a")
            for i in hrefs_element:
                season = i.inner_text()
                href = i.get_attribute("href")
                # print(country, season, href)
                self.season_hrefs[country][season] = {}
                self.season_hrefs[country][season] = self.url + href

    def __collect_country_hrefs(self):
        dropdown_menus = self.page.query_selector_all(".dropdown-menu")
        country_hrefs_box = dropdown_menus[0]
        if country_hrefs_box:
            hrefs_element = country_hrefs_box.query_selector_all("a")
            for i in hrefs_element:
                country = i.inner_text()
                href = i.get_attribute("href")
                if country == "UEFA Competitions":
                    pass
                else:
                    self.country_hrefs[country] = href

    # ------------------------------------------------------------------------------------------------------#
    def __get_table_by_nr(self, table_index: int) -> list:
        """find table by index and return table components

        Args:
            table_index (int): table place

        Returns:
            list: headers, rows
        """
        table_element = self.page.query_selector_all(".sortable.fixed.primary")
        table = table_element[table_index]
        table_data = table.evaluate(
            "(table) => { return { headers: Array.from(table.tHead.rows[0].cells, cell => cell.innerText.trim()), rows: Array.from(table.tBodies[0].rows, row => Array.from(row.cells, cell => cell.innerText.trim())) }; }"
        )
        headers = table_data.get("headers")
        rows = table_data.get("rows")

        return headers, rows

    def __collect_competition_data(self, season: str, country: str) -> None:
        headers, rows = self.__get_table_by_nr(table_index=0)

        df = processing_data.transform_competition_data(
            rows=rows, columns=headers, country=country, season=season
        )
        self.sql_engine.load_data(df=df, table_name="elo_competition", truncate=False)

        self.__append_data(
            df=df, append_dict=self.competition_data, season=season, country=country
        )

        with open(
            f"{self.output_path}competition_data.json", "w", encoding="utf-8"
        ) as json_file:
            json.dump(self.competition_data, json_file, ensure_ascii=False, indent=2)

    def __collect_raking_data(self, season: str, country: str) -> None:
        for i in range(0, 4):
            col, rows = self.__get_table_by_nr(table_index=i)
            if "Form (last 6)" in col:
                headers, rows = self.__get_table_by_nr(table_index=i)
                df = processing_data.transform_raking_data(
                    columns=headers, rows=rows, country=country
                )
                self.sql_engine.load_data(
                    df=df, table_name="elo_raking", truncate=False
                )

                self.__append_data(
                    df=df, append_dict=self.ranking_data, season=season, country=country
                )
                with open(
                    f"{self.output_path}raking_data.json", "w", encoding="utf-8"
                ) as json_file:
                    json.dump(
                        self.ranking_data, json_file, ensure_ascii=False, indent=2
                    )

                break
            else:
                headers = "No data"
                rows = "No data"
                # self.__append_data(
                #    df=df, append_dict=self.ranking_data, season=season, country=country
                # )

    def __collect_matches_data(self, season: str, country: str) -> None:
        for i in range(0, 5):
            col, rows = self.__get_table_by_nr(table_index=i)
            if "Away" in col:
                headers, rows = self.__get_table_by_nr(table_index=i)
                df = processing_data.transform_matches_data(
                    columns=headers, rows=rows, country=country
                )
                self.sql_engine.load_data(
                    df=df, table_name="elo_matches", truncate=False
                )
                self.__append_data(
                    df=df, append_dict=self.ranking_data, season=season, country=country
                )

                with open(
                    f"{self.output_path}matches_data.json", "w", encoding="utf-8"
                ) as json_file:
                    json.dump(
                        self.matches_data, json_file, ensure_ascii=False, indent=2
                    )

                break
            else:
                headers = "No data"
                rows = "No data"
                # self.__append_data(
                #    df=df, append_dict=self.ranking_data, season=season, country=country
                # )

    def __collect_elo_data(self, hrefs: dict):
        # self.sql_engine.truncate_tables()
        for i in hrefs.items():
            country = i[0]
            print(country)
            href = i[1]
            url = self.url + href
            self.page.goto(url, timeout=60000)
            season = self.__get_season_string()
            self.__season_hrefs_collector(country=country)
            self.__collect_competition_data(season=season, country=country)
            self.__collect_raking_data(season=season, country=country)
            self.__collect_matches_data(season=season, country=country)

    def __collect_elo_history_data(self, hrefs: dict):
        for country in hrefs:
            for href in hrefs[country]:
                url = self.url + href
                self.page.goto(url, timeout=60000)
                season = self.__get_season_string()
                self.__season_hrefs_collector(country=country)
                self.__collect_competition_data(season=season, country=country)
                print(country, season, url)
            # self.__collect_raking_data(season=season, country=country)
            # self.__collect_matches_data(season=season, country=country)

    @log.elapsed_time
    def parse(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            self.context = browser.new_context()
            self.page = self.context.new_page()
            self.page.goto(self.url, timeout=60000)
            self.__collect_country_hrefs()
            self.__collect_elo_data(hrefs=self.country_hrefs)

    @log.elapsed_time
    def parse_history(self):
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            self.context = browser.new_context()
            self.page = self.context.new_page()
            self.page.goto(self.url, timeout=60000)
            self.__collect_country_hrefs()
            history_hrefs_dict = {}
            for href_key in self.country_hrefs:
                for s in self.history_seasons.items():
                    season_param = s[1]
                    country = href_key
                    href: str = self.country_hrefs[href_key]
                    href_new = href.replace(self.current_season, season_param)
                    if country not in history_hrefs_dict:
                        history_hrefs_dict[country] = [href_new]
                    else:
                        history_hrefs_dict[country].append(href_new)

            self.__collect_elo_history_data(hrefs=history_hrefs_dict)
            # test


if "__main__" == __name__:
    elo = EloParser(
        current_season="2023-2024",
        history_seasons={
            "2022": "2022-2023",
            "2021": "2021-2022",
            "2020": "2020-2021",
        },
    )
    elo.parse_history()
    # print(elo.season_hrefs)


# powershell -ExecutionPolicy Bypass -File C:\iLegion\football_elo_scraper\venv\Scripts\Activate.ps1
# Set-ExecutionPolicy Bypass -Scope Process
# .\venv\Scripts\activate

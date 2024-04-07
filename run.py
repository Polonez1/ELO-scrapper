import click
import elo_scraper


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
def elo_parse():
    scrap = elo_scraper.EloParser()
    scrap.parse()


if __name__ == "__main__":
    elo_parse()

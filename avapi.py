import click
import pandas as pd
import numpy as np
import json
from os import path
from datetime import date
from urllib.request import urlopen

AVAPI_KEY_JSON = "avapi_key.json"
BASE = "https://www.alphavantage.co/query?function={}&symbol={}&apikey={}&datatype=csv"

STOCK_FUNC_LIST = {
    'intraday': "TIME_SERIES_INTRADAY",
    'daily':    "TIME_SERIES_DAILY",
    'weekly':   "TIME_SERIES_WEEKLY",
    'monthly':  "TIME_SERIES_MONTHLY",
    'global':   "GLOBAL_QUOTE"
}

CRYPTO_FUNC_LIST = {
    'rating':   "CRYPTO_RATING",
    'daily':    "DIGITAL_CURRENCY_DAILY",
    'weekly':   "DIGITAL_CURRENCY_WEEKLY",
    'monthly':  "DIGITAL_CURRENCY_MONTHLY"
}

INTERVAL_LIST = ["1min", "5min", "15min", "30min", "60min"]


class avapiJsonFileNotFoundError(Exception):
    """ Raised when an avapi_key.json file is not found"""
    pass


class avapiJsonEmptyError(Exception):
    """
    Raised when the 'avapi_key.json file is empty
    or there is no data within the 'avapi_key'
    """
    pass


class invalidFunctionError(Exception):
    """ Raised when an incorrect function argument is provided"""
    pass


class invalidIntervalError(Exception):
    """ Raised when an incorrect interval is provided to the 'intraday' argument"""
    pass


def read_key():
    """Try to read 'avapi_key.json' and return the 'key' field."""
    try:
        if (path.exists(AVAPI_KEY_JSON)):
            with open(AVAPI_KEY_JSON, 'r') as f:
                j = json.load(f)
                if not 'key' in j or len(j['key']) == 0:
                    raise avapiJsonEmptyError
                else:
                    return j['key']

        else:
            raise avapiJsonFileNotFoundError

    except avapiJsonFileNotFoundError:
        print("Error: 'avapi_key.json' file found. Try running 'setkey'.")
    except avapiJsonEmptyError:
        print(
            "Error: 'avapi_key.json' does not contain an API Key. Try running 'setkey'."
        )


def get_pandas_df(url, n):
    if n != 0:
        return pd.read_csv(url).head(n)
    else:
        return pd.read_csv(url)


@click.group(invoke_without_command=True)  # Allow users to call w/o command
@click.pass_context
@click.option('--verbose',
              '-v',
              is_flag=True,
              help="Increase output verbosity level.")
def main(ctx, verbose):
    """
    A command-line interface written in Python for the Alpha Vantage API.

    Author: Mac Fox
    """
    if ctx.invoked_subcommand is None:  # No command was specified
        click.echo("No command specified, try using '--help'")
    ctx.obj['VERBOSE'] = verbose


@main.command('setkey')
@click.option('--k',
              prompt="Alpha Vantage API Key",
              help="Alpha Vantage API Key")
def setkey(k):
    """Save an Alpha Vantage API key to 'avapi_key.json'."""
    avapi_key = {"key": k}
    with open("avapi_key.json", 'w') as f:
        json.dump(avapi_key, f)


@main.command('exrate')
@click.argument('from_currency')
@click.argument('to_currency')
@click.option('--save', is_flag=True, help="Save data to .csv file.")
def exrate(from_currency, to_currency, save):
    """
    Returns the realtime exchange rate for any pair of digital currency 
    (e.g., BTC) or physical currency (e.g., USD).
    """
    url = ("https://www.alphavantage.co/query?"
           "function=CURRENCY_EXCHANGE_RATE"
           f"&from_currency={from_currency}"
           f"&to_currency={to_currency}"
           f"&apikey={read_key()}")

    data = json.loads(urlopen(url).read())
    df = pd.json_normalize(data['Realtime Currency Exchange Rate'])
    click.echo(df.to_string(index=False))

    if save:
        filename = f"{date.today()}_exrate_{f}_{t}.csv"
        df.to_csv(filename, index=False)


@main.command('stock')
@click.argument('function')
@click.option('-s', '-symbol', prompt="Symbol", help="TSLA AAPL GME...")
@click.option('-i', '-interval', default="30min", help="1min 5min 15min 30min or 60min. Default = 30min")
@click.option('-n', '-last_n', default=0, help="Only get last_n rows of data")
@click.option('--save', is_flag=True, help="Save data to .csv file.")
def stock(function, s, i, n, save):
    """
    Get a specific time series function for a stock of interest.

    FUNCTION: intraday daily weekly monthly global

    Example: python3 avapi.py stock intraday -s'TSLA' -i'15min'

    Example: python3 avapi.py stock daily -s'TSLA'

    Example: python3 avapi.py stock daily -s'TSLA' -n30
    """
    try:
        if function not in STOCK_FUNC_LIST:  # Make sure function argument is valid
            raise invalidFunctionError
        else:
            if function == "rating":
                url = BASE.format(
                    STOCK_FUNC_LIST["intraday"], s, read_key()) + f"&interval={i}"
                df = get_pandas_df(url, n)
                click.echo(df)

            else:  # Construct query and get data
                url = BASE.format(
                    STOCK_FUNC_LIST[function], s, read_key())
                df = get_pandas_df(url, n)
                click.echo(df)

            if save:
                filename = f"{date.today()}_{function}_{s}_.csv"
                df.to_csv(filename, index=False)

    except invalidFunctionError:
        click.echo(
            "Error: Invalid function argument:'{}'".format(function))
    except invalidIntervalError:
        click.echo("Error: Invalid interval option:'{}'".format(i))


@main.command('crypto')
@click.argument('function')
@click.option('-s', '-symbol', prompt="Symbol", help="TSLA AAPL GME...")
@click.option('-n', '-last_n', default=0, help="Only get last_n rows of data")
@click.option('--save', is_flag=True, help="Save data to .csv file.")
def crypto(function, s, n, save):
    """
    Get a specific time series function for a crypto currency of interest.
    """
    try:
        if function not in CRYPTO_FUNC_LIST:  # Make sure function argument is valid
            raise invalidFunctionError
        if function == 'rating':
            url = ("https://www.alphavantage.co/query?"
                   "function=CRYPTO_RATING"
                   f"&symbol={s}&apikey={read_key()}")
            data = json.loads(urlopen(url).read())
            df = pd.json_normalize(data["Crypto Rating (FCAS)"])
            click.echo(df.to_string(index=False))
        else:
            url = ("https://www.alphavantage.co/query?"
                   f"function={CRYPTO_FUNC_LIST[function]}"
                   f"&symbol={s}&market=USD&apikey={read_key()}"
                   "&datatype=csv")
            df = get_pandas_df(url, n)
            click.echo(df)

        if save:
            filename = f"{date.today()}_{function}_{s}_.csv"
            df.to_csv(filename, index=False)

    except invalidFunctionError:
        click.echo(
            "Error: Invalid function argument for 'avapi get':'{}'".format(function))
    except invalidIntervalError:
        click.echo("Error: Invalid interval option:'{}'".format(i))


if __name__ == "__main__":
    # pylint: disable=unexpected-keyword-arg
    # pylint: disable=no-value-for-parameter
    main(obj={})

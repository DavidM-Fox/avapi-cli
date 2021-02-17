import click
import pandas as pd
import numpy as np
import json
from os import path
from urllib.request import urlopen
from collections import defaultdict

AVAPI_KEY_JSON = "avapi_key.json"
URL_BASE = "https://www.alphavantage.co/query?function={}&symbol={}&apikey={}"

URL_FUNC = [
    "TIME_SERIES_INTRADAY", "TIME_SERIES_DAILY", "TIME_SERIES_WEEKLY",
    "TIME_SERIES_MONTHLY", "GLOBAL_QUOTE"
]

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


class intervalStringError(Exception):
    """ Raised when an incorrect interval string is provided to 'intraday'"""
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


def dataframe_from_av_data(url, field, object_hook=None):
    """Returns a pandas data frame from Alpha Vantage JSON"""
    with urlopen(url) as resource:
        data = json.load(resource, object_hook=object_hook)[field]
        val = {} 
        time_data = []
        open_data = []
        high_data =[]
        low_data = []
        close_data = []
        volume_data = []
        
        for timestamp, values in data.items():
            time_data.append(timestamp)
            open_data.append(list(values.values())[0])
            high_data.append(list(values.values())[1])
            low_data.append(list(values.values())[2])
            close_data.append(list(values.values())[3])
            volume_data.append(list(values.values())[4])
        val['timestamp'] = time_data
        val['open'] = open_data
        val['high'] = high_data
        val['low'] = low_data
        val['close'] = close_data
        val['volume'] = volume_data
        df = pd.DataFrame(val)
        return df

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
    if ctx.invoked_subcommand is None:
        # No command was specified
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


@main.command('intraday')
@click.option('-s', prompt="Symbol", help="Symbol: 'TSLA' 'AAPL'...")
@click.option('-i',
              prompt="Interval",
              help="Data interval: '1min' '5min' '15min' '30min' or '60min'.")
@click.option('--save', is_flag=True, help="Save data to .csv file.")
def intraday(s, i, save):
    """Get intraday data for a symbol of interest.
    
    Example: python3 avapi.py intraday -s'TSLA' -i'15min'
    """
    try:
        if i not in INTERVAL_LIST:
            raise intervalStringError
        else:
            api_key = read_key()
            url = URL_BASE.format(URL_FUNC[0], s,
                                  api_key) + "&interval={}".format(i)
            field = "Time Series ({})".format(i)
            filename = "intraday_{}_{}".format(i, s)
            df = dataframe_from_av_data(url, field)
            print(df)
    except intervalStringError:
        click.echo("Error: Incorrect interval provided '{}'".format(i))


if __name__ == "__main__":
    # pylint: disable=unexpected-keyword-arg
    # pylint: disable=no-value-for-parameter
    main(obj={})

# Copyright (c) 2014-2019, Tibor Kiss <tibor.kiss@gmail.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


"""Kelly Criterion - (c) 2014-2019, Tibor Kiss <tibor.kiss@gmail.com>

Usage:
  python kelly_criterion.py [-h] [--risk-free-rate RATE] start_date end_date security [security ...]

Options:
  --risk-free-rate RATE  Annualized percentage of the Risk Free Rate (default: 0.04)
"""

import sys
import os
from datetime import datetime, date, timedelta
from typing import Set, Dict
import logging
import argparse

from pandas import DataFrame
from numpy.linalg import inv
from polygon import RESTClient
from dotenv import load_dotenv

log = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()


def calc_kelly_leverages(securities: Set[str],
                         start_date: date,
                         end_date: date,
                         risk_free_rate: float = 0.04) -> Dict[str, float]:
    """Calculates the optimal leverages for the given securities and
    time frame. Returns a list of (security, leverage) tuple with the
    calculate optimal leverages.

    Note: risk_free_rate is annualized
    """
    f = {}
    ret = {}
    excess_return = {}
    
    # Get API key from environment variables
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable not set. Please create a .env file with your Polygon API key.")
    
    # Create Polygon REST client
    client = RESTClient(api_key)

    # Download the historical prices and calculate the
    # excess return (return of security - risk free rate) for each security.
    for symbol in securities:
        try:
            # Polygon requires a time delta, so we add one day to end_date to include it
            aggs = client.get_aggs(
                ticker=symbol,
                multiplier=1,
                timespan="day",
                from_=start_date.strftime("%Y-%m-%d"),
                to=(end_date + timedelta(days=1)).strftime("%Y-%m-%d")
            )
            
            # Convert to DataFrame
            hist_prices = DataFrame([{
                'date': datetime.fromtimestamp(agg.timestamp/1000).date(),
                'close': agg.close,
                'volume': agg.volume,
                'open': agg.open,
                'high': agg.high,
                'low': agg.low
            } for agg in aggs])
            
            # Set date as index
            if not hist_prices.empty:
                hist_prices.set_index('date', inplace=True)
            else:
                raise ValueError(f"No data returned for {symbol}")
                
        except Exception as e:
            raise ValueError(f'Unable to download data for {symbol}. '
                             f'Reason: {str(e)}')

        f[symbol] = hist_prices

        ret[symbol] = hist_prices['close'].pct_change()
        # risk_free_rate is annualized
        excess_return[symbol] = (ret[symbol] - (risk_free_rate / 252))

    # Create a new DataFrame based on the Excess Returns.
    df = DataFrame(excess_return).dropna()

    # Calculate the CoVariance and Mean of the DataFrame
    C = 252 * df.cov()
    M = 252 * df.mean()

    # Calculate the Kelly-Optimal Leverages using Matrix Multiplication
    F = inv(C).dot(M)

    # Return a list of (security, leverage) tuple
    return {security: leverage
            for security, leverage in zip(df.columns.values.tolist(), F)}


def main():
    """Entry point of Kelly Criterion calculation."""
    logging.basicConfig(level=logging.INFO)

    log.info("Kelly Criterion calculation")
    
    # Get default dates
    today = date.today()
    five_years_ago = today.replace(year=today.year - 5)
    
    # Replace docopt with argparse
    parser = argparse.ArgumentParser(description="Kelly Criterion calculation")
    parser.add_argument('--risk-free-rate', type=float, default=0.04,
                        help='Annualized percentage of the Risk Free Rate (default: 0.04)')
    parser.add_argument('--start-date', default=five_years_ago.strftime("%Y-%m-%d"),
                        help=f'Start date in YYYY-MM-DD format (default: {five_years_ago.strftime("%Y-%m-%d")})')
    parser.add_argument('--end-date', default=today.strftime("%Y-%m-%d"),
                        help=f'End date in YYYY-MM-DD format (default: {today.strftime("%Y-%m-%d")})')
    parser.add_argument('securities', nargs='+', help='List of securities to analyze')
    
    args = parser.parse_args()

    # Parse risk-free-rate
    risk_free_rate = args.risk_free_rate

    # Verify risk-free-rate
    if not 0 <= risk_free_rate <= 1.0:
        log.error(f"risk-free-rate is not in between 0 and 1: "
                  f"{risk_free_rate:%.2f}")
        sys.exit(-1)

    # Parse start and end dates
    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    except ValueError:
        log.error(f"Error parsing start-date: {args.start_date}")
        sys.exit(-1)

    try:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    except ValueError:
        log.error(f"Error parsing end-date: {args.end_date}")
        sys.exit(-1)

    log.info(
        f"Arguments: "
        f"risk-free-rate={risk_free_rate} "
        f"start-date={start_date} "
        f"end-date={end_date} "
        f"securities={args.securities}")

    # Calculate the Kelly Optimal leverages
    try:
        leverages = calc_kelly_leverages(
            args.securities, start_date, end_date, risk_free_rate)
    except ValueError as e:
        log.error(f"Error during Kelly calculation: {str(e)}")
        sys.exit(-1)

    # Print the results if calculation was successful
    if leverages:
        log.info("Leverages per security:")
        sum_leverage = 0
        positive_leverage = 0
        negative_leverage = 0
        
        for symbol, leverage in leverages.items():
            sum_leverage += leverage
            if leverage > 0:
                positive_leverage += leverage
            else:
                negative_leverage += abs(leverage)
            log.info(f"  {symbol}: {leverage:.2f}")

        log.info(f"Sum leverage: {sum_leverage}")
        log.info(f"Total exposure: {positive_leverage + negative_leverage:.2f} (Long: {positive_leverage:.2f}, Short: {negative_leverage:.2f})")


if __name__ == '__main__':
    main()

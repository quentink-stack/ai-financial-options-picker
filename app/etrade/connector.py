# connector.py

import requests
from requests_oauthlib import OAuth1
import pandas as pd
import configparser
import os

def get_options_chain(session, base_url, symbol="AAPL", expiry="2025-09-19"):
    """Get options chain data using an authenticated session."""
    url = f"{base_url}/v1/market/optionchains"
    params = {
        "symbol": symbol,
        "expiryDate": expiry,
        "includeWeekly": "true",
        "skipAdjusted": "true"
    }
    
    r = session.get(url, params=params)
    if r.status_code != 200:
        raise Exception(f"Error: {r.status_code}, {r.text}")
    
    data = r.json()

    # Flatten into DataFrame
    options = []
    chain_response = data.get("OptionChainResponse", {})
    for chain in chain_response.get("OptionPair", []):
        call = chain.get("Call", {})
        put = chain.get("Put", {})
        options.append({
            "strike": chain.get("StrikePrice"),
            "call_bid": call.get("Bid"),
            "call_ask": call.get("Ask"),
            "call_iv": call.get("ImpliedVolatility"),
            "call_open_interest": call.get("OpenInterest"),
            "put_bid": put.get("Bid"),
            "put_ask": put.get("Ask"),
            "put_iv": put.get("ImpliedVolatility"),
            "put_open_interest": put.get("OpenInterest")
        })
    return pd.DataFrame(options)
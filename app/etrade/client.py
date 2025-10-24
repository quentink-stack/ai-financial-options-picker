# client.py

import webbrowser
import json
import configparser
import os
from rauth import OAuth1Service

# Updated paths to look in the etrade directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(os.path.dirname(BASE_DIR), "config.ini")  # config.ini stays in app/
TOKENS_FILE = os.path.join(BASE_DIR, "tokens.json")  # moved to etrade/tokens.json

def get_etrade_session(env="sandbox"):
    """
    Authenticate with E*TRADE and return an OAuth1 session + base_url.
    Saves access tokens to tokens.json for reuse.
    """

    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    consumer_key = config["DEFAULT"]["CONSUMER_KEY"]
    consumer_secret = config["DEFAULT"]["CONSUMER_SECRET"]

    if env == "sandbox":
        base_url = config["DEFAULT"]["SANDBOX_BASE_URL"]
        request_token_url = "https://apisb.etrade.com/oauth/request_token"
        access_token_url = "https://apisb.etrade.com/oauth/access_token"
    elif env == "prod":
        base_url = config["DEFAULT"]["PROD_BASE_URL"]
        request_token_url = "https://api.etrade.com/oauth/request_token"
        access_token_url = "https://api.etrade.com/oauth/access_token"
    else:
        raise ValueError("env must be 'sandbox' or 'prod'")

    # Check if we already have saved tokens
    try:
        with open(TOKENS_FILE, "r") as f:
            tokens = json.load(f)
            print("✅ Loaded saved tokens from file")
            from rauth import OAuth1Session
            session = OAuth1Session(
                consumer_key,
                consumer_secret,
                tokens["access_token"],
                tokens["access_secret"]
            )
            return session, base_url
    except FileNotFoundError:
        pass

    # Create OAuth1Service
    etrade = OAuth1Service(
        name="etrade",
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        request_token_url=request_token_url,
        access_token_url=access_token_url,
        authorize_url="https://us.etrade.com/e/t/etws/authorize?key={}&token={}",
        base_url=base_url
    )

    # Step 1: Get request token
    request_token, request_token_secret = etrade.get_request_token(
        params={"oauth_callback": "oob"}
    )

    # Step 2: Authorize
    authorize_url = etrade.authorize_url.format(consumer_key, request_token)
    print("➡️ Please go to this URL to authorize access:")
    print(authorize_url)
    webbrowser.open(authorize_url)

    verifier = input("Enter the PIN provided by E*TRADE: ")

    # Step 3: Get access token
    session = etrade.get_auth_session(
        request_token,
        request_token_secret,
        params={"oauth_verifier": verifier}
    )

    # Save tokens for reuse
    tokens = {
        "access_token": session.access_token,
        "access_secret": session.access_token_secret
    }
    with open(TOKENS_FILE, "w") as f:
        json.dump(tokens, f, indent=2)

    print("🎉 Auth complete, tokens saved to", TOKENS_FILE)
    return session, base_url


if __name__ == "__main__":
    s, base_url = get_etrade_session("sandbox")
    # Example: get quotes for AAPL
    r = s.get(base_url + "/v1/market/quote/AAPL.json")
    print(r.json())
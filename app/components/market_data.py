"""Market data UI components.

This module provides Streamlit UI components for displaying and interacting with market data.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import etrade.client as etrade_client

def render_market_search(session, base_url):
    """Render the market search UI section.
    
    Args:
        session: An authenticated E*TRADE session
        base_url: The base API URL for E*TRADE calls
    """
    st.markdown("## 🔍 Market Search")

    # Search box
    symbol = st.text_input(
        "Enter a stock symbol:",
        help="Enter a stock symbol to search for option chains."
    ).upper()

    # Only show the rest if we have a symbol
    if not symbol:
        return None
        
    try:
        # Search for the symbol
        results = etrade_client.lookup_product(session, base_url, symbol)
        
        if not results:
            st.warning(f"No results found for '{symbol}'")
            return None
            
        # Format the results into a DataFrame for display
        df = pd.DataFrame(results)
        
        # Display results in an expander
        with st.expander("Search Results", expanded=True):
            st.dataframe(
                df,
                column_config={
                    "All": "All Exchanges",
                    "symbolDescription": "Description"
                }
            )
            
        return symbol
            
    except Exception as e:
        st.error(f"Error searching for symbol: {e}")
        return None

def render_option_chain(session, base_url, symbol):
    """Render the options chain UI section.
    
    Args:
        session: An authenticated E*TRADE session
        base_url: The base API URL for E*TRADE calls
        symbol: The stock symbol to get options for
    """
    if not symbol:
        return

    st.markdown("## 📊 Options Chain")
    
    try:
        # Get expiry dates
        dates = etrade_client.get_option_expire_dates(session, base_url, symbol)
        if not dates:
            st.warning(f"No options available for {symbol}")
            return

        # Format dates for selection
        date_choices = {
            datetime.strptime(d, "%Y%m%d").strftime("%Y-%m-%d"): d 
            for d in dates
        }
        selected_date = st.selectbox(
            "Select expiration date:",
            options=list(date_choices.keys()),
            format_func=lambda x: x,
            help="Choose an expiration date to view available options."
        )
        
        if not selected_date:
            return
            
        expiry = date_choices[selected_date]
        
        # Get chain
        chain = etrade_client.get_option_chains(
            session, base_url, symbol, expiry
        )
        
        if not chain:
            st.warning(f"No options data available for {symbol} expiring {selected_date}")
            return
            
        # Create DataFrames for puts and calls
        calls_df = pd.DataFrame([
            {**opt, 'type': 'CALL'}
            for opt in chain.get('CALL', [])
        ])
        puts_df = pd.DataFrame([
            {**opt, 'type': 'PUT'} 
            for opt in chain.get('PUT', [])
        ])
        
        # Display chains
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Calls")
            if not calls_df.empty:
                st.dataframe(
                    calls_df,
                    column_config={
                        "symbol": None,  # Hide full option symbol
                        "type": None,    # Hide type since we know these are calls
                        "OptionCategory": None,  # Hide category
                        "strikePrice": st.column_config.NumberColumn(
                            "Strike",
                            help="Strike price of the option",
                            format="$%.2f"
                        ),
                        "bid": st.column_config.NumberColumn(
                            "Bid",
                            help="Current bid price",
                            format="$%.2f"
                        ),
                        "ask": st.column_config.NumberColumn(
                            "Ask", 
                            help="Current ask price",
                            format="$%.2f"
                        ),
                        "lastPrice": st.column_config.NumberColumn(
                            "Last",
                            help="Last traded price",
                            format="$%.2f"
                        ),
                    },
                    hide_index=True
                )
            else:
                st.info("No call options available")
                
        with col2:
            st.markdown("### Puts")
            if not puts_df.empty:
                st.dataframe(
                    puts_df,
                    column_config={
                        "symbol": None,  # Hide full option symbol
                        "type": None,    # Hide type since we know these are puts
                        "OptionCategory": None,  # Hide category
                        "strikePrice": st.column_config.NumberColumn(
                            "Strike",
                            help="Strike price of the option",
                            format="$%.2f"
                        ),
                        "bid": st.column_config.NumberColumn(
                            "Bid",
                            help="Current bid price",
                            format="$%.2f"
                        ),
                        "ask": st.column_config.NumberColumn(
                            "Ask",
                            help="Current ask price",
                            format="$%.2f"
                        ),
                        "lastPrice": st.column_config.NumberColumn(
                            "Last",
                            help="Last traded price",
                            format="$%.2f"
                        ),
                    },
                    hide_index=True
                )
            else:
                st.info("No put options available")

    except Exception as e:
        st.error(f"Error fetching options data: {e}")
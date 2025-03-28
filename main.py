import json
import requests
import time

API_KEY = ""
BASE_URL = "https://api.ataix.kz"

def get_request(endpoint):
    """Sends a GET request to the API and handles possible errors"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "accept": "application/json",
        "X-API-Key": API_KEY
    }
    try:
        response = requests.get(url, headers=headers, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("result", data)
    except requests.RequestException as e:
        print(f"API request error: {e}")
        return None

def post_request(endpoint, data):
    """Sends a POST request to the API"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "accept": "application/json",
        "X-API-Key": API_KEY,
        "Content-Type": "application/json"
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=20)
        response.raise_for_status()
        return response.json().get("result", response.json())
    except requests.RequestException as e:
        print(f"API request error: {e}")
        return None

def get_usdt_balance():
    """Retrieves the available USDT balance."""
    balance_data = get_request("/api/user/balances/USDT")
    if isinstance(balance_data, dict) and "available" in balance_data:
        return float(balance_data["available"])
    return None

def find_usdt_pairs():
    """Finds USDT trading pairs with a bid price ? 0.6"""
    symbols = get_request("/api/symbols")
    if not isinstance(symbols, list):
        print("Error: Unexpected API response format for /api/symbols")
        return None

    for pair in symbols:
        if isinstance(pair, dict) and pair.get("quote") == "USDT":
            try:
                bid_price = float(pair.get("bid", float("inf")))  # Try getting "bid" price
                if bid_price <= 0.6:
                    return pair["symbol"]
            except ValueError:
                continue
    return None

def get_highest_bid(symbol):
    """Finds the highest buy order price for the given trading pair."""
    symbols = get_request("/api/symbols")
    if not isinstance(symbols, list):
        print("Error: Unexpected response format for symbols")
        return None

    for pair in symbols:
        print(f"Checking pair: {pair}")  # Îòëàäêà: ñìîòðèì ñòðóêòóðó äàííûõ
        if pair.get("symbol") == symbol:
            bid_price = pair.get("bid") or pair.get("bestBid") or pair.get("highestBid")
            if bid_price:
                try:
                    return float(bid_price)
                except ValueError:
                    print(f"Error: Invalid bid price format for {symbol}")
                    return None

    print(f"Error: No bid price found for {symbol}")
    return None

def create_order(symbol, price, amount):
    """Creates a buy order for the specified symbol at the given price and amount."""
    payload = {
        "symbol": symbol,
        "side": "buy",
        "type": "limit",
        "price": round(price, 2), 
        "quantity": 1 
    }

    response = post_request("/api/orders", payload)

    print(f"Order response: {response}")  # Âûâîä îòâåòà API äëÿ ïðîâåðêè

    if response and "id" in response:
        return {"order_id": response["id"], "status": "NEW"}
    return None

def save_orders_to_file(orders, filename="orders.json"):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(orders, file, indent=4, ensure_ascii=False)
        print(f"Orders saved to {filename}")
    except Exception as e:
        print(f"Error saving orders to file: {e}")

def main():
    # Retrieve USDT balance
    usdt_balance = get_usdt_balance()
    if usdt_balance is None:
        print("Error: Failed to get USDT balance.")
        return

    print(f"Available balance: {usdt_balance:.6f} USDT")

    # Find a suitable trading pair
    symbol = find_usdt_pairs()
    if not symbol:
        print("No suitable trading pair found.")
        return

    print(f"Selected trading pair: {symbol}")

    # Get highest bid price
    highest_bid = get_highest_bid(symbol)
    if highest_bid is None:
        print(f"Error: Failed to get highest bid price for {symbol}")
        return

    print(f"Highest bid price: {highest_bid:.6f} USDT")

    # Îïðåäåëåíèå óðîâíåé öåí (-2%, -5%, -8%)
    price_levels = [
        highest_bid * 0.98,  # -2%
        highest_bid * 0.95,  # -5%
        highest_bid * 0.92   # -8%
    ]

    num_orders = 2
    amount_per_order = usdt_balance / (num_orders * highest_bid)  # Ðàâíîìåðíîå ðàñïðåäåëåíèå ñðåäñòâ

    orders = []

    for i, price in enumerate(price_levels):  # price òåïåðü áåðåòñÿ èç ñïèñêà
        order = create_order(symbol, price, amount_per_order)
        if order:
            print(f"Order {i + 1} placed: {order}")
            orders.append(order)
        else:
            print(f" ")

    time.sleep(1)  # Çàäåðæêà ïåðåä ñëåäóþùèì îðäåðîì
    
    save_orders_to_file(orders)
    
if __name__ == "__main__":
    main()
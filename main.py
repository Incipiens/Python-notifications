import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import schedule
import time
from win10toast import ToastNotifier

def get_weather(api_key, location):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
    response = requests.get(url)
    data = response.json()
    return data

def get_stock(api_key, symbol):
    url = f"https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol={symbol}&interval=1min&apikey={api_key}"
    response = requests.get(url)
    data = response.json()
    return data

def get_news(api_key, keyword):
    url = f"https://newsapi.org/v2/everything?q={keyword}&apiKey={api_key}"
    response = requests.get(url)
    data = response.json()
    return data['articles']


# This checks whether temperature is between 0 C and 30 C, just to demonstrate how you can add a criteria before notifying the user
def should_notify_weather(data):
    temp_k = data['main']['temp']
    temp_c = temp_k - 273.15
    if temp_c > 0 or temp_c < 30:
        return True
    return False

def should_notify_stock(data):
    last_close = float(data['Time Series (1min)'][list(data['Time Series (1min)'].keys())[0]]['4. close'])
    if last_close > 150:
        return True
    return False

def should_notify_game_price(price, threshold):
    if price <= threshold:
        return True
    return False

def display_weather(data):
    temp_k = data['main']['temp']
    temp_c = temp_k - 273.15
    print(f"Weather: {data['weather'][0]['description']}, Temperature: {temp_c:.2f}°C")

def display_stock(data):
    last_close = float(data['Time Series (1min)'][list(data['Time Series (1min)'].keys())[0]]['4. close'])
    print(f"Stock: {last_close:.2f} USD")

def send_email(subject, body, to_email, from_email, from_password):
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_email, from_password)
    text = msg.as_string()
    server.sendmail(from_email, to_email, text)
    server.quit()

def get_steam_game_price(appid):
    url = f"https://store.steampowered.com/api/appdetails?appids={appid}"
    response = requests.get(url)
    data = response.json()
    if data[str(appid)]['success']:
        price_info = data[str(appid)]['data']['price_overview']
        return price_info['final'] / 100.0  # Price in USD
    else:
        return None
    
def display_game_price(price, name):
    print(f"{name} price: {price:.2f} USD")

def display_news(articles, keyword):
    print(f"News for {keyword}:")
    for article in articles[:5]:  # Display top 5 news articles
        print(f"- {article['title']}")

def show_windows_notification(title, message):
    toaster = ToastNotifier()
    toaster.show_toast(title, message, duration=10)

def job():
    weather_api_key = 'XXX'
    stock_api_key = 'XXX'
    news_api_key = 'XXX'
    location = 'Dublin, Ireland'
    stock_symbol = 'AAPL'
    steam_appid = '1888930'
    steam_game_name = 'The Last of Us: Part I'
    price_threshold = 60.00
    news_keyword = 'technology'
    to_email = 'XXX'
    from_email = 'XXX'
    from_password = 'XXX'

    weather_data = get_weather(weather_api_key, location)
    stock_data = get_stock(stock_api_key, stock_symbol)
    game_price = get_steam_game_price(steam_appid)
    news_articles = get_news(news_api_key, news_keyword)

    if game_price is not None:
        display_game_price(game_price, steam_game_name)

    display_news(news_articles, news_keyword)
    display_weather(weather_data)
    display_stock(stock_data)
    

    # Calculate temp_c for weather notification
    temp_k = weather_data['main']['temp']
    temp_c = temp_k - 273.15

    if should_notify_weather(weather_data):
        send_email('Weather Alert', f"Current weather: {weather_data['weather'][0]['description']}, Temperature: {temp_c:.2f}°C", to_email, from_email, from_password)
        show_windows_notification('Weather Alert', f"Current weather: {weather_data['weather'][0]['description']}, Temperature: {temp_c:.2f}°C")

    if should_notify_stock(stock_data):
        last_close = float(stock_data['Time Series (1min)'][list(stock_data['Time Series (1min)'].keys())[0]]['4. close'])
        send_email('Stock Alert', f"Current stock price of {stock_symbol}: {last_close:.2f} USD", to_email, from_email, from_password)
    
    if game_price is not None and should_notify_game_price(game_price, price_threshold):
        send_email('Game Price Alert', f"The price of {steam_game_name} is now {game_price:.2f} USD, which is below your threshold of {price_threshold:.2f} USD.", to_email, from_email, from_password)

    if news_articles:
        news_body = '\n'.join([f"- {article['title']}" for article in news_articles[:5]])
        send_email('News Alert', f"Top news for {news_keyword}:\n{news_body}", to_email, from_email, from_password)


# This was set abnormally low for testing. Increase this.
schedule.every(0.1).minutes.do(job)

while True:
    schedule.run_pending()
    time.sleep(1)

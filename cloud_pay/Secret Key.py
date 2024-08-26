import jwt
from flask import Flask, request
from config_data.config import Config, load_config

config: Config = load_config('.env')
app = Flask(__name__)

secret_key = config.pay.api_secret_cloud

@app.route('/', methods=['POST'])
def handle_postback():
    if request.method == 'POST':
        status = request.form.get('status')
        invoice_id = request.form.get('invoice_id')
        amount_crypto = request.form.get('amount_crypto')
        currency = request.form.get('currency')
        order_id = request.form.get('order_id')
        token = request.form.get('token')

        try:
            jwt.decode(token, secret_key, algorithms=['HS256'])

            response = f"Payment status: {status}\n" \
                       f"Invoice ID: {invoice_id}\n" \
                       f"Amount in crypto: {amount_crypto} {currency}\n" \
                       f"Order ID: {order_id}\n"
            print(response)

            return response
        except jwt.InvalidTokenError:
            return "Invalid token\n"
    else:
        return "Invalid request method\n"

if __name__ == '__main__':
    app.run()

from flask import Flask, render_template, request, jsonify
import pickle
import numpy as np
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "../frontend"),
    static_folder=os.path.join(BASE_DIR, "../frontend")

)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, 'model')

with open(os.path.join( 'fraud_model.pkl'), 'rb') as f:
    model = pickle.load(f)

with open(os.path.join( 'label_encoders.pkl'), 'rb') as f:
    encoders = pickle.load(f)

with open(os.path.join( 'features.pkl'), 'rb') as f:
    FEATURES = pickle.load(f)

INDIAN_CITIES = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad',
                 'Pune', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Surat']

MERCHANTS = ['Flipkart', 'Amazon India', 'Swiggy', 'Zomato', 'BigBasket',
             'Myntra', 'Paytm Mall', 'Nykaa', 'MakeMyTrip', 'BookMyShow',
             'Reliance Digital', 'Croma', 'Shoppers Stop', 'DMart', 'Petrol Pump',
             'Hospital', 'Restaurant', 'Grocery Store', 'ATM Withdrawal', 'Utility Bill','Gambling', 'Third part application']


def safe_encode(encoder, value, known_list):
    """Encode a value; if unseen, use index 0 as fallback."""
    if value in encoder.classes_:
        return encoder.transform([value])[0]
    else:
        return 0  # fallback for unknown categories


@app.route('/')
def index():
    """Home page - transaction input form"""
    return render_template('index.html',
                           cities=INDIAN_CITIES,
                           merchants=MERCHANTS)


@app.route('/predict', methods=['POST'])
def predict():
    """
    Receive transaction details and return fraud prediction.
    Expects JSON data from the frontend form.
    """
    try:
        data = request.get_json()

        transaction_amount  = float(data['transaction_amount'])
        transaction_hour    = int(data['transaction_hour'])
        day_of_week         = int(data['day_of_week'])
        merchant_category   = str(data['merchant_category'])
        city                = str(data['city'])
        distance_from_home  = float(data['distance_from_home_km'])
        transactions_24h    = int(data['transactions_last_24h'])
        avg_amount          = float(data['avg_transaction_amount'])
        is_international    = int(data['is_international'])
        is_online           = int(data['is_online'])
        card_present        = int(data['card_present'])

        merchant_enc = safe_encode(encoders['merchant'], merchant_category, MERCHANTS)
        city_enc     = safe_encode(encoders['city'], city, INDIAN_CITIES)

        import pandas as pd
        features = pd.DataFrame([[
            transaction_amount, transaction_hour, day_of_week,
            merchant_enc, city_enc, distance_from_home,
            transactions_24h, avg_amount,
            is_international, is_online, card_present
        ]], columns=FEATURES)

        prediction = model.predict(features)[0]
        probabilities = model.predict_proba(features)[0]

        fraud_probability = round(float(probabilities[1]) * 100, 2)
        normal_probability = round(float(probabilities[0]) * 100, 2)

        if fraud_probability == 100:
            risk_level = "HIGH RISK"
            risk_color = "red" 
        if fraud_probability >= 70:
            risk_level = "HIGH RISK"
            risk_color = "red"   
        elif fraud_probability >= 40:
            risk_level = "MEDIUM RISK"
            risk_color = "orange"
        else:
            risk_level = "LOW RISK"
            risk_color = "green"

        reasons = []
        if transaction_hour < 5 or transaction_hour >= 22:
            reasons.append("⏰ Transaction at unusual hour (late night / early morning)")
        if transaction_amount > 50000:
            reasons.append("💰 Very high transaction amount (₹{:,.0f})".format(transaction_amount))
        if transaction_amount > avg_amount * 3:
            reasons.append("📈 Amount is 3x higher than your average transaction")
        if distance_from_home > 100:
            reasons.append("📍 Transaction location is far from home ({:.0f} km)".format(distance_from_home))
        if transactions_24h > 8:
            reasons.append("🔄 Too many transactions in last 24 hours ({})".format(transactions_24h))
        if is_international == 1:
            reasons.append("🌍 International transaction detected")
        if is_online == 1 and card_present == 0:
            reasons.append("💻 Online transaction with card not physically present")

        # Force fraud for restricted merchant categories, overriding the ML model
        restricted_merchants = ['Gambling', 'Third part application']
        if merchant_category in restricted_merchants:
            prediction = 1
            fraud_probability = 100.0
            normal_probability = 0.0
            reasons.append("🚫 Transaction made to a restricted/high-risk merchant category ({})".format(merchant_category))

        if not reasons and prediction == 0:
            reasons.append("🤖 ML model detected unusual pattern in transaction data")
        

        return jsonify({
            'success': True,
            'is_fraud': bool(prediction),
            'fraud_probability': fraud_probability,
            'normal_probability': normal_probability,
            'risk_level': risk_level,
            'risk_color': risk_color,
            'reasons': reasons,
            'message': '🚨 FRAUDULENT TRANSACTION DETECTED!' if prediction == 1 else '✅ Transaction Looks Normal'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400


@app.route('/about.html')
def about():
    """About page - how the system works"""
    return render_template('about.html')
if __name__ == '__main__':
    print("🚀 Starting Credit Card Fraud Detection Server...")
    print("📱 Open your browser and go to: http://127.0.0.1:5000")

    print("Template folder:", app.template_folder)
    print("Index exists:", os.path.exists(os.path.join(app.template_folder, "index.html")))
    print("About exists:", os.path.exists(os.path.join(app.template_folder, "about.html")))

    app.run(debug=True, host='0.0.0.0', port=5000)
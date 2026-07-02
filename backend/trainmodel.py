
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report, confusion_matrix
import pickle
import random

np.random.seed(42)
random.seed(42)

def generate_indian_transaction_data(n_samples=5000):
    """
    Generate realistic synthetic Indian credit card transactions.
    Features based on common Indian fraud patterns.
    """

    data = []

    indian_cities = ['Mumbai', 'Delhi', 'Bangalore', 'Chennai', 'Hyderabad',
                     'Pune', 'Kolkata', 'Ahmedabad', 'Jaipur', 'Surat']
    
    merchants = ['Flipkart', 'Amazon India', 'Swiggy', 'Zomato', 'BigBasket',
                 'Myntra', 'Paytm Mall', 'Nykaa', 'MakeMyTrip', 'BookMyShow',
                 'Reliance Digital', 'Croma', 'Shoppers Stop', 'DMart', 'Petrol Pump',
                 'Hospital', 'Restaurant', 'Grocery Store', 'ATM Withdrawal', 'Utility Bill','Gambling', 'Third part application']

    for _ in range(int(n_samples * 0.90)):
        hour = np.random.choice(range(8, 23), p=[0.05,0.10,0.10,0.12,0.10,0.10,0.10,0.08,0.07,0.05,0.05,0.04,0.03,0.01,0.00])
        amount = np.random.lognormal(mean=7.5, sigma=1.2)  # INR amounts, typical range ₹100 - ₹50,000
        amount = round(min(max(amount, 50), 150000), 2)

        data.append({
            'transaction_amount': amount,
            'transaction_hour': hour,
            'day_of_week': np.random.randint(0, 7),
            'merchant_category': np.random.choice(merchants),
            'city': np.random.choice(indian_cities),
            'distance_from_home_km': np.random.exponential(scale=15),
            'transactions_last_24h': np.random.poisson(3),
            'avg_transaction_amount': amount * np.random.uniform(0.7, 1.3),
            'is_international': 0,
            'is_online': np.random.choice([0, 1], p=[0.5, 0.5]),
            'card_present': np.random.choice([0, 1], p=[0.4, 0.6]),
            'is_fraud': 0
        })

    for _ in range(int(n_samples * 0.10)):
        # Fraud patterns: late night, high amount, unusual location, many txns
        hour = np.random.choice(list(range(0, 5)) + list(range(22, 24)))
        amount = np.random.lognormal(mean=10, sigma=1.5)  # Higher amounts
        amount = round(min(max(amount, 5000), 500000), 2)

        data.append({
            'transaction_amount': amount,
            'transaction_hour': hour,
            'day_of_week': np.random.randint(0, 7),
            'merchant_category': np.random.choice(merchants),
            'city': np.random.choice(indian_cities),
            'distance_from_home_km': np.random.exponential(scale=200),  # Far from home
            'transactions_last_24h': np.random.poisson(10),  # Many transactions
            'avg_transaction_amount': amount * np.random.uniform(0.1, 0.4),  # Way above avg
            'is_international': np.random.choice([0, 1], p=[0.3, 0.7]),  # Often international
            'is_online': np.random.choice([0, 1], p=[0.2, 0.8]),  # Mostly online
            'card_present': np.random.choice([0, 1], p=[0.8, 0.2]),  # Card not present
            'is_fraud': 1
        })

    df = pd.DataFrame(data)
    df = df.sample(frac=1).reset_index(drop=True)  # Shuffle
    return df


print("📊 Generating Indian transaction data...")
df = generate_indian_transaction_data(5000)

print(f"✅ Total transactions: {len(df)}")
print(f"   Normal: {(df['is_fraud']==0).sum()} | Fraud: {(df['is_fraud']==1).sum()}")

le_merchant = LabelEncoder()
le_city = LabelEncoder()

df['merchant_encoded'] = le_merchant.fit_transform(df['merchant_category'])
df['city_encoded'] = le_city.fit_transform(df['city'])

FEATURES = [
    'transaction_amount', 'transaction_hour', 'day_of_week',
    'merchant_encoded', 'city_encoded', 'distance_from_home_km',
    'transactions_last_24h', 'avg_transaction_amount',
    'is_international', 'is_online', 'card_present'
]

X = df[FEATURES]
y = df['is_fraud']

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("\n🤖 Training Random Forest model...")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    class_weight='balanced'  # Handle imbalanced data
)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print("\n📈 Model Performance:")
print(classification_report(y_test, y_pred, target_names=['Normal', 'Fraud']))

accuracy = (y_pred == y_test).mean() * 100
print(f"✅ Accuracy: {accuracy:.2f}%")

# Save model and encoders
with open('fraud_model.pkl', 'wb') as f:
    pickle.dump(model, f)

with open('label_encoders.pkl', 'wb') as f:
    pickle.dump({'merchant': le_merchant, 'city': le_city}, f)

# Save feature list
with open('features.pkl', 'wb') as f:
    pickle.dump(FEATURES, f)

print("\n✅ Model saved as fraud_model.pkl")
print("✅ Encoders saved as label_encoders.pkl")
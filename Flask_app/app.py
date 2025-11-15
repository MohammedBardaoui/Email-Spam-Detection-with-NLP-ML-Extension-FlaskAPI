from flask import Flask, request, jsonify
import joblib
import pandas as pd
from scipy import sparse
from preprocessing_utils import preprocess_text, calculate_suspicious_char_ratio, calculate_suspicious_words_ratio
from pyngrok import ngrok
from flask_cors import CORS
import nltk
nltk.download('punkt_tab')

# -------------------------------
# 1 Load ML artifacts
# -------------------------------
model = joblib.load("models/naive_bayes_model.joblib")
tfidf_vectorizer = joblib.load("models/tfidf_vectorizer.joblib")
scaler = joblib.load("models/scaler.joblib")

# -------------------------------
# 2 Initialize Flask
# -------------------------------
app = Flask(__name__)
CORS(app)

# -------------------------------
# 3 Define prediction route
# -------------------------------
@app.route("/predict", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        subject = data.get("subject", "")
        body = data.get("body", "")

        # Merge and preprocess
        full_text = subject + " " + body
        tokens = preprocess_text(full_text)
        clean_text = " ".join(tokens)

        # Numeric features
        ratio_char = calculate_suspicious_char_ratio(full_text)
        ratio_word = calculate_suspicious_words_ratio(full_text)
        numeric_features = pd.DataFrame(
            [[ratio_word, ratio_char]],
            columns=['suspicious_word_ratio', 'suspicious_char_ratio']
        )
        numeric_scaled = scaler.transform(numeric_features)

        # TF-IDF
        X_tfidf = tfidf_vectorizer.transform([clean_text])

        # Combine
        X_final = sparse.hstack([X_tfidf, numeric_scaled])

        # Predict
        prediction = model.predict(X_final)[0]
        probability = model.predict_proba(X_final)[0][1]
        label = "SPAM" if prediction == 1 else "HAM"

        return jsonify({
            "label": label,
            "probability": round(probability * 100, 2)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# -------------------------------
# 4 Start Flask with ngrok
# -------------------------------
if __name__ == "__main__":
    # Authenticate ngrok
    ngrok.set_auth_token("3546zXN7mASkD5fPmFL3N1U2g_wxUbrgtGE9Jhvb") # Your_ngrok_auhtentification_token

    # Open HTTP tunnel
    public_url = ngrok.connect(5000)
    print("🚀 ngrok tunnel URL:", public_url)

    # Run Flask
    app.run(port=5000)

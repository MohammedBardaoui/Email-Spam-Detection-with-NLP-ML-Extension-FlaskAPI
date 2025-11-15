import re
import nltk
import numpy as np
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from scipy import sparse

# Ensure necessary resources are downloaded
nltk.download("punkt", quiet=True)
nltk.download("stopwords", quiet=True)
nltk.download("wordnet", quiet=True)

# --- CONSTANTS ---
SUSPICIOUS_CHARS = r'[$€£!%]'
SUSPICIOUS_WORDS = [
    'free', 'win', 'prize', 'bonus', 'discount', 'offer', 'deal', 'sale',
    'urgent', 'immediate', 'act', 'miss', 'last', 'expires', 'deadline', 'hurry', 'quick', 'rush',
    'money', 'cash', 'earn', 'income', 'investment', 'guarantee', 'risk-free', 'refund', 'lottery', 'million',
    'subscribe', 'unsubscribe', 'reply', 'visit', 'download', 'order', 'register', 'join', 'apply',
    'viagra', 'cialis', 'password', 'account', 'security', 'verify', 'confirm', 'alert', 'notification', 'update'
]

greetings = [
    'dear', 'hi', 'hello', 'hey', 'greetings',
    'regards', 'best', 'thanks', 'thank',
    'sincerely', 'cheers', 'respectfully','welcome','goodbye'
]
STOPWORDS = set(stopwords.words('english'))
lemmatizer = WordNetLemmatizer()

GREETINGS_PATTERN = re.compile(r'\b(?:' + '|'.join(map(re.escape, greetings)) + r')\b', re.IGNORECASE)
URL_PATTERN = re.compile(r'http\S+|www\S+')
NON_ALPHA_PATTERN = re.compile(r'[^a-zA-Z]')
EMAIL_PATTERN = re.compile(r'\b[\w\.-]+@[\w\.-]+\.\w+\b')

def preprocess_text(text, min_len=2, max_len=13):
    # Lowercase
    text = text.lower()
    
    # Remove URLs
    text = URL_PATTERN.sub(' ', text)
    
    # Remove greetings
    text = GREETINGS_PATTERN.sub(' ', text)
    
    # Remove punctuation/non-alpha
    text = NON_ALPHA_PATTERN.sub(' ', text)
    
    # Tokenize
    tokens = word_tokenize(text)
    
    # Remove stopwords
    tokens = [t for t in tokens if t not in STOPWORDS]
    
    # Keep reasonable token lengths
    tokens = [t for t in tokens if min_len <= len(t) <= max_len]
    
    # Lemmatize
    tokens = [lemmatizer.lemmatize(t) for t in tokens]
    
    return tokens

# Function to calculate ratio (suspicious chars per word)
def calculate_suspicious_char_ratio(text):
    # count of suspicious characters
    char_count = len(re.findall(SUSPICIOUS_CHARS, text))
    
    # word count 
    words = word_tokenize(text.lower())  # Tokenize for precise word count
    word_count = len(words)
    
    # The ratio 
    if word_count > 0:
        return char_count / word_count
    else:
        return 0  

def calculate_suspicious_words_ratio(text):
    # Count of suspicious words
    suspicious_word_count = sum(1 for word in SUSPICIOUS_WORDS if re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE))
    
    # total word count 
    words = word_tokenize(text.lower()) 
    word_count = len(words)
    
    # The ratio 
    if word_count > 0:
        return suspicious_word_count / word_count
    else:
        return 0 

# --- Function to create feature matrices for train and test ---
def create_feature_matrices(train_df, test_df, vectorizer, numeric_train, numeric_test):
    # Fit vectorizer on train text
    X_train_text = vectorizer.fit_transform(train_df['clean_text'])
    # transform vectorizer on test text
    X_test_text  = vectorizer.transform(test_df['clean_text'])
    
    # Convert numeric features to sparse
    numeric_train_sparse = sparse.csr_matrix(numeric_train)
    numeric_test_sparse  = sparse.csr_matrix(numeric_test)
    
    # Combine text + numeric features
    X_train_combined = sparse.hstack([X_train_text, numeric_train_sparse])
    X_test_combined  = sparse.hstack([X_test_text, numeric_test_sparse])
    
    return X_train_combined, X_test_combined, vectorizer
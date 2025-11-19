import os
import string
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

class StockPriceSentimentPredictor:
    """A class to predict stock price movements based on sentiment analysis of news articles."""

    def __init__(self, model_type, model_path="model.joblib", vectorizer_path="vectorizer.joblib", encoder_path="encoder.joblib"):
        if not model_type:
            raise ValueError("A valid model type must be provided.")
        self.model_type = model_type
        self.model = None
        self.vectorizer = None
        self.encoder = None
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.encoder_path = encoder_path

        # Try to load existing artifacts
        self._load_existing()

    def _load_existing(self):
        """Load model, vectorizer, and encoder if files exist."""
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
        if os.path.exists(self.vectorizer_path):
            self.vectorizer = joblib.load(self.vectorizer_path)
        if os.path.exists(self.encoder_path):
            self.encoder = joblib.load(self.encoder_path)

    def fetch_dataset(self):
        """Fetch or load the dataset."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            dataset_path = os.path.join(script_dir, "..", "dataset", "all_sentences_unioned.csv")
            return pd.read_csv(dataset_path)
        except FileNotFoundError as e:
            print(f"Error loading dataset: {str(e)}")
            raise

    def preprocess_data(self, data):
        """Clean text, tokenize, and convert to numeric features + labels."""
        data['sentence'] = data['sentence'].str.lower().apply(
            lambda text: text.translate(str.maketrans('', '', string.punctuation))
        )
        self.vectorizer = TfidfVectorizer(stop_words='english')
        X = self.vectorizer.fit_transform(data['sentence'])

        self.encoder = LabelEncoder()
        y = self.encoder.fit_transform(data['label'])
        return X, y

    def initialize_model(self):
        """Initialize and return the ML model."""
        if self.model_type == "SVC":
            from sklearn.svm import SVC
            self.model = SVC(kernel='linear', probability=True)
        elif self.model_type == "NaiveBayes":
            from sklearn.naive_bayes import GaussianNB
            self.model = GaussianNB()
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        return self.model

    def train(self, X, y):
        """Train the model."""
        if self.model is None:
            self.initialize_model()

        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        if self.model_type == "NaiveBayes":
            X_train, X_test = X_train.toarray(), X_test.toarray()

        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        print(classification_report(y_test, y_pred, target_names=self.encoder.classes_))

        # Save artifacts after training
        self.save_model(self.model_path, self.vectorizer_path, self.encoder_path)

    def predict(self, texts):
        """Predict sentiment for new text(s)."""
        if self.vectorizer is None or self.model is None or self.encoder is None:
            raise RuntimeError("Model artifacts are missing. Please train the model first.")

        X = self.vectorizer.transform(texts)
        if self.model_type == "NaiveBayes":
            X = X.toarray()
        y_pred = self.model.predict(X)
        return self.encoder.inverse_transform(y_pred)

    def save_model(self, model_path, vectorizer_path, encoder_path):
        """Save the trained model, vectorizer, and encoder to disk."""
        joblib.dump(self.model, model_path)
        joblib.dump(self.vectorizer, vectorizer_path)
        joblib.dump(self.encoder, encoder_path)


if __name__ == "__main__":
    predictor = StockPriceSentimentPredictor(model_type="SVC")
    
    # If artifacts are missing, train from scratch
    if predictor.model is None or predictor.vectorizer is None or predictor.encoder is None:
        print("Training new model...")
        data = predictor.fetch_dataset()
        X, y = predictor.preprocess_data(data)
        predictor.train(X, y)
    else:
        print("Loaded existing model artifacts.")

    # Example prediction
    sample_headline = ["Stock markets surge after positive earnings reports"]
    print("Prediction:", predictor.predict(sample_headline))

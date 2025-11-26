# backend/model.py
import os
import string
import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

class StockPriceSentimentPredictor:
    """Predict stock price sentiment based on news headlines."""

    def __init__(self, model_type="SVC",
                 model_path="model.joblib",
                 vectorizer_path="vectorizer.joblib",
                 encoder_path="encoder.joblib"):
        self.model_type = model_type
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.encoder_path = encoder_path

        self.model = None
        self.vectorizer = None
        self.encoder = None

        # Load existing artifacts if available
        self._load_artifacts()

    def _load_artifacts(self):
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
            if os.path.exists(self.vectorizer_path):
                self.vectorizer = joblib.load(self.vectorizer_path)
            if os.path.exists(self.encoder_path):
                self.encoder = joblib.load(self.encoder_path)
        except Exception as e:
            print(f"Error loading artifacts: {e}")
            self.model = None
            self.vectorizer = None
            self.encoder = None

    def fetch_dataset(self):
        """Load dataset from CSV file."""
        dataset_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "all_sentences_unioned.csv")
        data = pd.read_csv(dataset_path)
        data = data.drop_duplicates()
        data = data.dropna(subset=['sentence', 'label'])
        data['label'] = data['label'].str.strip().str.lower()
        return data

    def preprocess_data(self, data):
        """Preprocess text and encode labels."""
        data['sentence'] = data['sentence'].str.lower().apply(
            lambda x: x.translate(str.maketrans('', '', string.punctuation))
        )

        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        X = self.vectorizer.fit_transform(data['sentence'])

        self.encoder = LabelEncoder()
        y = self.encoder.fit_transform(data['label'])
        return X, y

    def initialize_model(self):
        """Initialize ML model."""
        if self.model_type == "SVC":
            from sklearn.svm import SVC
            self.model = SVC(kernel='linear', probability=True, class_weight='balanced')
        elif self.model_type == "NaiveBayes":
            from sklearn.naive_bayes import GaussianNB
            self.model = GaussianNB()
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")

    def train(self, X, y):
        """Train the model."""
        if self.model is None:
            self.initialize_model()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        if self.model_type == "NaiveBayes":
            X_train, X_test = X_train.toarray(), X_test.toarray()

        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        print("Classification Report:")
        print(classification_report(y_test, y_pred, target_names=self.encoder.classes_))

        self.save_artifacts()

    def predict(self, texts):
        """Predict sentiment for new text(s)."""
        if not all([self.model, self.vectorizer, self.encoder]):
            raise RuntimeError("Model artifacts missing. Train or reload the model first.")

        X = self.vectorizer.transform(texts)
        if self.model_type == "NaiveBayes":
            X = X.toarray()

        y_pred = self.model.predict(X)
        return self.encoder.inverse_transform(y_pred)

    def save_artifacts(self):
        """Save model, vectorizer, and encoder."""
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.vectorizer, self.vectorizer_path)
        joblib.dump(self.encoder, self.encoder_path)


if __name__ == "__main__":
    predictor = StockPriceSentimentPredictor()

    if not all([predictor.model, predictor.vectorizer, predictor.encoder]):
        print("Training new model...")
        data = predictor.fetch_dataset()
        X, y = predictor.preprocess_data(data)
        predictor.train(X, y)
    else:
        print("Loaded existing model artifacts.")

    sample_headline = ["Stock markets surge after positive earnings reports"]
    print("Prediction:", predictor.predict(sample_headline))

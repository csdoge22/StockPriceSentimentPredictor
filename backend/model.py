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

    def __init__(self, model_type, model_path="model.joblib",
                 vectorizer_path="vectorizer.joblib", encoder_path="encoder.joblib"):
        if not model_type:
            raise ValueError("A valid model type must be provided.")
        self.model_type = model_type
        self.model = None
        self.vectorizer = None
        self.encoder = None
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.encoder_path = encoder_path

        # Try loading existing artifacts
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
        """Load dataset from CSV file."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            dataset_path = os.path.join(script_dir, "..", "dataset", "all_sentences_unioned.csv")
            data = pd.read_csv(dataset_path)
            # Clean dataset
            data = data.drop_duplicates()
            data = data.dropna(subset=['sentence', 'label'])
            data['label'] = data['label'].str.strip().str.lower()
            return data
        except FileNotFoundError as e:
            print(f"Error loading dataset: {str(e)}")
            raise

    def preprocess_data(self, data):
        """Preprocess text and encode labels."""
        # Lowercase and remove punctuation, keep numbers
        data['sentence'] = data['sentence'].str.lower().apply(
            lambda text: text.translate(str.maketrans('', '', string.punctuation))
        )

        # TF-IDF vectorization with unigrams + bigrams
        self.vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
        X = self.vectorizer.fit_transform(data['sentence'])

        # Encode labels
        self.encoder = LabelEncoder()
        y = self.encoder.fit_transform(data['label'])
        return X, y

    def initialize_model(self):
        """Initialize the ML model."""
        if self.model_type == "SVC":
            from sklearn.svm import SVC
            self.model = SVC(kernel='linear', probability=True, class_weight='balanced')
        elif self.model_type == "NaiveBayes":
            from sklearn.naive_bayes import GaussianNB
            self.model = GaussianNB()
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
        return self.model

    def train(self, X, y):
        """Train the model with stratified split."""
        if self.model is None:
            self.initialize_model()

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )

        # NaiveBayes needs dense arrays
        if self.model_type == "NaiveBayes":
            X_train, X_test = X_train.toarray(), X_test.toarray()

        self.model.fit(X_train, y_train)
        y_pred = self.model.predict(X_test)
        print("Classification Report:")
        print(classification_report(y_test, y_pred, target_names=self.encoder.classes_))

        # Save artifacts
        self.save_model(self.model_path, self.vectorizer_path, self.encoder_path)

    def predict(self, texts):
        """Predict sentiment for new text(s)."""
        if self.vectorizer is None or self.model is None or self.encoder is None:
            raise RuntimeError("Model artifacts are missing. Train the model first.")

        X = self.vectorizer.transform(texts)
        if self.model_type == "NaiveBayes":
            X = X.toarray()
        y_pred = self.model.predict(X)
        return self.encoder.inverse_transform(y_pred)

    def save_model(self, model_path, vectorizer_path, encoder_path):
        """Save trained artifacts."""
        joblib.dump(self.model, model_path)
        joblib.dump(self.vectorizer, vectorizer_path)
        joblib.dump(self.encoder, encoder_path)


if __name__ == "__main__":
    predictor = StockPriceSentimentPredictor(model_type="SVC")

    # Train if artifacts missing
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

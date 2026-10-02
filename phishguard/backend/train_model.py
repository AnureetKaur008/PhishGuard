"""
train_model.py
----------------
Trains the PhishGuard risk classifier on data/emails.json and saves it
to model.pkl. Prints precision / recall / F1 — the same metrics the
problem statement asks the dashboard to report.

Run:
    python train_model.py
"""

import os
import json
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

from features import extract, to_vector, FEATURE_ORDER

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_dataset(path=None):
    path = path or os.path.join(BASE_DIR, "data", "emails.json")
    with open(path) as f:
        rows = json.load(f)
    X, y = [], []
    for row in rows:
        feats = extract(row)["features"]
        X.append(to_vector(feats))
        y.append(1 if row["label"] == "phishing" else 0)
    return X, y


def main():
    X, y = load_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(
        n_estimators=200, max_depth=6, random_state=42, class_weight="balanced"
    )
    clf.fit(X_train, y_train)

    y_pred = clf.predict(X_test)
    precision = precision_score(y_test, y_pred)
    recall = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()
    false_positive_rate = fp / (fp + tn) if (fp + tn) else 0.0

    print("=== PhishGuard model evaluation (held-out test set) ===")
    print(f"Precision:            {precision:.3f}")
    print(f"Recall:               {recall:.3f}")
    print(f"F1 score:             {f1:.3f}")
    print(f"False positive rate:  {false_positive_rate:.3f}")
    print(f"Feature importances:")
    for name, imp in sorted(zip(FEATURE_ORDER, clf.feature_importances_),
                             key=lambda x: -x[1]):
        print(f"  {name:30s} {imp:.3f}")

    joblib.dump(clf, os.path.join(BASE_DIR, "model.pkl"))
    metrics = {
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1": round(f1, 3),
        "false_positive_rate": round(false_positive_rate, 3),
        "test_size": len(y_test),
    }
    with open(os.path.join(BASE_DIR, "metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)
    print("\nSaved model.pkl and metrics.json")


if __name__ == "__main__":
    main()

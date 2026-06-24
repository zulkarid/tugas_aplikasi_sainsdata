
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

def prepare_dataset(posts_data):

    df = pd.DataFrame(posts_data)

    df["jumlah_hashtag"] = df["hashtags"].apply(
        lambda x: len(x) if isinstance(x, list) else 0
    )

    df["panjang_caption"] = df["caption"].fillna("").astype(str).apply(len)

    df["likesCount"] = pd.to_numeric(
        df["likesCount"],
        errors="coerce"
    ).fillna(0)

    df["commentsCount"] = pd.to_numeric(
        df["commentsCount"],
        errors="coerce"
    ).fillna(0)

    median_likes = df["likesCount"].median()

    df["popular"] = (
        df["likesCount"] > median_likes
    ).astype(int)

    return df

def train_popularity_model(posts_data):

    df = prepare_dataset(posts_data)

    X = df[
        [
            "commentsCount",
            "jumlah_hashtag",
            "panjang_caption"
        ]
    ]

    y = df["popular"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    model = DecisionTreeClassifier(
        max_depth=4,
        random_state=42
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    return {
        "accuracy": round(accuracy_score(y_test, y_pred), 4),
        "precision": round(precision_score(y_test, y_pred, zero_division=0), 4),
        "recall": round(recall_score(y_test, y_pred, zero_division=0), 4),
        "f1_score": round(f1_score(y_test, y_pred, zero_division=0), 4)
    }


def predict_posts(posts_data):

    df = prepare_dataset(posts_data)

    feature_columns = [
        "commentsCount",
        "jumlah_hashtag",
        "panjang_caption"
    ]

    X = df[feature_columns]

    y = df["popular"]

    model = DecisionTreeClassifier(
        max_depth=4,
        random_state=42
    )

    model.fit(X, y)

    predictions = model.predict(X)

    results = []

    for i, pred in enumerate(predictions):

        results.append({
            "username": df.iloc[i].get("ownerUsername", ""),
            "likes": int(df.iloc[i]["likesCount"]),
            "comments": int(df.iloc[i]["commentsCount"]),
            "prediction": "Populer" if pred == 1 else "Tidak Populer"
        })

    return results

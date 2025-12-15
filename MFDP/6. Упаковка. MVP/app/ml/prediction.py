import joblib
import pandas as pd
import numpy as np
from helper.helper import get_user_data

PREDICTION_COLUMNS = joblib.load("./ml/columns.joblib")
MEANS = joblib.load("./ml/means.joblib")
STDS = joblib.load("./ml/stds.joblib")


def scale_data(data, means, stds):
    X_values = data.to_numpy(dtype=np.float32)
    X_values = (X_values - means) / stds

    return X_values


def preprocessing(user_df, general_df, premium_df):
    user_general_df = user_df[user_df.tank_id.isin(general_df.tank_id.values)]
    user_general_df = user_general_df.query("(battles >= wins + losses) & (battles > 10) & (damage_dealt > 0)")
    avg_cols = user_general_df.drop(["user_id", "tank_id", "max_xp", "battles", "max_frags", "mark_of_mastery"],
                                    axis=1).columns
    user_general_df[avg_cols] = user_general_df[avg_cols].div(user_general_df["battles"], axis=0).astype("float32")
    already_has = user_df[user_df.tank_id.isin(premium_df.tank_id.values)].tank_id.values
    predict_prem_df = premium_df[~premium_df.tank_id.isin(already_has)].query("tier >= 5")
    predict_prem_df = predict_prem_df.drop(["name", "default_profile.signal_range"], axis=1)

    user_general_df = user_general_df.pivot(index="user_id", columns="tank_id")
    user_general_df.columns = ["_".join([str(part) for part in col if part not in (None, "")]) for col in
                               user_general_df.columns]
    user_general_df.reset_index(inplace=True)

    prem_cols = (["tank_id"] + [col for col in predict_prem_df.columns if "default_profile" in col] + ["nation", "tier",
                                                                                                       "type"])
    predict_prem_df = predict_prem_df[prem_cols]

    X = user_general_df.merge(predict_prem_df, how="cross")
    needed_columns = list(set(PREDICTION_COLUMNS).difference(set(X.columns)))
    X = pd.concat([X, pd.DataFrame(columns=needed_columns)], axis=1)
    X = X[["user_id", "tank_id"] + list(PREDICTION_COLUMNS)]

    cat_cols = [col for col in X.columns if "mark_of_mastery" in col] + ["nation", "tier", "type"]
    num_cols = [col for col in X.columns if col not in ["user_id", "tank_id"] + cat_cols]

    X[num_cols] = scale_data(X[num_cols], MEANS, STDS)
    X[cat_cols] = X[cat_cols].astype("category")

    return X


def predict(model, user_id, general_df, premium_df):
    user_data = get_user_data(user_id)
    preprocessed_data = preprocessing(user_data, general_df, premium_df)
    preprocessed_data["preds"] = model.predict(preprocessed_data[PREDICTION_COLUMNS]).round().astype(int)
    res = preprocessed_data[["tank_id", "preds"]].sort_values("preds", ascending=False)

    return res.head(3)

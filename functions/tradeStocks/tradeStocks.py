import os
import io

import boto3

import pandas as pd
import dotenv as env


def handler(x, y):
    env.load_dotenv()

    s3_resource = boto3.resource(
        "s3",
        aws_access_key_id=os.environ["AWS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_KEY"],
    )

    df = pd.read_csv(
        io.BytesIO(
            s3_resource.Object(bucket_name="pcl-stockdata", key="mt.csv")
            .get()["Body"]
            .read()
        ),
        index_col=0,
    )

    assert isinstance(df, pd.DataFrame)

    bought = []

    for index, row in df.iterrows():
        if row["ema_50"] > row["ema_200"] and row["ema_50_y"] < row["ema_200_y"]:
            bought.append(index)

    print(bought)

    return {"status": 200, "data": {"bought_symbols": bought}}


if __name__ == "__main__":
    handler(0, 0)

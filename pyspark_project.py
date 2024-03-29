

# Commented out IPython magic to ensure Python compatibility.
# %pip install pyspark py4j -qq

from pyspark.sql import SparkSession

spark = SparkSession.builder.appName('PySpark_for_DataScience').getOrCreate()

import os

df = spark.read.csv(
    '/spotify_weekly_chart.csv',
    sep = ',',
    header = True,
    )

df.printSchema()

from pyspark.sql.types import *

data_schema = [
               StructField('Pos', IntegerType(), True),
               StructField('P+', StringType(), True),
               StructField('Artist', StringType(), True),
               StructField('Title', StringType(), True),
               StructField('Wks', IntegerType(), True),
               StructField('Pk', IntegerType(), True),
               StructField('(x?)', StringType(), True),
               StructField('Streams', IntegerType(), True),
               StructField('Streams+', DoubleType(), True),
               StructField('Total', IntegerType(), True),
            ]

final_struc = StructType(fields = data_schema)

df = spark.read.csv(
    '/spotify_weekly_chart.csv',
    sep = ',',
    header = True,
    schema = final_struc
    )

df.printSchema()

df.limit(5).toPandas()

df.describe().show()

df.count()

df = df.withColumnRenamed('Pos', 'Rank')

df.show(5)

df = df.drop('P+','Pk','(x?)','Streams+')

df.show(5)

df = df.na.drop()

df.select(['Artist', 'Artist', 'Total']).show(5)

from pyspark.sql.functions import col, lit, when

df.filter(
    (col("Total") >= lit("600000000")) & (col("Total") <= lit("700000000"))
).show(5)

df.select('Artist', 'Title',
            when(df.Wks >= 35, 1).otherwise(0)
           ).show(5)

df.select(['Artist','Wks','Total'])\
        .groupBy('Artist')\
        .mean()\
        .orderBy(['avg(Total)'], ascending = [False])\
        .show(5)

vis_df = (
    df.select(["Artist", "Wks", "Total"])
    .groupBy("Artist")
    .mean()
    .orderBy(["avg(Total)"], ascending=[False])
    .toPandas()
)

vis_df.iloc[0:7].plot(
    kind="bar",
    x="Artist",
    y="avg(Total)",
    figsize=(12, 6),
    ylabel="Average Average Streams",
)

final_data = (
    df.select(["Artist", "Wks", "Total"])
    .groupBy("Artist")
    .mean()
    .orderBy(["avg(Total)"], ascending=[False])
)

# CSV
final_data.write.csv("dataset.csv")

# JSON
final_data.write.save("dataset.json", format="json")

# Parquet
final_data.write.save("dataset.parquet", format="parquet")

from pyspark.ml.feature import (
    VectorAssembler,
    StringIndexer,
    OneHotEncoder,
    StandardScaler,
)

## Categorical Encoding
indexer = StringIndexer(inputCol="Artist", outputCol="Encode_Artist").fit(
    final_data
)
encoded_df = indexer.transform(final_data)

## Assembling Features
assemble = VectorAssembler(
    inputCols=["Encode_Artist", "avg(Wks)", "avg(Total)"],
    outputCol="features",
)

assembled_data = assemble.transform(encoded_df)

## Standard Scaling
scale = StandardScaler(inputCol="features", outputCol="standardized")
data_scale = scale.fit(assembled_data)
data_scale_output = data_scale.transform(assembled_data)
data_scale_output.show(5)

from pyspark.ml.clustering import KMeans
KMeans_algo=KMeans(featuresCol='standardized', k=4)
KMeans_fit=KMeans_algo.fit(data_scale_output)
preds=KMeans_fit.transform(data_scale_output)

preds.show(5)

import matplotlib.pyplot as plt
import seaborn as sns

df_viz = preds.select(
    "Artist", "avg(Wks)", "avg(Total)", "prediction"
).toPandas()
avg_df = df_viz.groupby(["prediction"], as_index=False).mean()

list1 = ["avg(Wks)", "avg(Total)"]

for i in list1:
    sns.barplot(x="prediction", y=str(i), data=avg_df)
    plt.show()

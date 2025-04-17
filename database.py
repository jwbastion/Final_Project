import pandas as pd
from sqlalchemy import create_engine
from urllib.parse import quote_plus

user = "teammate"
password = quote_plus("teampass123")
host = "localhost"
port = "5432"
db = "postgres"

engine = create_engine(f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}")

# 인코딩 주의: utf-8-sig
df_life = pd.read_csv("life.csv", encoding="utf-8-sig")
df_play = pd.read_csv("play.csv", encoding="utf-8-sig")
df_safety = pd.read_csv("safety.csv", encoding="utf-8-sig")
df_traffic = pd.read_csv("traffic.csv", encoding="utf-8-sig")
df_health = pd.read_csv("health.csv", encoding="utf-8-sig")

# 업로드
df_life.to_sql("life", engine, if_exists="append", index=False)
df_play.to_sql("play", engine, if_exists="append", index=False)
df_safety.to_sql("safety", engine, if_exists="append", index=False)
df_traffic.to_sql("traffic", engine, if_exists="append", index=False)
df_health.to_sql("health", engine, if_exists="append", index=False)

print("✅ 모든 테이블 업로드 완료!")

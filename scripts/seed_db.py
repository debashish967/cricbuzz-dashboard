# scripts/seed_db.py
import pandas as pd
from utils.db_connection import get_engine

engine = get_engine()

sample_matches = [
    {"match_id": 1, "teams": "India vs Australia", "score": "250/8", "overs": 50, "status": "Complete"},
    {"match_id": 2, "teams": "England vs Pakistan", "score": "120/3", "overs": 23.1, "status": "Live"}
]

df = pd.DataFrame(sample_matches)
df.to_sql("matches", engine, if_exists="replace", index=False)

print("✅ Sample matches inserted into DB")
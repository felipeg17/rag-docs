from datetime import datetime, timedelta
import os
import pdb

import dotenv

# Tracing
from langsmith import Client
import pandas as pd


# Cargar variables de entorno
dotenv.load_dotenv()

client = Client()

start_time = datetime.now() - timedelta(hours=8)

runs = list(
    client.list_runs(
        project_name=os.getenv("LANGCHAIN_PROJECT"),
        start_time=start_time,
    )
)

pdb.set_trace()

df = pd.DataFrame(
  [
    {
      "name": run.name,
      # "model": run.extra["invocation_params"][
      #     "model"
      # ],  # The parameters used when invoking the model are nested in the extra info
      **run.inputs,
      **(run.outputs or {}),
      "error": run.error,
      "latency": (run.end_time - run.start_time).total_seconds()
      if run.end_time
      else None,  # Pending runs have no end time
      "prompt_tokens": run.prompt_tokens,
      "completion_tokens": run.completion_tokens,
      "total_tokens": run.total_tokens,
    } for run in runs
  ],
  index=[run.id for run in runs],
)

df.head(5)

# Save the dataframe to a CSV file
df.to_csv("runs.csv")
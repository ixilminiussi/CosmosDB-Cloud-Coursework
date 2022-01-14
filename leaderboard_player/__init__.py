import logging
import json
import os

import azure.functions as func
from azure.cosmos import exceptions, CosmosClient, PartitionKey
from azure.cosmos.exceptions import CosmosHttpResponseError

host = os.environ["ACCOUNT_HOST"]
key = os.environ["ACCOUNT_KEY"]
# VVV WARNING : WHEN RUNNING LOCALLY USE THESE INSTEAD VVV
# host = os.environ["ConnectionStrings:ACCOUNT_HOST"]
# key = os.environ["ConnectionStrings:ACCOUNT_KEY"]

client = CosmosClient(host, credential=key, consistency_level="Session")

database = client.get_database_client("quiplash")
container = database.get_container_client("players")

def main(req: func.HttpRequest) -> func.HttpResponse:

    logging.info("Python HTTP trigger function processed a request.")

    #gets k
    k = req.params.get("top")
    if not k:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            k = req_body.get("top")


    if k <= 0:
        k = 1

    query = "SELECT * FROM c ORDER BY c.total_score DESC"

    profiles = list(container.query_items(query=query, enable_cross_partition_query=True))

    # checks that k isn"t too high
    if (k > len(profiles)):
        k = len(profiles)

    output = []
    for i in range(k):
        output.append({"username": profiles[i].get("username"), "score": profiles[i].get("total_score"), "games_played": profiles[i].get("games_played")})

    return func.HttpResponse(json.dumps(output), status_code = 200)
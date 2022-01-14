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
container = database.get_container_client("prompts")


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Python HTTP trigger function processed a request.")

    # Get whatever the value associated with "players" is
    players = req.params.get("players")
    if not players:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            players = req_body.get("players")

    if (str(players) == "-1"):
        query = "SELECT * FROM c"
    else:
        if (isinstance(players, str)):
            query = "SELECT * FROM c WHERE c.username = \"" + players + "\""
        else :
            query = "SELECT * FROM c WHERE"
            for player in players:
                query += " c.username = \"" + player + "\" OR"
            query = query[:-3] # removes extra "OR"

    prompts = list(container.query_items(query=query, enable_cross_partition_query=True))

    output = []
    for prompt in prompts:
        output.append({"id": int(prompt.get("id"))
        , "text": prompt.get("text"), "username": prompt.get("username")})

    outputjson = json.dumps(output)

    return func.HttpResponse(outputjson, status_code=200)
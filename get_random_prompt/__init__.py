import logging
import json
import os
import random

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

    # Get whatever the value associated with "n" is
    n = req.params.get("n")
    if not n:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            n = req_body.get("n")
    
    if (n < 1):
        return func.HttpResponse(json.dumps([]), status_code=200)

    query = "SELECT * FROM c"

    prompts = list(container.query_items(query=query, enable_cross_partition_query=True))

    # checks that n isn"t too high
    if (n > len(prompts)):
        n = len(prompts)

    # maps every value of n to a different value in len(prompts) range
    mapper = []
    for i in range(n):
        k = random.randrange(0, len(prompts), 1)
        while k in mapper:
            k = random.randrange(0, len(prompts))
        mapper.append(k)

    output = []

    for i in range(n):
        j = mapper[i]
        output.append({"id": int(prompts[j].get("id")), "text": prompts[j].get("text"), "username": prompts[j].get("username")})

    outputjson = json.dumps(output)

    return func.HttpResponse(outputjson, status_code=200)
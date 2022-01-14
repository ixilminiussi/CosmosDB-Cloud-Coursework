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

def main(req: func.HttpRequest, writer: func.Out[func.Document]) -> func.HttpResponse:

    logging.info("Python HTTP trigger function processed a request.")

    #gets username string
    username = req.params.get("username")
    if not username:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            username = req_body.get("username")

    #checks it"s not already taken
    query = "SELECT * FROM c WHERE c.username = \"" + username + "\""

    profiles = list(container.query_items(query=query, enable_cross_partition_query=True))

    if (profiles != []):
        output = {"result": False, "msg": "Username already exists"}
        return func.HttpResponse(json.dumps(output), status_code=200)

    #checks the length
    if (len(username) < 4):
        output = {"result": False, "msg": "Username less than 4 characters"}
        return func.HttpResponse(json.dumps(output), status_code=200)
    if (len(username) > 16):
        output = {"result": False, "msg": "Username more than 16 characters"}
        return func.HttpResponse(json.dumps(output), status_code=200)


    #gets password string
    password = req.params.get("password")
    if not password:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            password = req_body.get("password")

    #checks the length
    if (len(password) < 8):
        output = {"result": False, "msg": "Password less than 8 characters"}
        return func.HttpResponse(json.dumps(output), status_code=200)
    if (len(password) > 24):
        output = {"result": False, "msg": "Password more than 24 characters"}
        return func.HttpResponse(json.dumps(output), status_code=200)


    player = {"username": username, "password": password, "games_played": 0, "total_score": 0}
    output = {"result": True, "msg": "OK"} # default output, will get corrected if something is wrong

    #passes our values to json
    playerjson = json.dumps(player)
    outputjson = json.dumps(output)

    try:
        writer.set(func.Document.from_json(playerjson))
    except CosmosHttpResponseError:
        return func.HttpResponse("Something terrible happened....")

    return func.HttpResponse(outputjson, status_code=200)
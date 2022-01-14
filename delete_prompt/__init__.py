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
prompts_container = database.get_container_client("prompts")
players_container = database.get_container_client("players")


def main(req: func.HttpRequest) -> func.HttpResponse:
    
    logging.info("Python HTTP trigger function processed a request.")

        #gets id of prompt
    id = req.params.get("id")
    if not id:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            id = req_body.get("id")

    id = str(id) # makes sure it"s the appropriate format

    #checks the prompt matching the id
    query = "SELECT * FROM c WHERE c.id = \"" + id + "\""

    prompts = list(prompts_container.query_items(query=query, enable_cross_partition_query=True))

    if (prompts != []):
        prompt = prompts[0]
    else:
        output = {"result": False, "msg": "prompt id does not exist"}
        return func.HttpResponse(json.dumps(output), status_code=200)

    prompt_username = prompt.get("username")

    #gets username string
    username = req.params.get("username")
    if not username:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            username = req_body.get("username")

    #checks the username matches
    if (prompt_username != username):
        output = {"result": False, "msg": "bad username or password"}
        return func.HttpResponse(json.dumps(output), status_code=200)


    #checks the account matching the username
    query = "SELECT * FROM c WHERE c.username = \"" + username + "\""

    profiles = list(players_container.query_items(query=query, enable_cross_partition_query=True))

    if (profiles != []):
        profile = profiles[0]
    else:
        output = {"result": False, "msg": "bad username or password"}
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

    #checks password matches
    if (profile.get("password") != password):
        output = {"result": False, "msg": "bad username or password"}
        return func.HttpResponse(json.dumps(output), status_code=200)

    prompts_container.delete_item(item=id, partition_key=id)

    output = {"result": True, "msg": "OK"}
    return func.HttpResponse(json.dumps(output), status_code=200)
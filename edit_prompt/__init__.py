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
players_container = database.get_container_client("players")
prompts_container = database.get_container_client("prompts")

def main(req: func.HttpRequest, writer: func.Out[func.Document]) -> func.HttpResponse:

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

    #gets username string
    username = req.params.get("username")
    if not username:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            username = req_body.get("username")


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


    #gets prompt string
    prompt = req.params.get("text")
    if not prompt:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            prompt = req_body.get("text")

    #first checking size of text, to avoid unnecessary requests
    if (len(prompt) < 10):
        output = {"result": False, "msg": "prompt is less than 10 characters"}
        return func.HttpResponse(json.dumps(output), status_code=200)
    if (len(prompt) > 100):
        output = {"result": False, "msg": "prompt is more than 100 characters"}
        return func.HttpResponse(json.dumps(output), status_code=200)

    #checks for a prompt matching that text
    query = "SELECT * FROM c WHERE c.username = \"" + username + "\" AND c.text = \"" + prompt + "\""

    prompts = list(prompts_container.query_items(query=query, enable_cross_partition_query=True))

    if (prompts != []):
        output = {"result": False, "msg": "user already has a prompt with the same text"}
        return func.HttpResponse(json.dumps(output), status_code=200)

    prompt = {"id" : id, "username": username, "text" : prompt}
    output = {"result": True, "msg": "OK"} # default output

    #passes our values to json
    promptjson = json.dumps(prompt)
    outputjson = json.dumps(output)

    try:
        writer.set(func.Document.from_json(promptjson))
    except CosmosHttpResponseError:
        return func.HttpResponse("Something terrible happened....")

    return func.HttpResponse(outputjson, status_code=200)
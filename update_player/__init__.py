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

    #checks the account matching the username
    query = "SELECT * FROM c WHERE c.username = \"" + username + "\""

    profiles = list(container.query_items(query=query, enable_cross_partition_query=True))

    if (profiles != []):
        profile = profiles[0]
    else:
        output = {"result": False, "msg": "user does not exist"}
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
        output = {"result": False, "msg": "wrong password"}
        return func.HttpResponse(json.dumps(output), status_code=200)

    #gets add_to_games_played string
    add_to_games_played = req.params.get("add_to_games_played")
    if not add_to_games_played:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            add_to_games_played = req_body.get("add_to_games_played")

    #checks it doesn"t lead to negative score
    if add_to_games_played:
        if (profile.get("games_played") + add_to_games_played < 0):
                output = {"result": False, "msg": "Attempt to set negative score/games_played"}
                return func.HttpResponse(json.dumps(output), status_code=200)
    else:
        add_to_games_played = 0


    #gets add_to_score string
    add_to_score = req.params.get("add_to_score")
    if not add_to_score:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            add_to_score = req_body.get("add_to_score")
    
    #checks it doesn"t lead to negative score
    if add_to_score:
        if (profile.get("total_score") + add_to_score < 0):
                output = {"result": False, "msg": "Attempt to set negative score/games_played"}
                return func.HttpResponse(json.dumps(output), status_code=200)
    else: 
        add_to_score = 0

    #instead of modifying, we delete the old profile and add the new one (might change in the future, just seems easier for now)
    player = {"username": username, "password": password, "games_played": profile.get("games_played") + add_to_games_played, "total_score": profile.get("total_score") + add_to_score, "id": profile.get("id")}
    output = {"result": True, "msg": "OK"} # default output, will get corrected if something is wrong

    #passes our values to json
    playerjson = json.dumps(player)
    outputjson = json.dumps(output)

    try:
        writer.set(func.Document.from_json(playerjson))
    except CosmosHttpResponseError:
        return func.HttpResponse("Something terrible happened....")

    return func.HttpResponse(outputjson, status_code=200)
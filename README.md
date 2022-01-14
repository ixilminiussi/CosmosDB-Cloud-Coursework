this works once deployed, however when running locally

host = os.environ["ACCOUNT_HOST"]
key = os.environ["ACCOUNT_KEY"]

needs to be changed to

host = os.environ["ConnectionStrings:ACCOUNT_HOST"]
key = os.environ["ConnectionStrings:ACCOUNT_KEY"]

since the path in local.settings.json is slightly different 
than the one within Azure. I hope we weren't expected to make the same files
work both locally and in the cloud
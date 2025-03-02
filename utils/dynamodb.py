import boto3


def batch_get_item(table_name, primary_key, keys):
    client = boto3.client("dynamodb")
    request = {table_name: {"Keys": [{primary_key: {"S": key}} for key in keys]}}
    response = client.batch_get_item(RequestItems=request)

    if "Responses" in response:
        items = [
            {k: sv for k, v in item.items() for _, sv in v.items()}
            for item in response["Responses"][table_name]
        ]
        return items

    return []

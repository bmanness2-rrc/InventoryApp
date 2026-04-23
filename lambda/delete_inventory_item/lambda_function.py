import json
import boto3
from botocore.exceptions import ClientError
from decimal import Decimal

dynamodb = boto3.resource('dynamodb')
TABLE_NAME = 'Inventory'

def convert_decimals(obj):
    if isinstance(obj, list):
        return [convert_decimals(i) for i in obj]
    elif isinstance(obj, dict):
        return {k: convert_decimals(v) for k, v in obj.items()}
    elif isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    return obj

def lambda_handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    path_params = event.get('pathParameters', {})
    item_id = path_params.get('id')

    if not item_id:
        return {
            'statusCode': 400,
            'body': json.dumps("Missing 'id'")
        }

    try:
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('id').eq(item_id)
        )

        items = response.get('Items', [])

        if not items:
            return {
                'statusCode': 404,
                'body': json.dumps('No items found for this id')
            }

        deleted_items = []
        for item in items:
            table.delete_item(
                Key={
                    'id': item['id'],
                    'location_id': item['location_id']
                }
            )
            deleted_items.append(convert_decimals(item))

    except ClientError as e:
        print(f"Delete failed: {e.response['Error']['Message']}")
        return {
            'statusCode': 500,
            'body': json.dumps('Failed to delete item(s)')
        }

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f"{len(deleted_items)} item(s) deleted",
            'deletedItems': deleted_items
        })
    }
import os
import json
import boto3
from ip2geotools.databases.noncommercial import DbIpCity

if os.environ.get('is_lambda') == 'true':
    s3 = boto3.resource('s3')
else:
    s3 = boto3.resource(
        's3',
        aws_access_key_id='test',          # These credentials are arbitrary in LocalStack
        aws_secret_access_key='test',
        endpoint_url='http://localhost:4566'  # The LocalStack endpoint
    )
    s3.create_bucket(Bucket='visualize-us')

def get_s3_file():
    try:
        content_object = s3.Object('visualize-us', 'data.json')
        file_content = content_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
        print("Retrieved file from S3")
    except Exception as e: # File is not present
        print("File not found, creating new file")
        json_content = {}

    return json_content

def lambda_handler(event, context):
    stored_data = get_s3_file()
    ip = event['headers']['x-forwarded-for']
    res = DbIpCity.get(ip, api_key="free")

    latitude = res.latitude
    longitude = res.longitude
    key = f"{latitude},{longitude}"
    if ip not in stored_data:
        stored_data[key] = {
            'count': 1,
            'city': res.city,
            'region': res.region,
            'country': res.country,
        }
    else:
        stored_data[key]['count'] += 1

    s3.Object('visualize-us', 'data.json').put(Body=json.dumps(stored_data))

    # Get values as list
    values = [stored_data[key] for key in stored_data]
    return {
        'statusCode': 200,
        'body': {
            'full': values,
            'specific': stored_data[key],
        }
    }


# if __name__ == '__main__':
#     response = lambda_handler({
#         'headers': {
#             'x-forwarded-for': '198.35.26.96'
#         }
#     }, None)

#     print(response)
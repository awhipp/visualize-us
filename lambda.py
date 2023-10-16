'''
Create an S3 File and store the IP address and location of the user
who visited the website. The location is determined by the IP address.
'''
import os
import json
import boto3
import requests

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
    '''
    Get the S3 file and return the contents as a dictionary.
    '''
    try:
        content_object = s3.Object('visualize-us', 'data.json')
        file_content = content_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
    except Exception as e: # File is not present
        print("File not found, creating new file")
        json_content = {}

    return json_content

def get_location_from_ip(ip_address):
    '''
    Get the location of the user from the IP address.
    '''
    # Make a GET request to ipinfo.io with the IP address
    response = requests.get(f"https://ipinfo.io/{ip_address}/json", timeout=30)
    
    # Check if the request was successful
    if response.status_code == 200:
        data = response.json()
        return data
    else:
        return None


def lambda_handler(event, context):
    '''
    The main function that is called by AWS Lambda.
    '''
    stored_data = get_s3_file()
    ip = event['headers']['x-forwarded-for']
    res = get_location_from_ip(ip)

    key = res['loc']

    if ip not in stored_data:
        stored_data[key] = {
            'count': 1,
            'city': res['city'],
            'region': res['region'],
            'country': res['country'],
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

# For testing locally
if __name__ == '__main__':
    return_value = lambda_handler({
        'headers': {
            'x-forwarded-for': '198.35.26.96' # Random Address in San Jose from the Internet
        }
    }, None)
    print(return_value)

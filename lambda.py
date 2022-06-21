import json
import boto3
from datetime import datetime,timezone

ses_client = boto3.client("ses", region_name="eu-central-1")
config_client = boto3.client("config")
iam_client = boto3.client("iam")

def check_expired(date):
    #format = "%m/%d/%Y"
    #key_date = datetime.strptime(date, format)
    datedelta = datetime.now(timezone.utc) - date
    if datedelta.days >= 30:
        return True,datedelta.days
    else:
        return False,datedelta.days

def send_email(name,userid,keys):
    CHARSET = "UTF-8"
    HTML_EMAIL_CONTENT = """
        <html>
            <head></head>
            <h1 style='text-align:center'>Access Keys not rotated for 30 days</h1>
            <p>Access keys for user %s with Id %s has crossed the 30 day limit. The following keys have been disabled:</p>
        <table>
            <tr>
                <th>Key ID</th>
                <th>Age</th>
            </tr>
    """%(name,userid)
    
    for key in keys:
        HTML_EMAIL_CONTENT += """
            <tr>
                <td>%s</td>
                <td>%s</td>
            </tr>
        </table>
        </body>
        </html>"""%(key,keys[key])

    response = ses_client.send_email(
        Destination={
            "ToAddresses": [
                "shivam@betswap.gg",
            ],
        },
        Message={
            "Body": {
                "Html": {
                    "Charset": CHARSET,
                    "Data": HTML_EMAIL_CONTENT,
                }
            },
            "Subject": {
                "Charset": CHARSET,
                "Data": "Access Key not rotated for 30 days",
            },
        },
        Source="shivam@betswap.gg",
    )

def lambda_handler(event, context):
    resource = config_client.list_discovered_resources(resourceType='AWS::IAM::User',resourceIds=[event['Records'][0]['Sns']['Message']])
    #resource = config_client.list_discovered_resources(resourceType='AWS::IAM::User',resourceIds=['AIDAW7PWDJZAQHFIGRPJM'])
    print(event['Records'][0])
    print(resource)
    expired = False
    expired_keys = {}
    all_access_keys = iam_client.list_access_keys(UserName=resource['resourceIdentifiers'][0]['resourceName'])
    for key in all_access_keys['AccessKeyMetadata']:
        key_id = key['AccessKeyId']
        print(key)
        expired,days = check_expired(key['CreateDate'])
        if expired:
            expired_keys[key_id] = days
            #iam_client.update_access_key(AccessKeyId=key_id,Status='Inactive')
            
    if len(expired_keys):
        send_email(resource['resourceIdentifiers'][0]['resourceName'],resource['resourceIdentifiers'][0]['resourceId'],expired_keys)


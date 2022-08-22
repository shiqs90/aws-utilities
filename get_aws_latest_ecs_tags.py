import json
import boto3
from urllib import parse as urlparse
import base64

def fetch_tag_qa(environment):
    print("qa function called")
    client = boto3.client("ecs", region_name="ap-south-1")
    res=[]
    response = client.list_clusters(
        maxResults=99
    )
    print(response)
    if environment=="qa":
        print("Default QA environment")
    else:
        counter=0
        for i in response["clusterArns"]:
            if environment in i:
                print(environment+ " environment exists")
                break
            else:
                counter=counter+1
        if counter==len(response["clusterArns"]):
            print( environment+" environment does not exist")
            return {
                "statusCode": "200",
                "headers": { "Content-type": "application/json" },
                "body": json.dumps({
                    "text": environment+" environment does not exist",
                    "response_type": "in_channel"
                })
            }
    for cluster_arn in response['clusterArns']:
        service_arn = client.list_services(
            cluster=cluster_arn)
        service_name=service_arn['serviceArns'][0].split('/')[-1]

        response = client.describe_services(
            cluster=cluster_arn,services=[service_name])
        for service_detail in response['services']:
            task_def=service_detail['taskDefinition'].split('/')[-1]

            task_def_response = client.describe_task_definition(taskDefinition=task_def)
            for container_def in task_def_response['taskDefinition']['containerDefinitions']:
                str_resp=service_name+":"+str(container_def['image'].split(':')[-1])
                res.append(str_resp)
            response = {
                "statusCode": "200",
                "headers": { "Content-type": "application/json" },
                "body": json.dumps({
                    "text": '\n'.join(res),
                    "response_type": "in_channel"
                })
            }
    print(response)
    return response

def fetch_tag_alpha(environment):
    print("alpha function called")
    sts = boto3.client('sts')
    assume_role_response = sts.assume_role(RoleArn='arn:aws:iam::578469094242:role/_Fetch_Tag_Role',RoleSessionName='FetchTagrRole')
    access_key = assume_role_response['Credentials']['AccessKeyId']
    secret_key = assume_role_response['Credentials']['SecretAccessKey']
    session_token = assume_role_response['Credentials']['SessionToken']
    client = boto3.client("ecs", region_name="ap-south-1", aws_access_key_id=access_key, aws_secret_access_key=secret_key, aws_session_token=session_token)
    res=[]
    response = client.list_clusters(
        maxResults=99
    )
    if not (response["clusterArns"]):
        return {
            "statusCode": "200",
            "headers": { "Content-type": "application/json" },
            "body": json.dumps({
                "text": environment+" environment does not exist",
                "response_type": "in_channel"
            })
        }
    for cluster_arn in response['clusterArns']:
        service_arn = client.list_services(
            cluster=cluster_arn)
        service_name=service_arn['serviceArns'][0].split('/')[-1]

        response = client.describe_services(
            cluster=cluster_arn,services=[service_name])
        for service_detail in response['services']:
            task_def=service_detail['taskDefinition'].split('/')[-1]

            task_def_response = client.describe_task_definition(taskDefinition=task_def)
            for container_def in task_def_response['taskDefinition']['containerDefinitions']:
                str_resp=service_name+":"+str(container_def['image'].split(':')[-1])
                res.append(str_resp)
            response = {
                "statusCode": "200",
                "headers": { "Content-type": "application/json" },
                "body": json.dumps({
                    "text": '\n'.join(res),
                    "response_type": "in_channel"
                })
            }
    print(response)
    return response

def lambda_handler(event, context):
    msg_map = dict(urlparse.parse_qsl(base64.b64decode(str(event['body'])).decode('ascii')))  # data comes b64 and also urlencoded name=value& pairs
    params = msg_map.get('text','err').split(" ")  # params ['env','qa']
    environment = params[1].lower()
    qa_env_list=["qa","qa1","qa2","qa3","qa4","qa5"]
    if environment in qa_env_list:
        return fetch_tag_qa(environment)
    elif environment == 'alpha':
        return fetch_tag_alpha(environment)
    else:
        return {
            "statusCode": "200",
            "headers": { "Content-type": "application/json" },
            "body": json.dumps({
                "text": environment+" environment does not exist",
                "response_type": "in_channel"
            })
        }
#Python script invoking get_cost_and_usage will be:

#!/usr/bin/python3
import sys, getopt
import boto3
import pandas as pd
import numpy as np
import plotly.express as px
from openpyxl.workbook import Workbook

def main(argv):
    starting = ''
    ending = ''
    granularity = ''
    try:
        opts, args = getopt.getopt(argv,"s:e:g:",["start=","end=","granularity="])
    except getopt.GetoptError:
        print('get-cost-usage_usage-type.py -s 2022-03-07 -e 2022-05-07 -g MONTHLY')
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-s", "--start"):
            starting = arg
        elif opt in ("-e", "--end"):
            ending = arg
        elif opt in ("-g", "--granularity"):
            granularity = arg
    print("starting is", starting)
    print("endings", ending)
    print("granularity", granularity)

    sts = boto3.client('sts')
    assume_role_response = sts.assume_role(RoleArn='arn:aws:iam::223876882329:role/GetCostUsageReportRole',RoleSessionName='CostExplorerRole')
    access_key = assume_role_response['Credentials']['AccessKeyId']
    secret_key = assume_role_response['Credentials']['SecretAccessKey']
    session_token = assume_role_response['Credentials']['SessionToken']

    ce = boto3.client('ce',aws_access_key_id=access_key,aws_secret_access_key=secret_key,aws_session_token=session_token)

    request1 = {
        "TimePeriod" : {
            "Start": starting,
            "End": ending
        },
        "Granularity" : granularity,
        "GroupBy": [
            {
                "Type": "DIMENSION",
                "Key": "USAGE_TYPE"
            }
        ],
        "Metrics" : [ 'UnblendedCost', 'UsageQuantity' ]
    }
    response1 = ce.get_cost_and_usage(**request1)

    #Declare dataframe for cost
    df= pd.DataFrame({'Date': [''],
                      'Usage_Type': [''],
                      'Cost': [''] })

    # print date, cost
    for results in response1['ResultsByTime']:
        for groups in results['Groups']:
            df=df.append({'Date':results['TimePeriod']['Start'],'Usage_Type':groups['Keys'][0],'Cost':groups['Metrics']['UnblendedCost']['Amount']},ignore_index=True)
    df = df.drop(labels=0, axis=0)
    df.reset_index(drop=True,inplace=True)
    print(df)
    print("\n")

    token1=response1['NextPageToken']
    request2 = {
        "TimePeriod" : {
            "Start": starting,
            "End": ending
        },
        "Granularity" : granularity,
        "GroupBy": [
            {
                "Type": "DIMENSION",
                "Key": "USAGE_TYPE"
            }
        ],
        "Metrics" : [ 'UnblendedCost', 'UsageQuantity' ],
        "NextPageToken": token1
    }
    response2 = ce.get_cost_and_usage(**request2)
    for results in response2['ResultsByTime']:
        for groups in results['Groups']:
            df=df.append({'Date':results['TimePeriod']['Start'],'Usage_Type':groups['Keys'][0],'Cost':groups['Metrics']['UnblendedCost']['Amount']},ignore_index=True)
    print("**df after appending**")
    print(df)

    token2=response2['NextPageToken']
    request3 = {
        "TimePeriod" : {
            "Start": starting,
            "End": ending
        },
        "Granularity" : granularity,
        "GroupBy": [
            {
                "Type": "DIMENSION",
                "Key": "USAGE_TYPE"
            }
        ],
        "Metrics" : [ 'UnblendedCost', 'UsageQuantity' ],
        "NextPageToken": token2
    }
    response3 = ce.get_cost_and_usage(**request3)
    for results in response3['ResultsByTime']:
        for groups in results['Groups']:
            df=df.append({'Date':results['TimePeriod']['Start'],'Usage_Type':groups['Keys'][0],'Cost':groups['Metrics']['UnblendedCost']['Amount']},ignore_index=True)

    print("**final df**")
    print(df)
    print("\n")
    print("Saving data to excel")
    df.to_excel("output.xlsx")

    print("***Cleaning up low cost services")
    df['Cost'] = pd.to_numeric(df['Cost'])
    df=df.loc[df['Cost']>0.5]
    df.reset_index(drop=True,inplace=True)
    print(df)
    print("\n")

    group_df=df.groupby(['Usage_Type'],as_index=False).sum()
    print("***Total Cost for each Usage_Type")
    print(group_df)

    print("Sorted grouped df is:\n")
    group_df.sort_values(by='Cost',ascending=False, inplace=True)
    group_df.reset_index(drop=True,inplace=True)
    print(group_df)

    print("Top 8 Usage type:")
    topcost_df=group_df.head(8)
    print(topcost_df)
    top_usage_list=list(topcost_df['Usage_Type'])

    print("top_usage_list")
    print(top_usage_list)

    row = group_df.shape[0]
    print("row: ",row)
    others=row-8
    print("others: ",others)
    others_df=group_df.tail(others)
    print("others_df")
    print(others_df)
    others_df.reset_index(drop=True,inplace=True)
    others_list=list(others_df['Usage_Type'])
    print("Others list")
    print(others_list)
    df=df.replace(to_replace =others_list,value ="Others")
    print("***Printing Others DF")
    print(df)
    df.to_excel("others.xlsx")
    others_group_df=df.groupby(['Date','Usage_Type'],as_index=False).sum()
    others_group_df.to_excel("final.xlsx")

    #Plot Stacked-Bar Graph
    fig = px.bar(others_group_df, x="Date", y="Cost", color="Usage_Type",
                 title="Cost per Usage_Type", barmode = 'stack')
    fig.write_html("Usage_Type-Report.html")
    fig.write_image("Usage_Type-Report.png")

    #Declare dataframe for usage
    usage_df= pd.DataFrame({'Date': [''],
                            'Usage_Type': [''],
                            'Usage': [''] })

    # print date, usage
    """
    for results in response1['ResultsByTime']:
        for groups in results['Groups']:
            usage_df=usage_df.append({'Date':results['TimePeriod']['Start'],'Usage_Type':groups['Keys'][0],'Usage':groups['Metrics']['UsageQuantity']['Amount']},ignore_index=True)
    usage_df = usage_df.drop(labels=0, axis=0)
    usage_df.reset_index(drop=True,inplace=True)
    print(usage_df)
    """

if __name__ == "__main__":
    main(sys.argv[1:])
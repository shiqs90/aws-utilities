#Python script invoking get_cost_and_usage will be:

#!/usr/bin/python3
import sys, getopt
import boto3
import pandas as pd
import numpy as np
import plotly.express as px
from openpyxl.workbook import Workbook

#argumentList = sys.argv[1:]

def main(argv):
    starting = ''
    ending = ''
    granularity =''
    try:
        opts, args = getopt.getopt(argv,"s:e:g:",["start=","end=","granularity="])
    except getopt.GetoptError:
        print('get-cost-usage_linked-account.py -s 2022-03-07 -e 2022-05-07 -g DAILY')
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

    request = {
        'TimePeriod' : {
            'Start': starting,
            'End': ending
        },
        'Granularity' : granularity,
        "GroupBy": [
            {
                "Type": "DIMENSION",
                "Key": "LINKED_ACCOUNT"
            }
        ],
        "Metrics" : [ 'UnblendedCost', 'UsageQuantity' ]
    }

    response = ce.get_cost_and_usage(**request)

    #Declare dataframe for cost
    df= pd.DataFrame({'Date': [''],
                      'LinkedAccount': [''],
                      'Cost': [''] })

    # print date, cost
    for results in response['ResultsByTime']:
        for groups in results['Groups']:
            df=df.append({'Date':results['TimePeriod']['Start'],'LinkedAccount':groups['Keys'][0],'Cost':groups['Metrics']['UnblendedCost']['Amount']},ignore_index=True)
    df = df.drop(labels=0, axis=0)
    df.reset_index(drop=True,inplace=True)

    df['LinkedAccount'] = df['LinkedAccount'].replace(['122962809136','223876882329','345396902820','578469094242','666285982020','701759435715'],['Secret-Store',' .io','qa','alpha','dev','prod'])

    print("***Saving data to excel")
    df.to_excel("output.xlsx")
    print(df)
    print("\n")

    print("***Cleaning up low cost services")
    df['Cost'] = pd.to_numeric(df['Cost'])
    df=df.loc[df['Cost']>0.5]
    df.reset_index(drop=True,inplace=True)
    print(df)
    print("\n")

    bar_df=df.groupby(['LinkedAccount'],as_index=False).sum()
    print(bar_df)

    print("***Total Cost for each Linked Account")
    print(df['Cost'].sum())


    qa =df.loc[df['LinkedAccount'] == "qa"]
    print("***qa dataframe")
    print(qa)

    entire_df=df.loc[(df['LinkedAccount'] == "qa") | (df['LinkedAccount'] == "alpha") | (df['LinkedAccount'] == "dev") | (df['LinkedAccount'] == "prod") | (df['LinkedAccount'] == "Example.io") | (df['LinkedAccount'] == "Secret-Store")]
    print("Entire df")
    print(entire_df)

    #Plot Stacked-Bar Graph -Plotly
    fig = px.bar(entire_df, x="Date", y="Cost", color="LinkedAccount",
                 title="Cost per LinkedAccount", barmode = 'stack')
    fig.write_html("LinkedAccount-Report.html")
    fig.write_image("LinkedAccount-Report.png")

    #Declare dataframe for usage
    usage_df=pd.DataFrame({'Date': [''],
                           'LinkedAccount': [''],
                           'Usage': [''] })

    # print date, usage
    for results in response['ResultsByTime']:
        for groups in results['Groups']:
            usage_df=usage_df.append({'Date':results['TimePeriod']['Start'],'LinkedAccount':groups['Keys'][0],'Usage':groups['Metrics']['UsageQuantity']['Amount']},ignore_index=True)
    usage_df = usage_df.drop(labels=0, axis=0)
    usage_df.reset_index(drop=True,inplace=True)
    usage_df['LinkedAccount'] = usage_df['LinkedAccount'].replace(['122962809136','223876882329','345396902820','578469094242','666285982020','701759435715'],['Secret-Store','Example.io','qa','alpha','dev','prod'])
    print(usage_df)

if __name__ == "__main__":
    main(sys.argv[1:])

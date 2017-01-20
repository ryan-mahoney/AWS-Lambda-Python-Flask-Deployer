import boto3, sys, os, json
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-s', '--stage', dest='stage')
parser.add_option('-t', '--table', dest='table')
parser.add_option("-r", "--region", dest="region_name", default='us-east-1')
(options, args) = parser.parse_args()

# handle required fields
if not options.stage:
    parser.error('stage is required')

if not options.table:
    parser.error('table is required')

# get the service resource.
dynamodb = boto3.resource('dynamodb', region_name=options.region_name)

with open('/project/aws/dynamodb/' + options.table + '.json', 'r') as contentFile:
    content = contentFile.read()

tableDefinition = json.loads(content)
tableDefinition['TableName'] = options.stage + '_' + tableDefinition['TableName']

# create the DynamoDB table.
table = dynamodb.create_table(
    TableName=tableDefinition['TableName'],
    KeySchema=tableDefinition['KeySchema'],
    AttributeDefinitions=tableDefinition['AttributeDefinitions'],
    ProvisionedThroughput=tableDefinition['ProvisionedThroughput']
)

# wait until the table exists.
table.meta.client.get_waiter('table_exists').wait(TableName=tableDefinition['TableName'])

# print out some data about the table.
print(table.item_count)
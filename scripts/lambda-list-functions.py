import boto3, sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-r", "--region", dest="region_name", default='us-east-1')
(options, args) = parser.parse_args()

client = boto3.client('lambda', region_name=options.region_name)

response = client.list_functions()

if len(response['Functions']) < 1:
    print 'No functions in the region: ' + options.region_name
    sys.exit(0)

for function in response['Functions']:
    print function['FunctionName']

import boto3, sys
from optparse import OptionParser

parser = OptionParser()
parser.add_option("-r", "--region", dest="region_name", default='us-east-1')
(options, args) = parser.parse_args()

client = boto3.client('apigateway', region_name=options.region_name)

response = client.get_rest_apis()

if len(response['items']) < 1:
    print 'No restapis in the region: ' + options.region_name
    sys.exit(0)

for item in response['items']:
    print item

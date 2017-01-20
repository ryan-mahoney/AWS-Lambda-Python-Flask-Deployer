import boto3, sys, os
from optparse import OptionParser
import components.zipfolder as zipfolder

parser = OptionParser()
parser.add_option('-r', '--region', dest='region_name', default='us-east-1')
parser.add_option('-n', '--name', dest='function_name')
parser.add_option('-t', '--runtime', dest='runtime', default='python2.7')
parser.add_option('-i', '--role', dest='role')
parser.add_option('-j', '--handler', dest='handler')
parser.add_option('-d', '--description', dest='description', default='')
parser.add_option('-o', '--timeout', dest='timeout', default=30)
parser.add_option('-s', '--memory', dest='memory', default=128)
parser.add_option('-p', '--publish', dest='publish', default=True)
parser.add_option('-c', '--codepath', dest='codepath')
parser.add_option('-u', '--pip', dest='pip', default=False)
(options, args) = parser.parse_args()

# handle required fields
if not options.function_name:
    parser.error('name is required')

if not options.codepath:
    parser.error('codepath is required')

if not options.handler:
    parser.error('handler is required')

if not options.role:
    parser.error('role is required')

# install project dependencies
if options.pip:
    cmd = 'pip install -r ' + options.codepath + '/requirements.txt -t ' + options.codepath + '/dist-packages'
    os.system(cmd)

# make a lambda client
client = boto3.client('lambda', region_name=options.region_name)

# read the file data
zipdata = zipfolder.zip(options.codepath, None)

# see which functions already exist
response = client.list_functions()
for function in response['Functions']:
    # if it exists, update it
    if function['FunctionName'] == options.function_name:
        response = client.update_function_code(
            FunctionName=options.function_name,
            ZipFile=zipdata,
            Publish=options.publish
        )
        print('function already exists, updated')
        sys.exit(0)

response = client.create_function(
    FunctionName=options.function_name,
    Runtime=options.runtime,
    Role=options.role,
    Handler=options.handler,
    Code={
        'ZipFile': zipdata,
    },
    Description=options.description,
    Timeout=int(options.timeout),
    MemorySize=options.memory,
    Publish=options.publish
)

print response
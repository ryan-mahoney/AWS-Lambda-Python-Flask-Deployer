import boto3, sys, uuid, base64, re
from optparse import OptionParser

parser = OptionParser()
parser.add_option('-r', '--region', dest='region_name', default='us-east-1')
parser.add_option('-n', '--name', dest='name')
parser.add_option('-l', '--lambda', dest='lambda_name')
parser.add_option('-c', '--codepath', dest='codepath')
parser.add_option('-s', '--stage', dest='stage', default='test')
(options, args) = parser.parse_args()

if not options.name:
    parser.error('name is required')

if not options.lambda_name:
    parser.error('lambda is required')

if not options.codepath:
    parser.error('codepath is required')

# get resources from flask
resources = []
resourceMethods = {}
resourceIds = {}
resourceParentIds = {}
resourceContentTypeAdditional = {}
resourceOnlyResponseCode = {}
sys.path.append(options.codepath)
sys.path.append(options.codepath + '/dist-packages')
from app import app
for rule in app.url_map.iter_rules():

    # ignore default static path
    ruleStr = str(rule)
    if ruleStr == '/static/<path:filename>':
        continue

    # convert format of parameters
    ruleStr = re.sub('/\<[a-z]*\:', '{', ruleStr).replace('>', '}')
    resources.append(ruleStr)
    resourceMethods[ruleStr] = rule.methods

    # if custom content type is defined
    if rule.defaults is not None and 'contentType' in rule.defaults:
        resourceContentTypeAdditional[ruleStr] = rule.defaults['contentType']

    # if only one response code defined, useful for 302 redirects
    if rule.defaults is not None and 'responseCode' in rule.defaults:
        resourceOnlyResponseCode[ruleStr] = rule.defaults['responseCode']

resources = sorted(resources)

# fill in missing resources implied by existing route paths
for resource in resources:
    if resource.count('/') > 1:
        parts = resource[1:].split('/')
        pathPart = parts[-1]
        partPath = ''
        for part in parts:
            partPath = partPath + '/' + part
            if partPath not in resources:
                    resources.append(partPath)

resources = sorted(resources)


def getResourceParentId (resource):
    parts = resource[1:].split('/')
    count = len(parts)
    parent = parts[0:-1]
    if len(parent) == 0:
        return resourceIds['/']
    else:
        return resourceIds['/' + '/'.join(parent)]


def getResourceId (restApiId, path):
    respourceParentId = getResourceParentId(path)
    pathPart = path[1:].split('/')[-1]
    resourceResp = apiClient.create_resource(
        restApiId=restApiId,
        parentId=respourceParentId,
        pathPart=pathPart
    )
    resourceIds[path] = resourceResp['id']
    return resourceResp


# template mappings for method integrations
POST_TEMPLATE_MAPPING = '''#set($rawPostData = $input.path("$"))
{
  "body" : "$util.base64Encode($input.body)",
  "headers": {
    #foreach($header in $input.params().header.keySet())
    "$header": "$util.escapeJavaScript($input.params().header.get($header))" #if($foreach.hasNext),#end

    #end
  },
  "method": "$context.httpMethod",
  "params": {
    #foreach($param in $input.params().path.keySet())
    "$param": "$util.escapeJavaScript($input.params().path.get($param))" #if($foreach.hasNext),#end

    #end
  },
  "stage": "$context.stage",
  "path": "$context.resourcePath",
  "query": {
    #foreach($queryParam in $input.params().querystring.keySet())
    "$queryParam": "$util.escapeJavaScript($input.params().querystring.get($queryParam))" #if($foreach.hasNext),#end

    #end
  }
}'''

FORM_ENCODED_TEMPLATE_MAPPING = '''
{
  "body" : "$util.base64Encode($input.body)",
  "headers": {
    #foreach($header in $input.params().header.keySet())
    "$header": "$util.escapeJavaScript($input.params().header.get($header))" #if($foreach.hasNext),#end

    #end
  },
  "method": "$context.httpMethod",
  "params": {
    #foreach($param in $input.params().path.keySet())
    "$param": "$util.escapeJavaScript($input.params().path.get($param))" #if($foreach.hasNext),#end

    #end
  },
  "stage": "$context.stage",
  "path": "$context.resourcePath",
  "query": {
    #foreach($queryParam in $input.params().querystring.keySet())
    "$queryParam": "$util.escapeJavaScript($input.params().querystring.get($queryParam))" #if($foreach.hasNext),#end

    #end
  }
}'''

RESPONSE_TEMPLATE = '''#set($inputRoot = $input.path('$'))
$inputRoot.Content'''
ERROR_RESPONSE_TEMPLATE = '''#set($inputRoot = $input.path('$.errorMessage'))
$util.base64Decode($inputRoot)'''
REDIRECT_RESPONSE_TEMPLATE = ''

def selectionPattern(statusCode):
    pattern = ''
    if statusCode == '301':
        pattern = 'https://.*|/.*'
    elif statusCode == '302':
        pattern = 'https://.*|/.*|/.*'
    elif statusCode != '200':
        pattern = base64.b64encode("<!DOCTYPE html>" + str(statusCode)) + '.*'
        pattern = pattern.replace('+', r"\+")

    return pattern

# determine amazon account id
accountId = boto3.client('iam').get_user()['User']['Arn'].split(':')[4]

# get a boto clients in the specified region
#boto3.set_stream_logger('botocore')
awsRegion = options.region_name
apiClient = boto3.client('apigateway', region_name=awsRegion)
lambdaClient = boto3.client('lambda', region_name=awsRegion)
lambdaVersion = lambdaClient.meta.service_model.api_version

# get details about existing lambda function
lambdaResponse = lambdaClient.list_functions()
lambdaFunction = None
for lambdaItem in lambdaResponse['Functions']:
    if lambdaItem['FunctionName'] == options.lambda_name:
        lambdaFunction = lambdaItem
        break

if lambdaFunction is None:
    print 'unknown lambda function: ' + options.lambda_name
    sys.exit(0)

# see what apis already exists
gatewayResponse = apiClient.get_rest_apis()

for item in gatewayResponse['items']:
    if item['name'] == options.name:
        print 'this restapi already exists'

        resourceResp = apiClient.get_resources(
            restApiId=item['id']
        )
        for resource in resourceResp['items']:
            print resource
            if resource['path'] == '/':
                parentId = resource['id']

        print 'Parent: ' + parentId

        sys.exit(0)

# create api
restResponse = apiClient.create_rest_api(name=options.name)
print 'rest api created: ' + restResponse['name']

# create http method for default resource
resourceResp = apiClient.get_resources(restApiId=restResponse['id'])
defaultResourceId = resourceResp['items'][0]['id']
resourceIds['/'] = defaultResourceId
httpMethods = ['DELETE', 'GET', 'HEAD', 'OPTIONS', 'PATCH', 'POST', 'PUT']
integrationResponseCodes = [200, 201, 301, 302, 400, 401, 403, 404, 500]
integrationContentTypes = ['text/html']
methodResponseCodes = [200, 201, 301, 302, 400, 401, 403, 404, 500]
methodContentTypes = ['text/html']
methodHeaderTypes = ['Content-Type', 'Location', 'Status', 'X-Frame-Options', 'Set-Cookie']

for resourcePath in resources:

    # add resource if necessary
    if resourcePath == '/':
        resourceId = defaultResourceId
    else:
        # create resource
        resourceResp = getResourceId(restResponse['id'], resourcePath)
        resourceId = resourceResp['id']

    # add every method for every resource
    if resourcePath not in resourceMethods:
        continue
    for method in resourceMethods[resourcePath]:
        methodResp = apiClient.put_method(
            restApiId=restResponse['id'],
            resourceId=resourceId,
            httpMethod=method,
            authorizationType='NONE',
            apiKeyRequired=False
        )
        print 'method created: ' + resourcePath + ':' + method

        # setup request templates
        requestTemplates = {
            'application/json': POST_TEMPLATE_MAPPING,
            'application/x-www-form-urlencoded': POST_TEMPLATE_MAPPING,
            'multipart/form-data': FORM_ENCODED_TEMPLATE_MAPPING
        }

        # support additional non-standard content types
        if resourcePath in resourceContentTypeAdditional:
            requestTemplates[resourceContentTypeAdditional[resourcePath]] = POST_TEMPLATE_MAPPING

        # create lambda integration
        uri = 'arn:aws:apigateway:' + awsRegion + ':lambda:path/' + lambdaVersion + '/functions/' + lambdaFunction['FunctionArn'] + '/invocations'
        integrationResp = apiClient.put_integration(
            restApiId=restResponse['id'],
            resourceId=resourceId,
            httpMethod=method,
            type="AWS",
            integrationHttpMethod='POST',
            uri=uri,
            requestTemplates=requestTemplates
        )
        print 'integration created: ' + resourcePath + ':' + method

        # method response
        for response in methodResponseCodes:
            statusCode = str(response)

            responseParameters = {'method.response.header.' + headerType: False for headerType in methodHeaderTypes}
            responseModels = {contentType: 'Empty' for contentType in methodContentTypes}

            method_response = apiClient.put_method_response(
                restApiId=restResponse['id'],
                resourceId=resourceId,
                httpMethod=method,
                statusCode=statusCode,
                responseParameters=responseParameters,
                responseModels=responseModels
            )

            print 'method response: ' + resourcePath + ':' + method + ':' + statusCode

        # integration response
        for response in integrationResponseCodes:
            statusCode = str(response)

            responseParameters = {'method.response.header.' + headerType: 'integration.response.body.' + headerType for headerType in methodHeaderTypes}

            if statusCode == '200':
                responseTemplates = {contentType: RESPONSE_TEMPLATE for contentType in integrationContentTypes}
            elif statusCode in ['301', '302']:
                responseTemplates = {contentType: REDIRECT_RESPONSE_TEMPLATE for contentType in integrationContentTypes}
                responseParameters['method.response.header.Location'] = 'integration.response.body.errorMessage'
            else:
                responseTemplates = {contentType: ERROR_RESPONSE_TEMPLATE for contentType in integrationContentTypes}

            integration_response = apiClient.put_integration_response(
                restApiId=restResponse['id'],
                resourceId=resourceId,
                httpMethod=method,
                statusCode=statusCode,
                selectionPattern=selectionPattern(statusCode),
                responseParameters=responseParameters,
                responseTemplates=responseTemplates
            )

            print 'integration response: ' + resourcePath + ':' + method + ':' + statusCode

# create permission on the lambda function
permissionResp = lambdaClient.add_permission(
    FunctionName=lambdaFunction['FunctionName'],
    StatementId=uuid.uuid4().hex,
    Action="lambda:InvokeFunction",
    Principal="apigateway.amazonaws.com"
)
print 'permission created'

# deploy end point
apiClient.create_deployment(
    restApiId=restResponse['id'],
    stageName=options.stage,
)
print 'api deployed'
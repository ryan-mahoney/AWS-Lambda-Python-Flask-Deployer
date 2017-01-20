import uuid

resources = [
    '/',
    '/api/harvest',
    '/api/status',
    '/x/y/z'
]

# holder of id's assigned by amazon
resourceIds = {}
resourceParentIds = {}

def getResourceId (path):
    return uuid.uuid4()

def getResourceParentId (path):
    parts = resource[1:].split('/')
    count = len(parts)
    parent = parts[0:-1]
    if len(parent) == 0:
        return resourceIds['/']
    else:
        return resourceIds['/' + '/'.join(parent)]

# fill in missing resources
for resource in resources:
    print resource
    if resource.count('/') > 1:
        parts = resource[1:].split('/')
        pathPart = parts[-1]
        partPath = ''
        for part in parts:
            partPath = partPath + '/' + part
            if partPath not in resources:
                    resources.append(partPath)
resources = sorted(resources)


# determine parent id for each resource
for resource in resources:
    resourceIds[resource] = getResourceId(resource)
    resourceParentIds[resource] = getResourceParentId(resource)
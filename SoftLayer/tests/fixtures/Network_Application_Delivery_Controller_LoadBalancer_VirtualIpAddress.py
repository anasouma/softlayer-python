getBillingItem = {'id': 21370814 }
getVirtualServers = [
    {
        'port': 10004,
        'allocation': 100,
        'serviceGroups': [
            {
                'services': [
                    {
                        'status': 'DOWN',
                        'enabled': 1,
                        'ipAddressId': 13010178,
                        'id': 83574,
                        'groupReferences': [
                            {
                                'serviceId': 83574,
                                'serviceGroupId': 52232,
                                'weight': 4
                            }
                        ],
                        'healthChecks': [
                            {
                                'healthCheckTypeId': 2,
                                'id': 110380
                            }
                        ],
                        'port': 85
                    }
                ],
                'routingTypeId': 3,
                'id': 52232,
                'timeout': '',
                'routingMethodId': 10
            }
        ],
        'id': 51112
    }
]
editObject = {}
getObject = {
             'virtualServers': getVirtualServers }
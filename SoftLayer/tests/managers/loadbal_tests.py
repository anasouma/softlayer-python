"""
    SoftLayer.tests.managers.loadbal_tests
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    :license: MIT, see LICENSE for more details.
"""
from SoftLayer import LoadBalancerManager
from SoftLayer.tests import unittest, FixtureClient
from SoftLayer.tests.fixtures import (Account, Billing_Item)
from mock import ANY


class LoadBalancerTests(unittest.TestCase):

    def setUp(self):
        self.client = FixtureClient()
        self.lb_mgr = LoadBalancerManager(self.client)

    def test_get_lb_pkgs(self):
        self.lb_mgr.get_lb_pkgs()
        f = self.client['Product_Package'].getItems
        _filter = {
            'items': {
                'description': {
                    'operation': '*= Load Balancer'
                    }
                }
            }
        f.assert_called_once_with(filter=_filter, id=0)

    def test_get_ip_address(self):
        self.lb_mgr.get_ip_address()
        f = self.client['Network_Subnet_IpAddress'].getByIpAddress
        f.assert_called_once()

    def test_get_hc_types(self):
        self.lb_mgr.get_hc_types()
        f = self.client['Network_Application_Delivery_Controller_'
                        'LoadBalancer_Health_Check_Type'].getAllObjects
        f.assert_called_once()

    def test_get_routing_methods(self):
        self.lb_mgr.get_routing_methods()
        f = self.client['Network_Application_Delivery_Controller_'
                        'LoadBalancer_Routing_Method'].getAllObjects
        f.assert_called_once()

    def test_get_location(self):
        id1 = self.lb_mgr.get_location('sjc01')
        f = self.client['Location'].getDataCenters
        f.assert_called_once()
        self.assertEqual(id1, 168642)

        id2 = self.lb_mgr.get_location('dal05')
        f = self.client['Location'].getDataCenters
        f.assert_called_once()
        self.assertEqual(id2, 'FIRST_AVAILABLE')

    def test_get_routing_types(self):
        self.lb_mgr.get_routing_types()
        f = self.client['Network_Application_Delivery_Controller_'
                        'LoadBalancer_Routing_Type'].getAllObjects
        f.assert_called_once()

    def test_cancel_lb(self):
        loadbal_id = 6327
        billing_item_id = 21370814
        result = self.lb_mgr.cancel_lb(loadbal_id)
        f = self.client['Billing_Item'].cancelService
        f.assert_called_once_with(id=billing_item_id)
        self.assertEqual(result, Billing_Item.cancelService)

    def test_add_local_lb(self):
        price_id = 6327
        datacenter = 'sjc01'
        self.lb_mgr.add_local_lb(price_id, datacenter)

        _package = {
            'complexType': 'SoftLayer_Container_Product_Order_Network_'
                           'LoadBalancer',
            'quantity': 1,
            'packageId': 0,
            "location": 168642,
            'prices': [{'id': price_id}]
        }
        f = self.client['Product_Order'].placeOrder
        f.assert_called_once_with(_package)

    def test_get_local_lbs(self):
        self.lb_mgr.get_local_lbs()
        call = self.client['Account'].getAdcLoadBalancers
        mask = ('mask[loadBalancerHardware[datacenter],ipAddress]')
        call.assert_called_once_with(mask=mask)

    def test_get_local_lb(self):
        lb_id = 12345
        self.lb_mgr.get_local_lb(lb_id)
        call = self.client['Network_Application_Delivery_Controller_'
                           'LoadBalancer_VirtualIpAddress'].getObject

        mask = ('mask[loadBalancerHardware[datacenter], '
                'ipAddress, virtualServers[serviceGroups'
                '[routingMethod,routingType,services'
                '[healthChecks[type], groupReferences,'
                ' ipAddress]]]]')
        call.assert_called_once_with(id=lb_id, mask=mask)

    def test_delete_service(self):
        lb_id = 12345
        service_id = 1234
        self.lb_mgr.delete_service(lb_id, service_id)
        call = self.client['Network_Application_Delivery_Controller_'
                          'LoadBalancer_Service'].deleteObject

        call.assert_called_once_with(id=service_id)

    def test_delete_service_group(self):
        lb_id = 12345
        service_group = 1234
        self.lb_mgr.delete_service_group(lb_id, service_group)
        call = self.client['Network_Application_Delivery_Controller_'
                          'LoadBalancer_VirtualServer'].deleteObject

        call.assert_called_once_with(id=service_group)

    def test_toggle_service_status(self):
        lb_id = 12345
        service_id = 1234
        self.lb_mgr.toggle_service_status(lb_id, service_id)
        call = self.client['Network_Application_Delivery_Controller_'
                          'LoadBalancer_Service'].toggleStatus

        call.assert_called_once_with(id=service_id)

    def test_edit_service(self):
        loadbal_id = 12345
        service_id = 83574
        ip_address = {'id': 123456}
        port = 80
        enabled = 1
        hc_type = 21
        weight = 1
        self.lb_mgr.edit_service(loadbal_id, service_id, ip_address,
                                 port, enabled, hc_type, weight)
        call = self.client['Network_Application_Delivery_Controller_'
                          'LoadBalancer_VirtualIpAddress'].getVirtualServers
        _filter = {'virtualServers': {'serviceGroups': {'services': {'id': {'operation': 83574}}}}}
        mask = 'mask[serviceGroups[services[groupReferences,healthChecks]]]'
        call.assert_called_once_with(filter=_filter, mask=mask, id=loadbal_id)

        call = self.client['Network_Application_Delivery_Controller_'
                          'LoadBalancer_VirtualIpAddress'].editObject

        template = [
        {
            'port': 10004,
            'allocation': 100,
            'serviceGroups': [
                {
                    'services': [
                        {
                            'status': 'DOWN',
                            'enabled': enabled,
                            'ipAddressId': ip_address['id'],
                            'id': 83574,
                            'groupReferences': [
                                {
                                    'serviceId': 83574,
                                    'serviceGroupId': 52232,
                                    'weight': weight
                                }
                            ],
                            'healthChecks': [
                                {
                                    'healthCheckTypeId': hc_type,
                                    'id': 110380
                                }
                            ],
                            'port': port
                        }
                    ],
                    'routingTypeId': 3,
                    'id': 52232,
                    'timeout': '',
                    'routingMethodId': 10
                }
            ],
            'id': 51112
        }]
        call.assert_called_once_with(template={'virtualServers': template}, id=loadbal_id)

    def test_add_service(self):
        loadbal_id = 12345
        group_id = 52232
        ip_address = {'id': 123456}
        port = 80
        enabled = 1
        hc_type = 21
        weight = 1
        self.lb_mgr.add_service(loadbal_id, group_id, ip_address,
                                 port, enabled, hc_type, weight)
        call = self.client['Network_Application_Delivery_Controller_'
                          'LoadBalancer_VirtualIpAddress'].getObject

        call.assert_called_once_with(id=loadbal_id)

        call = self.client['Network_Application_Delivery_Controller_'
                          'LoadBalancer_VirtualIpAddress'].editObject

        template = [
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
                                    'weight': 1
                                }
                            ],
                            'healthChecks': [
                                {
                                    'healthCheckTypeId': 2,
                                    'id': 110380
                                }
                            ],
                            'port': 85
                        },
                            {
                            'enabled': enabled,
                            'port': port,
                            'ipAddressId': ip_address['id'],
                            'healthChecks': [
                                {
                                    'healthCheckTypeId': hc_type
                                }
                            ],
                            'groupReferences': [
                                {
                                    'weight': weight
                                }
                            ]
                            }
                    ],
                    'routingTypeId': 3,
                    'id': 52232,
                    'timeout': '',
                    'routingMethodId': 10
                }
            ],
            'id': 51112
        }]
        call.assert_called_once_with(template=template, id=loadbal_id)

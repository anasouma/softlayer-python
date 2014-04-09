"""
usage: sl loadbal [<command>] [<args>...] [options]

LoadBalancer management

The available commands are:

  cancel           Cancel an existing load balancer
  create           Create a new load balancer
  create-options   Lists the different packages for load balancers
  detail           Provide details about a particular load balancer
  group-add        Add a new service group in the load balancer
  group-delete     Delete a service group from the load balancer
  group-edit       Edit the properties of a service group
  group-reset      Resets all the connections on a service group
  health-checks    List the different health check values
  list             List active load balancers (--local | --global)
  routing-methods  List supported routing methods
  routing-types    List supported routing types
  service-add      Add a service to an existing service group
  service-delete   Delete an existing service
  service-edit     Edit an existing service
  service-toggle   Toggle the status of the service

"""
# :license: MIT, see LICENSE for more details.

from SoftLayer import LoadBalancerManager
from SoftLayer.CLI import (CLIRunnable, Table, resolve_id,
                           confirm, KeyValueTable)
from SoftLayer.CLI.helpers import CLIAbort


def get_local_lbs_table(load_balancers):
    """ Helper package to format the local load balancers into a table.

    :param dict load_balancers: A dictionary representing the load_balancers
    :returns: A table containing the local load balancers
    """
    t = Table(['ID',
               'VIP Address',
               'Location',
               'SSL Offload',
               'Connections/second',
               'Type'])

    t.align['VIP Address'] = 'r'
    t.align['Location'] = 'r'
    t.align['Connections/second'] = 'r'
    t.align['Connections/second'] = 'r'
    t.align['Type'] = 'r'

    for load_balancer in load_balancers:
        sslSupport = 'Not Supported'
        if load_balancer['sslEnabledFlag']:
            if load_balancer['sslActiveFlag']:
                sslSupport = 'On'
            else:
                sslSupport = 'Off'
        lb_type = 'Standard'
        if load_balancer['dedicatedFlag']:
            lb_type = 'Dedicated'
        elif load_balancer['highAvailabilityFlag']:
            lb_type = 'HA'
        t.add_row([
            'local:%s' % load_balancer['id'],
            load_balancer['ipAddress']['ipAddress'],
            load_balancer['loadBalancerHardware'][0]['datacenter']['name'],
            sslSupport,
            load_balancer['connectionLimit'],
            lb_type
        ])
    return t


def get_local_lb_table(load_balancer):
    """ Helper package to format the local loadbal details into a table.

    :param dict load_balancer: A dictionary representing the loadbal
    :returns: A table containing the local loadbal details
    """
    t = KeyValueTable(['Name', 'Value'])
    t.align['Name'] = 'l'
    t.align['Value'] = 'l'
    t.add_row(['General properties', '----------'])
    t.add_row([' ID', 'local:%s' % load_balancer['id']])
    t.add_row([' IP Address', load_balancer['ipAddress']['ipAddress']])
    t.add_row([' Datacenter',
               load_balancer['loadBalancerHardware'][0]['datacenter']['name']])
    t.add_row([' Connections limit', load_balancer['connectionLimit']])
    t.add_row([' Dedicated', load_balancer['dedicatedFlag']])
    t.add_row([' HA', load_balancer['highAvailabilityFlag']])
    t.add_row([' SSL Enabled', load_balancer['sslEnabledFlag']])
    t.add_row([' SSL Active', load_balancer['sslActiveFlag']])
    index0 = 1
    for virtual_server in load_balancer['virtualServers']:
        t.add_row(['Service group %s' % index0,
                   '**************'])
        index0 += 1
        t2 = Table(['Service group ID', 'Port', 'Allocation', 'Routing type',
                    'Routing Method'])

        for group in virtual_server['serviceGroups']:
            t2.add_row([
                '%s:%s' % (load_balancer['id'], virtual_server['id']),
                virtual_server['port'],
                '%s %%' % virtual_server['allocation'],
                '%s:%s' % (group['routingTypeId'],
                           group['routingType']['name']),
                '%s:%s' % (group['routingMethodId'],
                           group['routingMethod']['name'])
            ])

            t.add_row([' Group Properties', t2])

            t3 = Table(['Service_ID', 'IP Address', 'Port', 'Health Check',
                        'Weight', 'Enabled', 'Status'])
            for service in group['services']:
                healthCheck = service['healthChecks'][0]
                t3.add_row([
                    '%s:%s' % (load_balancer['id'], service['id']),
                    service['ipAddress']['ipAddress'],
                    service['port'],
                    '%s:%s' % (healthCheck['healthCheckTypeId'],
                               healthCheck['type']['name']),
                    service['groupReferences'][0]['weight'],
                    service['enabled'],
                    service['status']
                ])
            t.add_row([' Services', t3])
    return t


class LoadBalancerList(CLIRunnable):
    """
usage: sl loadbal list [options]

List active local load balancers

"""
    action = 'list'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)

        load_balancers = mgr.get_local_lbs()
        return get_local_lbs_table(load_balancers)


class LoadBalancerHealthChecks(CLIRunnable):
    """
usage: sl loadbal health-check-types [options]

List load balancer service health check types that can be used
"""
    action = 'health-check-types'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)

        hc_types = mgr.get_hc_types()
        t = KeyValueTable(['ID', 'Name'])
        t.align['ID'] = 'l'
        t.align['Name'] = 'l'
        t.sortby = 'ID'
        for hc_type in hc_types:
            t.add_row([hc_type['id'], hc_type['name']])
        return t


class LoadBalancerRoutingMethods(CLIRunnable):
    """
usage: sl loadbal routing-methods [options]

List load balancers routing methods that can be used
"""
    action = 'routing-methods'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)

        routing_methods = mgr.get_routing_methods()
        t = KeyValueTable(['ID', 'Name'])
        t.align['ID'] = 'l'
        t.align['Name'] = 'l'
        t.sortby = 'ID'
        for routing_method in routing_methods:
            t.add_row([routing_method['id'], routing_method['name']])
        return t


class LoadBalancerRoutingTypes(CLIRunnable):
    """
usage: sl loadbal routing-types [options]

List load balancers routing types that can be used
"""
    action = 'routing-types'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)

        routing_types = mgr.get_routing_types()
        t = KeyValueTable(['ID', 'Name'])
        t.align['ID'] = 'l'
        t.align['Name'] = 'l'
        t.sortby = 'ID'
        for routing_type in routing_types:
            t.add_row([routing_type['id'], routing_type['name']])
        return t


class LoadBalancerDetails(CLIRunnable):
    """
usage: sl loadbal detail <identifier> [options]

Get Load balancer details

"""
    action = 'detail'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)

        input_id = args.get('<identifier>')

        key_value = input_id.split(':')
        loadbal_id = int(key_value[1])

        load_balancer = mgr.get_local_lb(loadbal_id)
        return get_local_lb_table(load_balancer)


class LoadBalancerCancel(CLIRunnable):
    """
usage: sl loadbal cancel <identifier> [options]

Cancels an existing load_balancer
Options:
  --really     Whether to skip the confirmation prompt

"""
    action = 'cancel'
    options = ['really']

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')

        key_value = input_id.split(':')
        loadbal_id = int(key_value[1])

        if args['--really'] or confirm("This action will cancel a load "
                                       "balancer. Continue?"):
            mgr.cancel_lb(loadbal_id)
            return 'Load Balancer with id %s is being cancelled!' % loadbal_id
        else:
            raise CLIAbort('Aborted.')


class LoadBalancerServiceDelete(CLIRunnable):
    """
usage: sl loadbal service-delete <identifier> [options]

Cancels an existing load_balancer service
Options:
   --really     Whether to skip the confirmation prompt

"""
    action = 'service-delete'
    options = ['really']

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')

        key_value = input_id.split(':')
        loadbal_id = int(key_value[0])
        service_id = int(key_value[1])

        if args['--really'] or confirm("This action will cancel a service "
                                       "from your load balancer. Continue?"):
            mgr.delete_service(loadbal_id, service_id)
            return 'Load balancer service %s is being cancelled!' % input_id
        else:
            raise CLIAbort('Aborted.')


class LoadBalancerServiceToggle(CLIRunnable):
    """
usage: sl loadbal service-toggle <identifier> [options]

Toggle the status of an existing load_balancer service
Options:
  --really     Whether to skip the confirmation prompt

"""
    action = 'service-toggle'
    options = ['really']

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')

        key_value = input_id.split(':')
        loadbal_id = int(key_value[0])
        service_id = int(key_value[1])

        if args['--really'] or confirm("This action will toggle the service "
                                       "status on the service. Continue?"):
            mgr.toggle_service_status(loadbal_id, service_id)
            return 'Load balancer service %s status updated!' % input_id
        else:
            raise CLIAbort('Aborted.')


class LoadBalancerServiceEdit(CLIRunnable):
    """
usage: sl loadbal service-edit <identifier> [options]

Enable an existing load_balancer service
Options:
--enabled=ENABLED  Set to 1 to enable the service, or 0 to disable
--port=PORT        Change the value of the port
--weight=WEIGHT    Change the weight of the service
--hc_type=HCTYPE   Change the health check type
--ip=IP            Change the IP of the service

"""
    action = 'service-edit'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')

        key_value = input_id.split(':')
        loadbal_id = int(key_value[0])
        service_id = int(key_value[1])

        # check if any input is provided
        if not (args['--ip'] or args['--enabled'] or args['--weight']
                or args['--port'] or args['--hc_type']):
            return 'At least one property is required to be changed!'

        # check if the IP is valid
        ip_address = None
        if args['--ip']:
            ip_address = mgr.get_ip_address(args['--ip'])
            if not ip_address:
                return 'Provided IP address is not valid!'

        mgr.edit_service(loadbal_id,
                         service_id,
                         enabled=int(args.get('--enabled') or -1),
                         port=int(args.get('--port') or -1),
                         weight=int(args.get('--weight') or -1),
                         hc_type=int(args.get('--hc_type') or -1),
                         ip_address=ip_address)
        return 'Load balancer service %s is being modified!' % input_id


class LoadBalancerServiceAdd(CLIRunnable):
    """
usage: sl loadbal service-add <identifier> --ip=IP --port=PORT --weight=WEIGHT
                              --hc_type=HCTYPE --enabled=ENABLED [options]

Adds a new load_balancer service
Required:
--enabled=ENABLED  Set to 1 to enable the service, 0 to disable [default: 1].
--port=PORT        Set to the desired port value [default: 80].
--weight=WEIGHT    Set to the desired weight  value [default: 1].
--hc_type=HCTYPE   Set to the desired health check value [default: 21].
--ip=IP            Set to the desired IP value.

"""
    action = 'service-add'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')

        key_value = input_id.split(':')
        loadbal_id = int(key_value[0])
        group_id = int(key_value[1])

        # check if the IP is valid
        ip_address = None
        if args['--ip']:
            ip_address = mgr.get_ip_address(args['--ip'])
            if not ip_address:
                return 'Provided IP address is not valid!'

        mgr.add_service(loadbal_id,
                        group_id,
                        enabled=args.get('--enabled'),
                        port=args.get('--port'),
                        weight=args.get('--weight'),
                        hc_type=args.get('--hc_type'),
                        ip_address=ip_address)
        return 'Load balancer service is being added!'


class LoadBalancerServiceGroupDelete(CLIRunnable):
    """
usage: sl loadbal group-delete <identifier> [options]

Cancels an existing load_balancer service group
Options:
  --really     Whether to skip the confirmation prompt

"""
    action = 'group-delete'
    options = ['really']

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')

        key_value = input_id.split(':')
        loadbal_id = int(key_value[0])
        group_id = int(key_value[1])

        if args['--really'] or confirm("This action will cancel a service"
                                       " group. Continue?"):
            mgr.delete_service_group(loadbal_id, group_id)
            return 'Service group %s is being deleted!' % input_id
        else:
            raise CLIAbort('Aborted.')


class LoadBalancerServiceGroupEdit(CLIRunnable):
    """
usage: sl loadbal group-edit <identifier> [options]

Edits an existing load_balancer service group
Required:
--allocation=ALLOC       Change the allocated number of connections
--port=PORT              Change the port
--routing_type=TYPE      Change the port routing type
--routing_method=METHOD  Change the routing method

"""
    action = 'group-edit'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')

        key_value = input_id.split(':')
        loadbal_id = int(key_value[0])
        group_id = int(key_value[1])
        routing_type = args.get('--routing_type')
        routing_method = args.get('--routing_method')

        mgr.edit_service_group(loadbal_id,
                               group_id,
                               allocation=int(args.get('--allocation') or -1),
                               port=int(args.get('--port') or 0),
                               routing_type=int(routing_type or 0),
                               routing_method=int(routing_method or 0))

        return 'Load balancer service group %s is being updated!' % input_id


class LoadBalancerServiceGroupReset(CLIRunnable):
    """
usage: sl loadbal group-reset <identifier> [options]

Resets the connections on a certain service group

"""
    action = 'group-reset'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')

        key_value = input_id.split(':')
        loadbal_id = int(key_value[0])
        group_id = int(key_value[1])

        mgr.reset_service_group(loadbal_id, group_id)
        return 'Load balancer service group connections are being reset!'


class LoadBalancerServiceGroupAdd(CLIRunnable):
    """
usage: sl loadbal group-add <identifier> --allocation=ALLOC --port=PORT --routing_type=TYPE --routing_method=METHOD [options]

Adds a new load_balancer service
Required:
--allocation=ALLOC       The % of connections that will be allocated
--port=PORT              The virtual port number for the group
--routing_type=TYPE      The routing type for the group
--routing_method=METHOD  The routing method for the group

"""
    action = 'group-add'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')
        key_value = input_id.split(':')

        if key_value[0] != 'local':
            return 'This CLI is only valid for local load balancers'

        loadbal_id = int(key_value[1])

        mgr.add_service_group(loadbal_id,
                              allocation=int(args.get('--allocation')),
                              port=int(args.get('--port')),
                              routing_type=int(args.get('--routing_type')),
                              routing_method=int(args.get('--routing_method')))

        return 'Load balancer service group is being added!'


class LoadBalancerCreate(CLIRunnable):
    """
usage: sl loadbal create <identifier> (--datacenter=DC) [options]

Adds a load_balancer given the billing id returned from create-options

Required:
  -d, --datacenter=DC    Datacenter shortname (sng01, dal05, ...)
                         Note: Omitting this value defaults to the first
                           available datacenter

Options:
  --really     Whether to skip the confirmation prompt
"""
    action = 'create'
    options = ['really']

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = resolve_id(
            mgr.resolve_ids, args.get('<identifier>'), 'load_balancer')
        if not confirm("This action will incur charges on your account. "
                       "Continue?"):
            raise CLIAbort('Aborted.')
        mgr.add_local_lb(input_id, datacenter=args['--datacenter'])
        return "Load balancer is being created!"


class CreateOptionsLoadBalancer(CLIRunnable):
    """
usage: sl loadbal create-options

Output available options when adding a new load balancer

"""
    action = 'create-options'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)

        t = Table(['id', 'capacity', 'description', 'price'])

        t.sortby = 'price'
        t.align['price'] = 'r'
        t.align['capacity'] = 'r'
        t.align['id'] = 'r'

        packages = mgr.get_lb_pkgs()

        for package in packages:
            t.add_row([
                package['prices'][0]['id'],
                package.get('capacity'),
                package['description'],
                format(float(package['prices'][0]['recurringFee']), '.2f')
            ])

        return t

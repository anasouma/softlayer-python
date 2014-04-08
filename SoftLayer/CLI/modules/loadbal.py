"""
usage: sl loadbal [<command>] [<args>...] [options]

LoadBalancer management

The available commands are:

Local & global load balancer
  cancel           Cancel an existing load balancer
  create           Create a new load balancer
  create-options   Lists the different packages for load balancers
  detail           Provide details about a particular load balancer
  health-checks    List the different health check values
  list             List active load balancers (--local | --global)
  routing-methods  List supported routing methods
  routing-types    List supported routing types

Local load balancer

  group_add        Add a new service group in the load balancer
  group-delete     Delete a service group from the load balancer
  group-edit       Edit the properties of a service group
  group-reset      Resets all the connections on a service group
  service-add      Add a service to an existing service group
  service-delete   Delete an existing service
  service-edit     Edit an existing service
  service-toggle   Toggle the status of the service

Global load balancer

  host-add        Add a new service group in the load balancer
  host-delete     Add a new service group in the load balancer
  host-cancel     Add a new service group in the load balancer

"""
# :license: MIT, see LICENSE for more details.

from SoftLayer import LoadBalancerManager
from SoftLayer.CLI import (CLIRunnable, Table, resolve_id,
                           confirm, KeyValueTable)
from SoftLayer.CLI.helpers import CLIAbort


def get_global_lb_table(load_balancer):
    """ Helper package to display the detail of a global loadbal.

    :param dict load_balancer: A dictionary representing a single loadbal
    :returns: A table containing the global load balancers
    """

    t = KeyValueTable(['Name', 'Value'])
    t.align['Name'] = 'l'
    t.align['Value'] = 'l'
    t.add_row(['General properties', '----------'])
    t.add_row([' ID', 'global:%s' % load_balancer['id']])
    t.add_row([' hostname', load_balancer['hostname']])
    t.add_row([' Fallback IP', load_balancer.get('fallbackIp') or 'None'])
    t.add_row([' Method', load_balancer['loadBalanceType']['name']])
    t.add_row([' Connections/sec', load_balancer['connectionsPerSecond']])

    t2 = Table(['ID', 'Destination IP', 'Health Check', 'Port', 'Location',
                'Enabled', 'Hits', 'Status'])
    for destination in load_balancer['hosts']:
        t2.add_row([
            '%s:%s' % (load_balancer['id'], destination['id']),
            destination['destinationIp'],
            destination['healthCheck'],
            destination['destinationPort'],
            destination['location'].split('.')[0],
            'Yes' if destination['enabled'] == 1 else 'No',
            destination.get('hits') or 0.0,
            destination.get('status') or 'N/A'
        ])
    t.add_row([' Hosts', t2])

    return t


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


def get_global_lbs_table(load_balancers):
    """ Helper package to format the global load balancers into a table.

    :param dict load_balancers: A dictionary representing the load_balancers
    :returns: A table containing the global load balancers
    """
    t = Table(['id',
               'hostname',
               'Fallback IP',
               'Method',
               'Connections/sec'])

    for load_balancer in load_balancers:
        t.add_row(['global:%s' % load_balancer['id'],
                   load_balancer['hostname'],
                   load_balancer.get('fallbackIp') or 'None',
                   load_balancer['loadBalanceType']['name'],
                   load_balancer['connectionsPerSecond']])

    return t


class LoadBalancerList(CLIRunnable):
    """
usage: sl loadbal list (--local | --global) [options]

List active load balancers
Required:
  --local     list local load balancers
  --global    list global load balancers

"""
    action = 'list'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)

        if args['--local']:
            load_balancers = mgr.get_local_lbs()
            return get_local_lbs_table(load_balancers)

        if args['--global']:
            load_balancers = mgr.get_global_lbs()
            return get_global_lbs_table(load_balancers)

        return


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
        lb_type = key_value[0]
        loadbal_id = int(key_value[1])

        if lb_type == 'local':
            load_balancer = mgr.get_local_lb(loadbal_id)
            return get_local_lb_table(load_balancer)
        if lb_type == 'global':
            load_balancer = mgr.get_global_lb(loadbal_id)
            return get_global_lb_table(load_balancer)
        return


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
usage: sl loadbal group-add <identifier> --allocation=ALLOC --port=PORT
                  --routing_type=TYPE --routing_method=METHOD [options]

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
usage: sl loadbal create <identifier> (--datacenter=DC) [--hostname=HOSTNAME]
                         [--domain=DOMAIN] [options]

Adds a load_balancer given the billing id returned from create-options

Required:
  -d, --datacenter=DC    Datacenter shortname (sng01, dal05, ...)
                         Note: Omitting this value defaults to the first
                           available datacenter

Options:
  --really     Whether to skip the confirmation prompt
  --global     Whether the load balancer being ordered is global
  --hostname=HOSTNAME   The hostname to use for the global load balancer
  --domain=DOMAIN     The domain to use for the global load balancer
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
        if args.get('--global'):
            mgr.add_global_lb(input_id,
                              datacenter=args['--datacenter'],
                              hostname=args['--hostname'],
                              domain=args['--domain'])
        else:
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


class LoadBalancerHostAdd(CLIRunnable):
    """
usage: sl loadbal host-add <identifier> --ip=IP --port=PORT [options]

Adds a new load_balancer service
Required:
--ip=IP       The IP address of the host
--port=PORT   The virtual port number for the group

Options:
  --order=ORDER        At what order to insert the host  [default: 0].
  --disable            Enabled by default, specify disable otherwise
  --health_check=TYPE  Healthcheck type, either tcp or http [default: http]
  --weight=WEIGHT      The weight to give to the host [default: 1].
"""
    action = 'host-add'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')
        key_value = input_id.split(':')

        if key_value[0] != 'global':
            return 'This CLI is only valid for global load balancers'

        loadbal_id = int(key_value[1])

        mgr.add_host(global_loadbal_id=loadbal_id,
                     ip=args['--ip'],
                     port=int(args['--port']),
                     order=int(args['--order']),
                     health_check=args['--health_check'],
                     weight=int(args['--weight']),
                     enabled=(False if args['--disable'] else True))

        return 'Load balancer service group is being added!'


class LoadBalancerHostDelete(CLIRunnable):
    """
usage: sl loadbal host-delete <identifier> [options]

Cancels an existing load_balancer host
Options:
  --really     Whether to skip the confirmation prompt

"""
    action = 'host-delete'
    options = ['really']

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')

        key_value = input_id.split(':')
        loadbal_id = int(key_value[0])
        host_id = int(key_value[1])

        if args['--really'] or confirm("This action will cancel a host"
                                       " on your load balancer. Continue?"):
            mgr.delete_host(loadbal_id, host_id)
            return 'Host %s is being deleted!' % input_id
        else:
            raise CLIAbort('Aborted.')


class LoadBalancerHostEdit(CLIRunnable):
    """
usage: sl loadbal host-edit <identifier> [--enable|--disable] [options]

Edit a global load balancer host

Options:
  --health_check=TYPE  The healthcheck type, either tcp or http.
  --weight=WEIGHT  The weight to give to the host.
  --ip=IP       The IP address of the host
  --port=PORT   The virtual port number for the group
  --enable      Enable the host
  --disable     Disable the host
"""
    action = 'host-edit'

    def execute(self, args):
        mgr = LoadBalancerManager(self.client)
        input_id = args.get('<identifier>')
        key_value = input_id.split(':')

        loadbal_id = int(key_value[0])
        host_id = int(key_value[1])
        enabled = -1
        if args['--enable']:
            enabled = 1
        elif args['--disable']:
            enabled = 0

        # check if any input is provided
        if not (args['--ip'] or args['--health_check'] or args['--weight'] or
                args['--port'] or args['--enable'] or args['--disable']):
            return 'At least one property is required to be changed!'

        mgr.edit_host(loadbal_id=loadbal_id,
                      host_id=host_id,
                      ip=args['--ip'],
                      port=int(args.get('--port') or 0),
                      health_check=args['--health_check'],
                      weight=int(args.get('--weight') or 0),
                      enabled=enabled)

        return 'Load balancer host %s is being updated!' % input_id

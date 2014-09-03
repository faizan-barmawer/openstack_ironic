# Copyright 2014 Hewlett-Packard Development Company, L.P.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
Common functionalities shared between different iLO modules.
"""


from oslo.config import cfg
from oslo.utils import importutils

from ironic.common import exception
from ironic.common import i18n
from ironic.common.i18n import _
from ironic.openstack.common import log as logging

ilo_client = importutils.try_import('proliantutils.ilo.ribcl')


STANDARD_LICENSE = 1
ESSENTIALS_LICENSE = 2
ADVANCED_LICENSE = 3


opts = [
    cfg.IntOpt('client_timeout',
               default=60,
               help='Timeout (in seconds) for iLO operations'),
    cfg.IntOpt('client_port',
               default=443,
               help='Port to be used for iLO operations'),
]

CONF = cfg.CONF
CONF.register_opts(opts, group='ilo')

LOG = logging.getLogger(__name__)

_LI = i18n._LI
_LW = i18n._LW
_LE = i18n._LE

REQUIRED_PROPERTIES = {
    'ilo_address': _("IP address or hostname of the iLO. Required."),
    'ilo_username': _("username for the iLO with administrator privileges. "
                      "Required."),
    'ilo_password': _("password for ilo_username. Required.")
}
OPTIONAL_PROPERTIES = {
    'client_port': _("port to be used for iLO operations. Optional."),
    'client_timeout': _("timeout (in seconds) for iLO operations. Optional.")
}
COMMON_PROPERTIES = REQUIRED_PROPERTIES.copy()
COMMON_PROPERTIES.update(OPTIONAL_PROPERTIES)


def parse_driver_info(node):
    """Gets the driver specific Node deployment info.

    This method validates whether the 'driver_info' property of the
    supplied node contains the required information for this driver.

    :param node: an ironic node object.
    :returns: a dict containing information from driver_info
        and default values.
    :raises: InvalidParameterValue on invalid inputs.
    :raises: MissingParameterValue if some mandatory information
        is missing on the node
    """
    info = node.driver_info
    d_info = {}

    error_msgs = []
    for param in REQUIRED_PROPERTIES:
        try:
            d_info[param] = info[param]
        except KeyError:
            error_msgs.append(_("'%s' not supplied to IloDriver.") % param)
    if error_msgs:
        msg = (_("The following parameters were mising while parsing "
                 "driver_info:\n%s") % "\n".join(error_msgs))
        raise exception.MissingParameterValue(msg)

    for param in OPTIONAL_PROPERTIES:
        value = info.get(param, CONF.ilo.get(param))
        try:
            value = int(value)
        except ValueError:
            error_msgs.append(_("'%s' is not an integer.") % param)
            continue
        d_info[param] = value

    if error_msgs:
        msg = (_("The following errors were encountered while parsing "
                 "driver_info:\n%s") % "\n".join(error_msgs))
        raise exception.InvalidParameterValue(msg)

    return d_info


def get_ilo_object(node):
    """Gets an IloClient object from proliantutils library.

    Given an ironic node object, this method gives back a IloClient object
    to do operations on the iLO.

    :param node: an ironic node object.
    :returns: an IloClient object.
    :raises: InvalidParameterValue on invalid inputs.
    :raises: MissingParameterValue if some mandatory information
        is missing on the node
    """
    driver_info = parse_driver_info(node)
    ilo_object = ilo_client.IloClient(driver_info['ilo_address'],
                                      driver_info['ilo_username'],
                                      driver_info['ilo_password'],
                                      driver_info['client_timeout'],
                                      driver_info['client_port'])
    return ilo_object


def get_ilo_license(node):
    """Gives the current installed license on the node.

    Given an ironic node object, this method queries the iLO
    for currently installed license and returns it back.

    :param node: an ironic node object.
    :returns: a constant defined in this module which
        refers to the current license installed on the node.
    :raises: InvalidParameterValue on invalid inputs.
    :raises: MissingParameterValue if some mandatory information
        is missing on the node
    :raises: IloOperationError if it failed to retrieve the
        installed licenses from the iLO.
    """
    # Get the ilo client object, and then the license from the iLO
    ilo_object = get_ilo_object(node)
    try:
        license_info = ilo_object.get_all_licenses()
    except ilo_client.IloError as ilo_exception:
        raise exception.IloOperationError(operation=_('iLO license check'),
                                          error=str(ilo_exception))

    # Check the license to see if the given license exists
    current_license_type = license_info['LICENSE_TYPE']

    if current_license_type.endswith("Advanced"):
        return ADVANCED_LICENSE
    elif current_license_type.endswith("Essentials"):
        return ESSENTIALS_LICENSE
    else:
        return STANDARD_LICENSE


# TODO(rameshg87): This needs to be moved to iLO's management interface.
def set_persistent_boot_device(node, device):
    """Sets the node to boot from a device for the next boot persistently.

    :param node: an ironic node object.
    :param device: the device to boot from
    :raises: IloOperationError if setting boot device failed.
    """
    ilo_object = get_ilo_object(node)

    try:
        ilo_object.set_persistent_boot(device)
    except ilo_client.IloError as ilo_exception:
        operation = _("Setting %s as persistent boot device") % device
        raise exception.IloOperationError(operation=operation,
                                          error=ilo_exception)

    LOG.debug(_LI("Node %(uuid)s set to boot persistently from %(device)s."),
             {'uuid': node.uuid, 'device': device})


def set_boot_mode(node, boot_mode):
    """Sets the node to boot using boot_mode for the next boot.

    The valid values for boot_mode are 'bios' and 'uefi'.

    :param node: an ironic node object.
    :param boot_mode: Next boot mode.
    :raises: IloOperationError if setting boot mode failed.
    """
    if boot_mode is None:
        LOG.info(_LI("No boot mode specified."))
        return

    ilo_object = get_ilo_object(node)

    try:
        p_boot_mode = ilo_object.get_pending_boot_mode()
    except ilo_client.IloCommandNotSupportedError:
        p_boot_mode = 'LEGACY'

    if p_boot_mode.lower().replace('legacy', 'bios') == boot_mode:
        LOG.info(_LI("Node %(uuid)s pending boot mode is %(boot_mode)s."),
                 {'uuid': node.uuid, 'boot_mode': boot_mode})
        return

    try:
        ilo_object.set_pending_boot_mode(
                        boot_mode.replace('bios', 'legacy').upper())
    except ilo_client.IloError as ilo_exception:
        operation = _("Setting %s as boot mode") % boot_mode
        raise exception.IloOperationError(operation=operation,
                error=ilo_exception)

    LOG.info(_LI("Node %(uuid)s boot mode is set to %(boot_mode)s."),
             {'uuid': node.uuid, 'boot_mode': boot_mode})


def validate_boot_mode(node):
    """Validate the boot_mode capability set in node property.

    :param node: an ironic node object.
    :raises: InvalidParameterValue, if some information is missing or
            invalid.
    """
    boot_mode = get_node_capability(node, 'boot_mode')

    if boot_mode not in [None, 'bios', 'uefi']:
        raise exception.InvalidParameterValue(_LE("Invalid boot_mode "
                          "parameter '%s'.") % boot_mode)


def update_boot_mode_capability(task):
    """Update 'boot_mode' capability value of node's 'capabilities' property.

    :param task: Task object.

    """
    ilo_object = get_ilo_object(task.node)

    try:
        p_boot_mode = ilo_object.get_pending_boot_mode()
    except ilo_client.IloCommandNotSupportedError:
        p_boot_mode = 'LEGACY'

    set_node_capability(task, 'boot_mode',
                         p_boot_mode.replace('LEGACY', 'bios').lower())


def set_node_capability(task, capability, value):
    """Set 'capability' to node's 'capabilities' property.

    If value is 'None', then remove the capability from node property

    :param task: Task object.
    :param capability: Capability key.
    :param value: Capability value.

    """
    node = task.node
    capabilities = node.properties.get('capabilities')

    if capability is None:
        return None

    if value:
        new_cap = capability + ':' + value
    else:
        new_cap = ''

    old_cap_value = None

    if capabilities:
        for node_capability in str(capabilities).split(','):
            parts = node_capability.split(':')
            if len(parts) == 2 and parts[0] and parts[1]:
                if parts[0] == capability:
                    old_cap_value = capability + ':' + parts[1]
                    break
            else:
                LOG.warn(_LW("Ignoring malformed capability '%s'. "
                    "Format should be 'key:val'.") % node_capability)

        if old_cap_value:
            capabilities = capabilities.replace(old_cap_value, new_cap)
        else:
            if value:
                capabilities = new_cap + ',' + capabilities
            else:
                return None
    else:
        capabilities = new_cap

    node.properties['capabilities'] = capabilities
    node.save(task.context)


def get_node_capability(node, capability):
    """Returns 'capability' value from node's 'capabilities' property

    :param node: Node object.
    :param capability: Capability key.
    :return: Capability value.
             If capability is not present, then return None

    """
    capabilities = node.properties.get('capabilities')
    if capabilities is not None:
        for node_capability in str(capabilities).split(','):
            parts = node_capability.split(':')
            if len(parts) == 2 and parts[0] and parts[1]:
                if parts[0] == capability:
                    return parts[1]
            else:
                LOG.warn(_LW("Ignoring malformed capability '%s'. "
                    "Format should be 'key:val'.") % node_capability)
    return None

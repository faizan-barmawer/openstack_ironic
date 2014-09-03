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
iLO Deploy Driver(s) and supporting methods.
"""

from ironic.drivers.modules.ilo import common as ilo_common
from ironic.drivers.modules import pxe


class IloPXEDeploy(pxe.PXEDeploy):

    def validate(self, task):
        """Validate the deployment information for the task's node.

        This method calls the PXEDeploy's validate method.  In addition to
        this, it also validates whether the 'boot_mode' capability of the node
        has been set to a proper value.

        :param task: a TaskManager instance containing the node to act on.
        :raises: InvalidParameterValue, if some information is missing or
            invalid.
        """
        ilo_common.validate_boot_mode(task.node)
        super(IloPXEDeploy, self).validate(task)

    def deploy(self, task):
        """Start deployment of the task's node'.

        This method calls PXEDeploy's deploy method to deploy on the given
        node.  In addition to that, it sets the node to the request boot_mode
        and also sets the boot device to 'NETWORK'.

        :param task: a TaskManager instance containing the node to act on.
        :returns: deploy state DEPLOYWAIT.
        """
        boot_mode = ilo_common.get_node_capability(task.node, 'boot_mode')
        if boot_mode:
            ilo_common.set_boot_mode(task.node, boot_mode)
        else:
            ilo_common.update_boot_mode_capability(task)

        ilo_common.set_persistent_boot_device(task.node, 'NETWORK')

        return super(IloPXEDeploy, self).deploy(task)

# Copyright 2014 Hewlett-Packard Development Company, L.P.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Test class for common methods used by iLO modules."""

import mock

from ironic.conductor import task_manager
from ironic.db import api as dbapi
from ironic.drivers.modules.ilo import common as ilo_common
from ironic.drivers.modules import pxe
from ironic.openstack.common import context
from ironic.openstack.common import importutils
from ironic.tests import base
from ironic.tests.conductor import utils as mgr_utils
from ironic.tests.db import utils as db_utils
from ironic.tests.objects import utils as obj_utils

ilo_client = importutils.try_import('proliantutils.ilo.ribcl')


INFO_DICT = db_utils.get_test_ilo_info()


class IloPXEDeployTestCase(base.TestCase):

    def setUp(self):
        super(IloPXEDeployTestCase, self).setUp()
        self.dbapi = dbapi.get_instance()
        self.context = context.get_admin_context()
        mgr_utils.mock_the_extension_manager(driver="pxe_ilo")
        self.node = obj_utils.create_test_node(self.context,
                driver='pxe_ilo', driver_info=INFO_DICT)

    @mock.patch.object(pxe.PXEDeploy, 'validate')
    @mock.patch.object(ilo_common, 'validate_boot_mode')
    def test_validate(self, boot_mode_mock, pxe_validate_mock):
        with task_manager.acquire(self.context, self.node.uuid,
                                  shared=False) as task:
            task.driver.deploy.validate(task)
            boot_mode_mock.assert_called_once_with(task.node)
            pxe_validate_mock.assert_called_once_with(task)

    @mock.patch.object(pxe.PXEDeploy, 'deploy')
    @mock.patch.object(ilo_common, 'set_persistent_boot_device')
    @mock.patch.object(ilo_common, 'set_boot_mode')
    @mock.patch.object(ilo_common, 'get_node_capability')
    def test_deploy_boot_mode_exists(self, node_capability_mock,
                                     set_boot_mode_mock, set_persistent_mock,
                                     pxe_deploy_mock):
        with task_manager.acquire(self.context, self.node.uuid,
                                  shared=False) as task:
            node_capability_mock.return_value = 'uefi'
            task.driver.deploy.deploy(task)
            node_capability_mock.assert_called_once_with(task.node,
                                                         'boot_mode')
            set_boot_mode_mock.assert_called_once_with(task.node, 'uefi')
            set_persistent_mock.assert_called_once_with(task.node, 'NETWORK')
            pxe_deploy_mock.assert_called_once_with(task)

    @mock.patch.object(pxe.PXEDeploy, 'deploy')
    @mock.patch.object(ilo_common, 'set_persistent_boot_device')
    @mock.patch.object(ilo_common, 'update_boot_mode_capability')
    @mock.patch.object(ilo_common, 'get_node_capability')
    def test_deploy_boot_mode_doesnt_exist(self, node_capability_mock,
                                update_capability_mock, set_persistent_mock,
                                           pxe_deploy_mock):
        with task_manager.acquire(self.context, self.node.uuid,
                                  shared=False) as task:
            node_capability_mock.return_value = None
            task.driver.deploy.deploy(task)
            node_capability_mock.assert_called_once_with(task.node,
                                                         'boot_mode')
            update_capability_mock.assert_called_once_with(task)
            set_persistent_mock.assert_called_once_with(task.node, 'NETWORK')
            pxe_deploy_mock.assert_called_once_with(task)

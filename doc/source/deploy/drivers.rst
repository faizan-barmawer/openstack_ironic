.. _drivers:

=================
Enabling Drivers
=================

DRAC
----

DRAC with PXE deploy
^^^^^^^^^^^^^^^^^^^^

- Add ``pxe_drac`` to the list of ``enabled_drivers in`` ``/etc/ironic/ironic.conf``
- Install openwsman-python package

SNMP
----

The SNMP power driver enables control of power distribution units of the type
frequently found in data centre racks. PDUs frequently have a management
ethernet interface and SNMP support enabling control of the power outlets.

The SNMP power driver works with the PXE driver for network deployment and
network-configured boot.

Supported PDUs
^^^^^^^^^^^^^^

- American Power Conversion (APC)
- CyberPower (implemented according to MIB spec but not tested on hardware)
- EatonPower (implemented according to MIB spec but not tested on hardware)
- Teltronix

Software Requirements
^^^^^^^^^^^^^^^^^^^^^

- The PySNMP package must be installed, variously referred to as ``pysnmp``
or ``python-pysnmp``

Enabling the SNMP Power Driver
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Add ``pxe_snmp`` to the list of ``enabled_drivers`` in ``/etc/ironic/ironic.conf``
- Ironic Conductor must be restarted for the new driver to be loaded.

Ironic Node Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

Nodes are configured for SNMP control by setting the Ironic node object's
``driver`` property to be ``pxe_snmp``.  Further configuration values are
added to ``driver_info``:

- ``snmp_address``: the IPv4 address of the PDU controlling this node.
- ``snmp_port``: (optional) A non-standard UDP port to use for SNMP operations.
If not specified, the default port (161) is used.
- ``snmp_outlet``: The power outlet on the PDU (1-based indexing).
- ``snmp_protocol``: (optional) SNMP protocol version
(permitted values ``1``, ``2c`` or ``3``). If not specified, SNMPv1 is chosen.
- ``snmp_community``: (Required for SNMPv1 and SNMPv2c) SNMP community
parameter for reads and writes to the PDU.
- ``snmp_security``: (Required for SNMPv3) SNMP security string.

PDU Configuration
^^^^^^^^^^^^^^^^^

This version of the SNMP power driver does not support handling
PDU authentication credentials. When using SNMPv3, the PDU must be
configured for ``NoAuthentication`` and ``NoEncryption``. The
security name is used analagously to the SNMP community in early
SNMP versions.

iLO drivers
-----------

iLO drivers enable to take advantage of features of iLO management engine
in HP Proliant servers. More information about iLO drivers is available at
https://wiki.openstack.org/wiki/Ironic/Drivers/iLODrivers.

Supported servers
^^^^^^^^^^^^^^^^^

The driver is officially tested on HP Proliant Gen 8 servers and above which
uses iLO 4.

Software Requirements
^^^^^^^^^^^^^^^^^^^^^

- The ``proliantutils`` package must be installed which is available in pypi.

Enabling an iLO driver
^^^^^^^^^^^^^^^^^^^^^^

The following iLO drivers are available:

1. ``iscsi_ilo`` - This driver uses iLO for power operations, iLO virtual
   media for booting the proliant nodes, and uses iscsi to deploy the images.
2. ``agent_ilo`` - This driver uses iLO for power operations, iLO virtual
   media for booting the proliant nodes, and uses ironic-python-agent to deploy
   the images.
3. ``pxe_ilo`` - This driver uses iLO for power operations, PXE to deploy
   the images and iLO for device management.

To enable an iLO driver, add the respective iLO driver (i.e ``iscsi_ilo`` or
``agent_ilo`` or ``pxe_ilo``) to the list of ``enabled_drivers`` in
``/etc/ironic/ironic.conf``.

Ironic Node Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^

Nodes configured for iLO driver should have the ``driver`` property set to
``iscsi_ilo`` or ``agent_ilo`` or ``pxe_ilo``.  The following configuration
values are also required in ``driver_info``:

- ``ilo_address``: IP address or hostname of the iLO.
- ``ilo_username``: Username for the iLO with administrator privileges.
- ``ilo_password``: Password for the above iLO user.
- ``client_port``: (optional) Port to be used for iLO operations if you are
  using a custom port on the iLO.
- ``client_timeout``: (optional) Timeout for iLO operations.
- ``ilo_deploy_iso``: The Glance UUID of the deploy ISO image. More information
  about creating deploy images are available here at
  https://wiki.openstack.org/wiki/Ironic/Drivers/iLODrivers.
- ``ipmi_address``: IP address or hostname of the iLO.
- ``ipmi_username``: Username for the iLO with administrator privileges.
- ``ipmi_password``: Password for the above iLO user.

``iscsi_ilo`` and ``pxe_ilo`` drivers support image deployment on UEFI
enabled baremetal nodes. The following additional setup has to be done to
perform deploy in UEFI boot mode.

1. Update the ironic node with ``boot_mode`` capability in node's properties
   field::

    ironic node-update <NODE-ID> add properties/capabilities='boot_mode:uefi'

2. Make sure that bare metal node is configured to boot in UEFI boot mode.

NOTE: The address, username, password for the iLO must be duplicated in both
'ilo' and 'ipmi' sets of parameters.  This will be fixed in future releases.

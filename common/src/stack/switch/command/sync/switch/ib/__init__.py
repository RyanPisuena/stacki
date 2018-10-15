# @copyright@
# Copyright (c) 2006 - 2017 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
import stack.util
import subprocess
from stack.exception import CommandError

class command(stack.commands.SwitchArgumentProcessor,
	stack.commands.sync.command):
		pass

class Command(command):
	"""
	Reconfigure Infiniband switches.

	<arg optional='1' type='string' name='switch' repeat='1'>
	Zero, one or more ib switch names. If no switch names are supplied,
	all switches will be reconfigured.  All switches will have root's
	public key uploaded, and if `nukeswitch` is True, all will be wiped.
	Only switches which are currently subnet managers will have any other
	configuration applied.
	</arg>

	<param type='boolean' name='nukeswitch' optional='1'>
	If 'yes', then put the switch into a default state (e.g., no vlans, no partitions),
	Just a "flat" switch.
	Default: no
	</param>

	<example cmd="sync switch infiniband-0-0">
	Reconfigure and set startup configuration on infiniband-0-0.
	</example>

	<example cmd="sync switch">
	Reconfigure all switches.
	</example>
	"""

	def run(self, params, args):

		nukeswitch, = self.fillParams([
			('nukeswitch', False),
		])

		self.nukeswitch = self.str2bool(nukeswitch)

		switches = self.getSwitchNames(args)

		switch_attrs = self.getHostAttrDict(switches)

		for switch in switches:
			if 'switch_type' in switch_attrs[switch] and switch_attrs[switch]['switch_type'] != 'infiniband':
				msg = f'{switch} is not an infiniband switch, please verify "stack list host attr {switch} attr=switch_type"'
				raise CommandError(self, msg)

		for switch in self.call('list.host.interface', switches):
			switch_name = switch['host']

			model = self.getHostAttr(switch_name, 'component.model')
			self.runImplementation(switch_attrs[switch_name]['component.model'], [switch_name])


# @copyright@
# Copyright (c) 2018 Teradata
# All rights reserved. Stacki(r) v5.x stacki.com
# https://github.com/Teradata/stacki/blob/master/LICENSE.txt
# @copyright@

import stack.commands
from stack.exception import ArgRequired, ParamValue, CommandError


class Command(
	stack.commands.Command,
	stack.commands.SwitchArgumentProcessor,
):
	"""
	Lists the infiniband partitions in the Stacki database for one or more
	switches.

	<arg type='string' name='switch'>
	The name of the switches to list partitions for.  If a switch is not an
	infiniband subnet manager an error will be raised.
	</arg>

	<param type='string' name='name' optional='1'>
	The name of the partition to list on the switch(es).
	</param>
	"""

	def run(self, params, args):
		if not len(args):
			raise ArgRequired(self, 'switch')

		name, = self.fillParams([
			('name', None),
		])

		if name and name.lower() == 'default':
			name = 'Default'

		switches = self.getSwitchNames(args)
		ibswitches = [sw for sw in self.call('list.switch', ['expanded=True'])
						if sw['model'] == 'm7800' and sw['ib subnet manager']]

		bad_switches = set(switches).difference(sw['switch'] for sw in ibswitches)
		if bad_switches:
			msg = 'The following switches are either non-infiniband or are not subnet managers: '
			raise CommandError(self, msg + f'{", ".join(bad_switches)}')

		format_str = ','.join(['%s'] * len(switches))
		sw_select = '''
			nodes.name, ib.part_name, ib.part_key, ib.options
			FROM nodes, ib_partitions ib
			WHERE nodes.name IN (%s)
			AND nodes.id=ib.switch''' % format_str

		vals = list(switches)

		if name:
			sw_select += ' AND ib.part_name=%s'
			vals.append(name)

		sw_select += ' ORDER BY nodes.name'

		self.beginOutput()
		for line in self.db.select(sw_select, vals):
			self.addOutput(line[0], (line[1], '0x{0:04x}'.format(line[2]), line[3]))
		self.endOutput(header=['switch', 'partition', 'partition key', 'options'])

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
	Lists the infiniband partition members in the Stacki database for one or
	more switches.

	<arg type='string' name='switch'>
	The name of the switches to list partition members for.  If a switch is
	not an infiniband subnet manager an error will be raised.
	</arg>

	<param type='string' name='name' optional='1'>
	The name of the partition to list members for on the switch(es).
	</param>

	<param type='boolean' name='expanded' optional='1'>
	List additional output from the partitions table.
	</param>
	"""

	def run(self, params, args):
		if not len(args):
			raise ArgRequired(self, 'switch')

		name, expanded = self.fillParams([
			('name', None),
			('expanded', False),
		])
		expanded = self.str2bool(expanded)

		if name and name.lower() == 'default':
			name = 'Default'

		switches = self.getSwitchNames(args)
		ibswitches = [sw for sw in self.call('list.switch', ['expanded=True'])
						if sw['model'] == 'm7800' and sw['ib subnet manager']]

		bad_switches = set(switches).difference(sw['switch'] for sw in ibswitches)
		if bad_switches:
			msg = 'The following switches are either non-infiniband or are not subnet managers: '
			raise CommandError(self, msg + f'{", ".join(bad_switches)}')

		sql_columns = 'swnodes.name AS switch, nodes.name AS host, networks.device, networks.mac, ib_p.part_name, ib_m.member_type'
		
		table_headers = ['switch', 'host', 'device', 'guid', 'partition', 'membership']
		if expanded:
			sql_columns += ', ib_p.part_key, ib_p.options'
			table_headers.extend(['partition key', 'options'])

		format_str = ','.join(['%s'] * len(switches))
		member_select = sql_columns + '''
		FROM nodes swnodes, nodes, networks, ib_partitions ib_p, ib_memberships ib_m
		WHERE
			swnodes.name in (%s) AND
			swnodes.id=ib_m.switch AND
			nodes.id=networks.node AND
			networks.id=ib_m.interface AND
			ib_p.id=ib_m.part_name
		''' % format_str

		vals = list(switches)

		if name:
			member_select += ' AND ib_p.part_name in (%s)'
			vals.append(name)

		member_select += ' ORDER BY switch, host, part_name'

		self.beginOutput()
		for line in self.db.select(member_select, vals):
			if expanded:
				line = list(line)
				line[6] = '0x{0:04x}'.format(line[6])
			self.addOutput(line[0], (line[1:]))
		self.endOutput(header=table_headers)

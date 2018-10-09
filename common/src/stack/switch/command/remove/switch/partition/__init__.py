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
	Remove infiniband partitions from the Stacki database for one or more
	switches.

	<arg type='string' name='switch'>
	The name of the switches to remove partitions for.  If a switch is not an
	infiniband subnet manager an error will be raised.
	</arg>

	<param type='string' name='name' optional='1'>
	The name of the partition to remove from the switch(es).
	</param>
	"""

	def run(self, params, args):
		if not len(args):
			raise ArgRequired(self, 'switch')

		name, = self.fillParams([
			('name', None),
		])

		# force is really whether or not this command came from ADD vs SET
		if name and name.lower() == 'default':
			name = 'Default'

		switches = self.getSwitchNames(args)
		ibswitches = [sw for sw in self.call('list.switch', ['expanded=True'])
						if sw['model'] == 'm7800' and sw['ib subnet manager']]

		bad_switches = set(switches).difference(sw['switch'] for sw in ibswitches)
		if bad_switches:
			msg = 'The following switches are either non-infiniband or are not subnet managers: '
			raise CommandError(self, msg + f'{", ".join(bad_switches)}')

		ids_sql = 'name, id FROM nodes WHERE name IN (%s)' % ','.join(['%s'] * len(switches))
		sw_ids = dict((row[0], row[1]) for row in self.db.select(ids_sql, tuple(switches)))

		format_str = ','.join(['%s'] * len(switches))
		delete_stmt = '''
			DELETE from ib_partitions
			WHERE switch IN (%s)''' % format_str
							   
		vals = list(sw_ids.values())

		if name:
			sw_select += ' AND ib_partitions.part_name=%s'
			vals.append(name)

		self.db.execute(delete_stmt, vals)
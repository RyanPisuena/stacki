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
	Sets the infiniband partition flags in the Stacki database.
	Note that a sync is still required to enact this change on the switch.

	<arg type='string' name='switch'>
	The name of the switches on which to set this flag.  If a switch
	is not an infiniband subnet manager an error will be raised.
	</arg>

	<param type='string' name='name' optional='0'>
	The name of the partition to set this flag on.  Must either be 'Default'
	or a hex value between 0x0001-0x7FFE (1 and 32,766).
	</param>

	<param type='string' name='options' optional='1'>
	A list of options to set on the partition.  The format is 
	'flag=value flag2=value2'.  Currently supported are 'ipoib=True|False'
	and 'defmember=limited|full'.  Unless explicitly specified, 'ipoib' and
	'defmember' are not set.
	</param>
	"""		

	def run(self, params, args):
		if not len(args):
			raise ArgRequired(self, 'switch')

		name, options_param, force = self.fillParams([
			('name', None, True),
			('options', None),
			('force', True),
		])

		# force is really whether or not this command came from ADD vs SET
		stack_set = self.str2bool(force)

		name = name.lower()
		if name == 'default':
			name = 'Default'
			pkey = 0x7fff
		else:
			try:
				pkey = int(name, 16)
			except ValueError:
				raise ParamValue(self, 'name', 'a hex value between 0x0001 and 0x7FFE, or "default"')

		parsed_options_str = ''
		if options_param:
			options = dict(flag.split('=') for flag in options_param.split() if '=' in flag)
			if 'ipoib' in options:
				parsed_options_str += f"ipoib={self.str2bool(options['ipoib'])}"
				del options['ipoib']
			if 'defmember' in options and options['defmember'].lower() in ['limited', 'full']:
				parsed_options_str += f" defmember={options['defmember'].lower()}"
				del options['defmember']
			if options:
				# if there's any leftover, error
				msg = 'The following are invalid partition options: '
				raise CommandError(self, msg + ' '.join(f'{k}={v}' for k, v in options.items()))

		switches = self.getSwitchNames(args)
		ibswitches = [sw for sw in self.call('list.switch', ['expanded=True'])
						if sw['model'] == 'm7800' and sw['ib subnet manager']]

		bad_switches = set(switches).difference(sw['switch'] for sw in ibswitches)
		if bad_switches:
			msg = 'the following switches are either non-infiniband or are not subnet managers: '
			raise CommandError(self, msg + f'{", ".join(bad_switches)}')

		ids_sql = 'name, id FROM nodes WHERE name IN (%s)' % ','.join(['%s'] * len(switches))
		sw_ids = dict((row[0], row[1]) for row in self.db.select(ids_sql, tuple(switches)))

		sql_check = 'id, options FROM ib_partitions WHERE switch=%s AND part_name=%s'
		for switch in switches:
			# if doing an ADD, we want to ensure the partition doesn't already exist
			exists = self.db.select(sql_check, (sw_ids[switch], name))
			if not exists:
				continue

			existing_part_id = exists[0][0]

			if not stack_set:
				raise CommandError(self, f'partition "{name}" already exists on switch "{switch}"')
			if options_param is None:
				# if user supplied no options field, for existing keep the previous options field
				parsed_options_str = exists[0][1]

		# if it already exists, we do an UPDATE instead
		sql_update = 'UPDATE ib_partitions SET switch=%s, part_key=%s, part_name=%s, options=%s WHERE switch=%s and id=%s'
		sql_insert = 'INSERT INTO ib_partitions (switch, part_key, part_name, options) VALUES (%s, %s, %s, %s)'

		for switch in switches:
			if stack_set and exists:
				self.db.execute(sql_update, (sw_ids[switch], pkey, name, parsed_options_str, sw_ids[switch], existing_part_id))
			else:
				self.db.execute(sql_insert, (sw_ids[switch], pkey, name, parsed_options_str))
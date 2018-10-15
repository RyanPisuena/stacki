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
	Set membership state on an infiniband partition in the Stacki database for
	a switch.

	<arg type='string' name='switch'>
	The name of the switches to add partition members to.  If a switch is
	not an infiniband subnet manager an error will be raised.
	</arg>

	<param type='string' name='name' optional='0'>
	The name of the partition to set membership status on the switch.
	</param>

	<param type='string' name='guid' optional='1'>
	The GUID of the host's infiniband interface to use.
	</param>

	<param type='string' name='guid' optional='1'>
	The hostname with an infiniband interface to add as a member.  Must be
	specified with the name of the interface to use.
	</param>

	<param type='string' name='interface' optional='1'>
	The name of an infiniband interface to add as a member.  Must be specified
	with the name of the host the interface belongs to.
	</param>

	<param type='string' name='membership' optional='1'>
	The membership state to use for this member on the partition.  Must be 'both',
	or 'limited'.  Defaults to 'limited'.
	</param>
	"""

	def run(self, params, args):
		if len(args) != 1:
			raise ArgUnique(self, 'switch')

		name, guid, hostname, interface, membership = self.fillParams([
			('name', None, True),
			('guid', None),
			('hostname', None),
			('interface', None),
			('membership', 'limited'),
		])

		if not guid and not hostname:
			raise CommandError(self, 'either guid or hostname and interface must be specified')

		if guid:
			guid = guid.lower()
		if hostname and not interface or interface and not hostname:
			raise CommandError(self, 'hostname and interface must both be specified')
		else:
			ifaces = self.call('list.host.interface', [hostname])
			for row in ifaces:
				if row['interface'] == interface:
					guid = row['mac']
					break
			else: #nobreak
				raise CommandError(self, f'hostname has no interface named "{interface}"')

		name = name.lower()
		if name == 'default':
			name = 'Default'

		membership = membership.lower()
		if membership not in ['limited', 'full']:
			raise ParamValue(self, 'membership', 'either "limited" or "full"')

		switches = self.getSwitchNames(args)
		ibswitches = [sw for sw in self.call('list.switch', ['expanded=True'])
						if sw['model'] == 'm7800' and sw['ib subnet manager']]

		bad_switches = set(switches).difference(sw['switch'] for sw in ibswitches)
		if bad_switches:
			msg = 'The following switches are either non-infiniband or are not subnet managers: '
			raise CommandError(self, msg + f'{", ".join(bad_switches)}')

		switch, = switches
		switch_id = self.db.select('id FROM nodes WHERE name=%s', switch)

		# lookups using sql instead of api calls because all 'list switch partition' calls are expensive.
		# Ensure this partition exists on the switch
		if self.db.count(
				'(id) FROM ib_partitions WHERE part_name=%s AND switch=%s',
				(name, switch_id)) == 0:
			raise CommandError(self, f'partition {name} does not exist on switch {switch}')

		# Determine if this member already exists on the partition and switch
		existing = False
		if self.db.count('''
			(ib_m.id)
			FROM ib_memberships ib_m, ib_partitions ib_p, nodes, networks
			WHERE ib_m.switch=nodes.id AND
				nodes.name=%s AND
				networks.id=ib_m.interface AND
				ib_m.part_name=ib_p.id AND
				ib_p.part_name=%s AND
				networks.mac=%s ''',
				(switch, name, guid)) > 0:
			existing = True

		insert_sql = '''
				INSERT INTO ib_memberships (switch, interface, part_name, member_type)
				VALUES (%s,
						(SELECT id FROM networks WHERE mac=%s),
						(SELECT id FROM ib_partitions WHERE part_name=%s AND switch=%s),
						%s)
				'''

		update_sql = '''
				UPDATE ib_memberships
				SET switch=%s,
					interface=(SELECT id FROM networks WHERE mac=%s),
					part_name=(SELECT id FROM ib_partitions WHERE part_name=%s AND switch=%s),
					member_type=%s
				WHERE switch=%s AND
					part_name=(SELECT id FROM ib_partitions WHERE part_name=%s AND switch=%s) AND
					interface=(SELECT id FROM networks WHERE mac=%s)
				'''

		if existing:
			self.db.execute(update_sql, (switch_id, guid, name, switch_id, membership, switch_id, name, switch_id, guid))
		else:
			self.db.execute(insert_sql, (switch_id, guid, name, switch_id, membership))
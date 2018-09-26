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
	Adds a partition for an Infiniband switch to the Stacki database.
	Note that a sync is still required to enact this change on the switch.

	<arg type='string' name='switch'>
	The name of the switches on which to create this partition.  If a switch
	is not an infiniband subnet managers an error will be raised.
	</arg>

	<param type='string' name='name' optional='0'>
	The name of the partition to be created.  Must either be 'Default' or a
	hex value between 0x0001-0x7FFE (1 and 32,766).
	</param>

	<param type='string' name='options' optional='1'>
	A set of options to create the partition with.  The format is 
	'flag=value flag2=value2'.  Currently supported are 'ipoib=True|False'
	and 'defmember=limited|full'.  Unless explicitly specified, 'ipoib' and
	'defmember' are not set.
	</param>

	"""

	def run(self, params, args):
		self.command('set.switch.partition', self._argv + ['force=false'])
		return self.rc
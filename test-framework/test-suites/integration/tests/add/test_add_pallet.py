import json
from textwrap import dedent

import pytest


@pytest.mark.usefixtures('create_pallet_isos', 'create_blank_iso')
class TestAddPallet:
	def test_add_pallet_no_pallet(self, host):
		# Call add pallet with nothign mounted and no pallets passed in
		result = host.run('stack add pallet')
		assert result.rc == 255
		assert result.stderr == 'error - no pallets provided and /mnt/cdrom is unmounted\n'

	def test_add_pallet_invalid(self, host):
		# Add something that doesn't exist
		result = host.run('stack add pallet /export/test.iso')
		assert result.rc == 255
		assert result.stderr == 'error - Cannot find /export/test.iso or /export/test.iso is not an ISO image\n'

	def test_add_pallet_username_no_password(self, host):
		result = host.run('stack add pallet /export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso username=test')
		assert result.rc == 255
		assert result.stderr == dedent('''\
			error - must supply a password with the username
			[pallet ...] [clean=bool] [dir=string] [password=string] [updatedb=string] [username=string]
		''')

	def test_add_pallet_password_no_username(self, host):
		result = host.run('stack add pallet /export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso password=test')
		assert result.rc == 255
		assert result.stderr == dedent('''\
			error - must supply a username with the password
			[pallet ...] [clean=bool] [dir=string] [password=string] [updatedb=string] [username=string]
		''')

	def test_add_pallet_minimal(self, host):
		# Add our minimal pallet
		result = host.run('stack add pallet /export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso')
		assert result.rc == 0
		assert result.stdout == 'Copying minimal 1.0-sles12 to pallets ...\n'

		# Check it made it in as expected
		result = host.run('stack list pallet minimal output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'minimal',
				'version': '1.0',
				'release': 'sles12',
				'arch': 'x86_64',
				'os': 'sles',
				'boxes': ''
			}
		]

	def test_add_pallet_no_mountpoint(self, host, rmtree):
		# Remove our mountpoint
		rmtree('/mnt/cdrom')

		# Add our minimal pallet
		result = host.run('stack add pallet /export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso')
		assert result.rc == 0
		assert result.stdout == 'Copying minimal 1.0-sles12 to pallets ...\n'

		# Check it made it in as expected
		result = host.run('stack list pallet minimal output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'minimal',
				'version': '1.0',
				'release': 'sles12',
				'arch': 'x86_64',
				'os': 'sles',
				'boxes': ''
			}
		]

	def test_add_pallet_mountpoint_in_use(self, host):
		# Mount an ISO to simulate something left mounted
		result = host.run('mount /export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso /mnt/cdrom')
		assert result.rc == 0

		# Add our minimal pallet
		result = host.run('stack add pallet /export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso')
		assert result.rc == 0
		assert result.stdout == 'Copying minimal 1.0-sles12 to pallets ...\n'

		# Check it made it in as expected
		result = host.run('stack list pallet minimal output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'minimal',
				'version': '1.0',
				'release': 'sles12',
				'arch': 'x86_64',
				'os': 'sles',
				'boxes': ''
			}
		]

	def test_add_pallet_mounted_cdrom(self, host):
		# Mount our pallet
		result = host.run('mount /export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso /mnt/cdrom')
		assert result.rc == 0

		# Add our minimal pallet that is already mounted
		result = host.run('stack add pallet')
		assert result.rc == 0
		assert result.stdout == dedent('''\
			/export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso on /mnt/cdrom type iso9660 (ro,relatime)
			Copying minimal 1.0-sles12 to pallets ...
		''')

		# Check it made it in as expected
		result = host.run('stack list pallet minimal output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'minimal',
				'version': '1.0',
				'release': 'sles12',
				'arch': 'x86_64',
				'os': 'sles',
				'boxes': ''
			}
		]

	def test_add_pallet_minimal_dryrun(self, host):
		# Add our minimal pallet as a dryrun
		result = host.run('stack add pallet /export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso dryrun=true')
		assert result.rc == 0
		assert result.stdout == dedent('''\
			NAME    VERSION RELEASE ARCH   OS
			minimal 1.0     sles12  x86_64 sles /export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso
		''')

		# Confirm it didn't get added to the DB
		result = host.run('stack list pallet minimal')
		assert result.rc == 255
		assert result.stderr == dedent('''\
			error - "minimal" argument is not a valid pallet
			[pallet ...] {expanded=bool} [arch=string] [os=string] [release=string] [version=string]
		''')

	def test_add_pallet_duplicate(self, host):
		# Add our minimal pallet
		result = host.run('stack add pallet /export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso')
		assert result.rc == 0
		assert result.stdout == 'Copying minimal 1.0-sles12 to pallets ...\n'

		# Add our minimal pallet again
		result = host.run('stack add pallet /export/test-files/pallets/minimal-1.0-sles12.x86_64.disk1.iso')
		assert result.rc == 0
		assert result.stdout == 'Copying minimal 1.0-sles12 to pallets ...\n'

		# Adding the same pallet multiple times should only result in a
		# single pallet in the database
		result = host.run('stack list pallet minimal output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'minimal',
				'version': '1.0',
				'release': 'sles12',
				'arch': 'x86_64',
				'os': 'sles',
				'boxes': ''
			}
		]

	def test_add_pallet_add_OS_pallet_again(self, host, host_os):
		# Add our OS pallet, which is already added so it should be quick
		if host_os == 'sles':
			result = host.run('stack add pallet /export/isos/SLE-12-SP3-Server-DVD-x86_64-GM-DVD1.iso')
			assert result.rc == 0
			assert result.stdout == 'Copying "SLES" (12,x86_64) pallet ...\nPatching SLES pallet\n'
		else:
			result = host.run('stack add pallet /export/isos/CentOS-7-x86_64-Everything-1708.iso')
			assert result.rc == 0
			assert result.stdout == 'Copying CentOS 7-redhat7 pallet ...\n'

	def test_add_pallet_add_OS_pallet_dryrun(self, host, host_os):
		# Add our OS pallet as a dryrun
		if host_os == 'sles':
			result = host.run('stack add pallet /export/isos/SLE-12-SP3-Server-DVD-x86_64-GM-DVD1.iso dryrun=true')
			assert result.rc == 0
			assert result.stdout == dedent('''\
				NAME VERSION RELEASE ARCH   OS
				SLES 12      sp3     x86_64 sles /export/isos/SLE-12-SP3-Server-DVD-x86_64-GM-DVD1.iso
			''')
		else:
			result = host.run('stack add pallet /export/isos/CentOS-7-x86_64-Everything-1708.iso dryrun=true')
			assert result.rc == 0
			assert result.stdout == dedent('''\
				NAME   VERSION RELEASE ARCH   OS
				CentOS 7       redhat7 x86_64 redhat /export/isos/CentOS-7-x86_64-Everything-1708.iso
			''')

	def test_add_pallet_disk_pallet(self, host):
		# Add the minimal pallet from the disk
		result = host.run('stack add pallet /export/test-files/pallets/minimal')
		assert result.rc == 0

		# Check it made it in as expected
		result = host.run('stack list pallet minimal output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'minimal',
				'version': '1.0',
				'release': 'sles12',
				'arch': 'x86_64',
				'os': 'sles',
				'boxes': ''
			}
		]

	def test_add_pallet_network_iso(self, host, run_file_server):
		# Add the minimal pallet ISO from the network
		result = host.run('stack add pallet http://127.0.0.1:8000/pallets/minimal-1.0-sles12.x86_64.disk1.iso')
		assert result.rc == 0

		# Check it made it in as expected
		result = host.run('stack list pallet minimal output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'minimal',
				'version': '1.0',
				'release': 'sles12',
				'arch': 'x86_64',
				'os': 'sles',
				'boxes': ''
			}
		]

	def test_add_pallet_network_directory(self, host, run_file_server):
		# Add the minimal pallet directory from the network
		result = host.run('stack add pallet http://127.0.0.1:8000/pallets/minimal/1.0/sles12/sles/x86_64')
		assert result.rc == 0

		# Check it made it in as expected
		result = host.run('stack list pallet minimal output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'minimal',
				'version': '1.0',
				'release': 'sles12',
				'arch': 'x86_64',
				'os': 'sles',
				'boxes': ''
			}
		]

	def test_add_pallet_failed_download(self, host, run_file_server):
		result = host.run('stack add pallet http://127.0.0.1:8000/test.iso')
		assert result.rc == 255
		assert result.stderr == 'error - unable to download test.iso: http error 404\n'

	def test_add_pallet_invalid_iso(self, host):
		result = host.run('stack add pallet /export/test-files/pallets/blank.iso')
		assert result.rc == 255
		assert result.stderr == 'error - unknown pallet on /mnt/cdrom\n'

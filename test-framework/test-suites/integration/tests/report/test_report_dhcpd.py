class TestReportDhcpd:
	def test_duplicate_interface(self, host):
		result = host.run('stack add host interface frontend-0-0 interface=eth0 mac=00:11:22:33:44:55 ip=1.2.3.4 network=private')
		assert result.rc == 0
		result = host.run('stack set host interface interface frontend-0-0 mac=00:11:22:33:44:55 interface=eth1')
		assert result.rc == 0

		# duplicate interface should be excluded from report
		result = host.run('stack report dhcpd')
		assert result.rc == 0
		assert result.stdout.count('eth1') == 2

	def test_invalid_channel(self, host):
		result = host.run('stack add host interface frontend-0-0 interface=eth0 mac=00:11:22:33:44:55 channel=alvin')
		assert result.rc == 0

		# interface with invalid channel should be excluded from report
		result = host.run('stack report dhcpd')
		assert result.rc == 0
		assert 'eth0' not in result.stdout

	def test_invalid_ipmi_channel(self, host):
		result = host.run('stack add host interface frontend-0-0 interface=ipmi channel=1')
		assert result.rc == 0

		# interface with invalid channel should be excluded from report
		result = host.run('stack report dhcpd')
		assert result.rc == 0
		assert 'eth0' not in result.stdout

	def test_single_pxe_network_sles(self, host, fake_os_sles):
		# Change the mac on eth1 so it will match our expected outputs
		result = host.run('stack set host interface mac frontend-0-0 interface=eth1 mac=00:11:22:33:44:55')
		assert result.rc == 0

		# Change the gateway on the private network, so that will match
		result = host.run('stack set network gateway private gateway=192.168.0.1')
		assert result.rc == 0

		# The default network has a single PXE interface
		result = host.run('stack report dhcpd')
		assert result.rc == 0

		with open(f'/export/test-files/report/test_single_pxe_network_sles.txt') as output:
			assert result.stdout == output.read()

	def test_single_pxe_network_redhat(self, host, fake_os_redhat):
		# Change the mac on eth1 so it will match our expected outputs
		result = host.run('stack set host interface mac frontend-0-0 interface=eth1 mac=00:11:22:33:44:55')
		assert result.rc == 0

		# Change the gateway on the private network, so that will match
		result = host.run('stack set network gateway private gateway=192.168.0.1')
		assert result.rc == 0

		# The default network has a single PXE interface
		result = host.run('stack report dhcpd')
		assert result.rc == 0

		with open(f'/export/test-files/report/test_single_pxe_network_redhat.txt') as output:
			assert result.stdout == output.read()

	def test_multiple_pxe_networks(self, host, host_os):
		# Change the mac on eth1 so it will match our expected outputs
		result = host.run('stack set host interface mac frontend-0-0 interface=eth1 mac=00:11:22:33:44:55')
		assert result.rc == 0

		# Change the gateway on the private network, so that will match
		result = host.run('stack set network gateway private gateway=192.168.0.1')
		assert result.rc == 0

		# Add a PXE test network in 10-dot
		result = host.run('stack add network test address=10.0.0.0 mask=255.255.255.0 gateway=10.0.0.1 pxe=true')
		assert result.rc == 0

		# Add a second interface on the test network to the frontend
		result = host.run('stack add host interface frontend-0-0 interface=eth3 network=test')
		assert result.rc == 0

		# Generate our dhcpd file
		result = host.run('stack report dhcpd')
		assert result.rc == 0

		with open(f'/export/test-files/report/test_multiple_pxe_networks_{host_os}.txt') as output:
			assert result.stdout == output.read()

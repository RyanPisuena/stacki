import json
from textwrap import dedent


class TestEnableCart:
	def test_enable_cart_no_args(self, host):
		result = host.run('stack enable cart')
		assert result.rc == 255
		assert result.stderr == dedent('''\
			error - "cart" argument is required
			{cart ...} [box=string]
		''')

	def test_enable_cart_invalid_cart(self, host):
		result = host.run('stack enable cart test')
		assert result.rc == 255
		assert result.stderr == dedent('''\
			error - "test" argument is not a valid cart
			{cart ...} [box=string]
		''')

	def test_enable_cart_invalid_box(self, host):
		result = host.run('stack enable cart test box=test')
		assert result.rc == 255
		assert result.stderr == 'error - unknown box "test"\n'

	def test_enable_cart_default_box(self, host):
		# Add our test cart
		result = host.run('stack add cart test')
		assert result.rc == 0

		# Add the cart to the default box
		result = host.run('stack enable cart test')
		assert result.rc == 0

		# Confirm it is in the box now
		result = host.run('stack list cart test output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'test',
				'boxes': 'default'
			}
		]

	def test_enable_cart_with_box(self, host):
		# Add our test box
		result = host.run('stack add box test')
		assert result.rc == 0

		# Add our test cart
		result = host.run('stack add cart test')
		assert result.rc == 0

		# Add the cart to the test box
		result = host.run('stack enable cart test box=test')
		assert result.rc == 0

		# Confirm it is in the box now
		result = host.run('stack list cart test output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'test',
				'boxes': 'test'
			}
		]

	def test_enable_cart_already_enabled(self, host):
		# Add our test cart
		result = host.run('stack add cart test')
		assert result.rc == 0

		# Add the cart to the default box
		result = host.run('stack enable cart test')
		assert result.rc == 0

		# Confirm it is in the box now
		result = host.run('stack list cart test output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'test',
				'boxes': 'default'
			}
		]

		# Now enable it again, nothing should change in the db
		result = host.run('stack enable cart test')
		assert result.rc == 0

		# Confirm everything is the same
		result = host.run('stack list cart test output-format=json')
		assert result.rc == 0
		assert json.loads(result.stdout) == [
			{
				'name': 'test',
				'boxes': 'default'
			}
		]

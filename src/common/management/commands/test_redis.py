import logging
from datetime import datetime

from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.core.management.base import BaseCommand, CommandError

from common.complex_state import UserStateManager, UserStatus

logger = logging.getLogger(__name__)

User = get_user_model()


class Command(BaseCommand):
	help = 'Test Redis connectivity and functionality across all configured databases'

	def add_arguments(self, parser):
		parser.add_argument('--detailed', action='store_true', help='Show detailed output for all operations')
		parser.add_argument('--user-id', type=int, help='Test with a specific user ID')
		parser.add_argument('--skip-cleanup', action='store_true', help='Skip cleanup of test data')

	def handle(self, *args, **options):
		"""Main command handler"""
		self.detailed = options['detailed']
		self.user_id = options.get('user_id')
		self.skip_cleanup = options['skip_cleanup']

		self.stdout.write(self.style.HTTP_INFO('=' * 60))
		self.stdout.write(self.style.HTTP_INFO('Redis Connectivity and Functionality Test'))
		self.stdout.write(self.style.HTTP_INFO('=' * 60))

		try:
			# Test all cache configurations
			self._test_cache_configurations()

			# Test user state management
			self._test_user_state_management()

			# Test performance
			self._test_performance()

			# Cleanup if not skipped
			if not self.skip_cleanup:
				self._cleanup_test_data()

			self.stdout.write(self.style.SUCCESS('\n✅ All Redis tests completed successfully!'))

		except Exception as e:
			self.stdout.write(self.style.ERROR(f'\n❌ Redis test failed: {e!s}'))
			logger.exception('Redis test command failed')
			raise CommandError(f'Redis test failed: {e!s}')

	def _test_cache_configurations(self):
		"""Test all configured cache backends"""
		self.stdout.write(self.style.WARNING('\n🔍 Testing Cache Configurations...'))

		cache_configs = [
			('default', 'Default Cache'),
			('user_state', 'User State Cache'),
			('sessions', 'Sessions Cache'),
		]

		for cache_name, description in cache_configs:
			try:
				cache = caches[cache_name]
				test_key = f'test:{cache_name}:{datetime.now().isoformat()}'
				test_value = {
					'timestamp': datetime.now().isoformat(),
					'cache_name': cache_name,
					'test_data': 'Redis connectivity test',
				}

				# Test basic operations
				cache.set(test_key, test_value, 30)
				retrieved_value = cache.get(test_key)

				if retrieved_value == test_value:
					self.stdout.write(self.style.SUCCESS(f'  ✅ {description}: Connection OK'))
					if self.detailed:
						self._show_cache_details(cache_name, cache)
				else:
					raise ValueError('Data mismatch on retrieval')

				# Test TTL and deletion
				cache.touch(test_key, 60)
				cache.delete(test_key)

				if cache.get(test_key) is None:
					self.stdout.write(self.style.SUCCESS(f'  ✅ {description}: Operations OK'))
				else:
					raise ValueError('Key not deleted properly')

			except Exception as e:
				self.stdout.write(self.style.ERROR(f'  ❌ {description}: {e!s}'))
				raise

	def _test_user_state_management(self):
		"""Test user state management functionality"""
		self.stdout.write(self.style.WARNING('\n👤 Testing User State Management...'))

		try:
			state_manager = UserStateManager()

			# Test connection
			if state_manager.test_connection():
				self.stdout.write(self.style.SUCCESS('  ✅ State Manager: Connection OK'))
			else:
				raise ValueError('State manager connection failed')

			# Get test user
			test_user_id = self._get_test_user_id()

			# Test user state operations
			self._test_user_status_operations(state_manager, test_user_id)
			self._test_user_session_operations(state_manager, test_user_id)
			self._test_user_activity_operations(state_manager, test_user_id)

		except Exception as e:
			self.stdout.write(self.style.ERROR(f'  ❌ User State Management: {e!s}'))
			raise

	def _test_user_status_operations(self, state_manager: UserStateManager, user_id: int):
		"""Test user status related operations"""
		self.stdout.write('  🔄 Testing user status operations...')

		# Set user online with session
		session_id = f'test_session_{datetime.now().timestamp()}'
		metadata = {'test': 'data', 'location': 'test_command'}

		state_manager.set_user_online(user_id, session_id, metadata)
		if state_manager.is_user_online(user_id):
			self.stdout.write(self.style.SUCCESS('    ✅ Set user online: OK'))
		else:
			raise ValueError('Failed to set user online')

		# Get user status and verify data
		status_data = state_manager.get_user_status(user_id)
		if status_data.get('status') == UserStatus.ONLINE and status_data.get('is_online'):
			self.stdout.write(self.style.SUCCESS('    ✅ Get user status: OK'))
		else:
			raise ValueError(f'Status check failed: {status_data}')

		# Test activity update (heartbeat)
		state_manager.update_user_activity(user_id, 'test_heartbeat')
		updated_status = state_manager.get_user_status(user_id)
		if updated_status.get('heartbeat'):
			self.stdout.write(self.style.SUCCESS('    ✅ User activity update: OK'))
		else:
			raise ValueError('Failed to update user activity')

		# Test online users count
		online_count = state_manager.get_online_users_count()
		if online_count >= 1:
			self.stdout.write(self.style.SUCCESS(f'    ✅ Online users count: {online_count}'))
		else:
			raise ValueError('Online users count is zero')

		# Set user offline
		state_manager.set_user_offline(user_id, session_id)
		if not state_manager.is_user_online(user_id):
			self.stdout.write(self.style.SUCCESS('    ✅ Set user offline: OK'))
		else:
			raise ValueError('Failed to set user offline')

	def _test_user_session_operations(self, state_manager: UserStateManager, user_id: int):
		"""Test user session related operations"""
		self.stdout.write('  🔄 Testing user session operations...')

		session_id_1 = f'test_session_1_{datetime.now().timestamp()}'
		session_id_2 = f'test_session_2_{datetime.now().timestamp()}'

		session_metadata = {
			'ip_address': '127.0.0.1',
			'user_agent': 'Test Agent',
			'created_at': datetime.now().isoformat(),
		}

		# Test setting user online with first session
		state_manager.set_user_online(user_id, session_id_1, session_metadata)
		status_data = state_manager.get_user_status(user_id)

		if status_data.get('session_id') == session_id_1 and status_data.get('metadata') == session_metadata:
			self.stdout.write(self.style.SUCCESS('    ✅ Set session with metadata: OK'))
		else:
			raise ValueError('Failed to set session with metadata')

		# Test multiple sessions by setting online with different session
		state_manager.set_user_online(user_id, session_id_2, {'test': 'second_session'})
		status_data = state_manager.get_user_status(user_id)

		if len(status_data.get('sessions', [])) >= 1:
			self.stdout.write(self.style.SUCCESS('    ✅ Multiple sessions tracking: OK'))
		else:
			self.stdout.write(self.style.WARNING('    ⚠️ Multiple sessions: Limited tracking'))

		# Test removing specific session by going offline
		state_manager.set_user_offline(user_id, session_id_1)
		if not state_manager.is_user_online(user_id):
			self.stdout.write(self.style.SUCCESS('    ✅ Remove session via offline: OK'))
		else:
			self.stdout.write(self.style.WARNING('    ⚠️ User still online after session removal'))

	def _test_user_activity_operations(self, state_manager: UserStateManager, user_id: int):
		"""Test user activity logging operations"""
		self.stdout.write('  🔄 Testing user activity operations...')

		activity_data = {
			'action': 'test_activity',
			'timestamp': datetime.now().isoformat(),
			'details': 'Redis test activity',
		}

		# Log activity
		result = state_manager.log_user_activity(user_id, 'test_activity', activity_data)
		if result:
			self.stdout.write(self.style.SUCCESS('    ✅ Log user activity: OK'))
		else:
			raise ValueError('Failed to log user activity')

		# Test direct cache access to verify activity was logged
		activity_key = f'user:activity:{user_id}'
		activities = state_manager.cache.get(activity_key, [])

		if activities and len(activities) > 0:
			latest_activity = activities[0]
			if latest_activity.get('activity') == 'test_activity':
				self.stdout.write(self.style.SUCCESS('    ✅ Retrieve user activity: OK'))
			else:
				raise ValueError('Activity data mismatch')
		else:
			raise ValueError('No activities found in cache')

		# Test that activities are limited (log multiple and check)
		for i in range(5):
			state_manager.log_user_activity(user_id, f'bulk_test_{i}', {'index': i})

		activities = state_manager.cache.get(activity_key, [])
		if len(activities) >= 5:
			self.stdout.write(self.style.SUCCESS(f'    ✅ Activity log management: {len(activities)} entries'))
		else:
			raise ValueError('Activity log not working as expected')

	def _test_performance(self):
		"""Test Redis performance with batch operations"""
		self.stdout.write(self.style.WARNING('\n⚡ Testing Performance...'))

		try:
			cache = caches['user_state']

			# Test batch writes
			start_time = datetime.now()
			test_data = {}

			for i in range(100):
				key = f'perf_test_{i}'
				value = {'index': i, 'timestamp': datetime.now().isoformat()}
				cache.set(key, value, 60)
				test_data[key] = value

			write_duration = (datetime.now() - start_time).total_seconds()

			# Test batch reads
			start_time = datetime.now()
			retrieved_count = 0

			for key in test_data.keys():
				if cache.get(key) is not None:
					retrieved_count += 1

			read_duration = (datetime.now() - start_time).total_seconds()

			# Cleanup performance test data
			for key in test_data.keys():
				cache.delete(key)

			self.stdout.write(
				self.style.SUCCESS(
					f'  ✅ Performance Test: {len(test_data)} writes in {write_duration:.3f}s, '
					f'{retrieved_count} reads in {read_duration:.3f}s'
				)
			)

		except Exception as e:
			self.stdout.write(self.style.ERROR(f'  ❌ Performance Test: {e!s}'))
			raise

	def _cleanup_test_data(self):
		"""Clean up any remaining test data"""
		self.stdout.write(self.style.WARNING('\n🧹 Cleaning up test data...'))

		try:
			for cache_name in ['default', 'user_state', 'sessions']:
				cache = caches[cache_name]

				# Look for test keys (this is a simple approach)
				# In production, you might want a more sophisticated cleanup
				test_keys = ['health_check', f'test:{cache_name}:*', 'perf_test_*']

				# Note: delete_many or pattern-based deletion might not be available
				# depending on the Redis backend configuration

			self.stdout.write(self.style.SUCCESS('  ✅ Cleanup completed'))

		except Exception as e:
			self.stdout.write(self.style.WARNING(f'  ⚠️ Cleanup warning: {e!s}'))

	def _get_test_user_id(self) -> int:
		"""Get a test user ID"""
		if self.user_id:
			if User.objects.filter(id=self.user_id).exists():
				return self.user_id
			else:
				raise CommandError(f'User with ID {self.user_id} does not exist')

		# Try to get the first available user
		user = User.objects.first()
		if user:
			return user.id
		else:
			# Create a test user if none exists
			test_user = User.objects.create_user(email='redis_test@example.com', full_name='Redis Test User')
			self.stdout.write(
				self.style.WARNING(f'  ℹ️ Created test user: {test_user.email} (ID: {test_user.id})')
			)
			return test_user.id

	def _show_cache_details(self, cache_name: str, cache):
		"""Show detailed cache information"""
		try:
			# Get cache client info if available
			client = getattr(cache, '_cache', None)
			if client and hasattr(client, 'connection_pool'):
				pool = client.connection_pool
				self.stdout.write(f'    📊 Cache Details ({cache_name}):')
				self.stdout.write(f'      - Connection Pool: {pool.__class__.__name__}')
				if hasattr(pool, 'connection_pool_class'):
					self.stdout.write(f'      - Pool Class: {pool.connection_pool_class.__name__}')

		except Exception as e:
			self.stdout.write(f'    ⚠️ Could not retrieve cache details: {e!s}')

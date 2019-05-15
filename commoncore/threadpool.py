# -*- coding: utf-8 -*-

'''*
	This program is free software: you can redistribute it and/or modify
	it under the terms of the GNU General Public License as published by
	the Free Software Foundation, either version 3 of the License, or
	(at your option) any later version.

	This program is distributed in the hope that it will be useful,
	but WITHOUT ANY WARRANTY; without even the implied warranty of
	MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
	GNU General Public License for more details.

	You should have received a copy of the GNU General Public License
	along with this program.  If not, see <http://www.gnu.org/licenses/>.
*'''

'''
Threadpool borrowed from ActiveState
http://code.activestate.com/recipes/203871-a-generic-programming-thread-pool/
'''

import threading
from time import sleep
from Queue import PriorityQueue

# Ensure booleans exist (not needed for Python 2.2.1 or higher)
try:
	True
except NameError:
	False = 0
	True = not False

class MyPriorityQueue(PriorityQueue):
	def __init__(self):
		PriorityQueue.__init__(self)
		self.counter = 0

	def put(self, item, priority=None):
		priority = self.counter if priority is None else priority
		PriorityQueue.put(self, (priority, self.counter, item))
		self.counter += 1

	def get(self, *args, **kwargs):
		_, _, item = PriorityQueue.get(self, *args, **kwargs)
		return item

class ThreadPool:

	"""Flexible thread pool class.  Creates a pool of threads, then
	accepts tasks that will be dispatched to the next available
	thread."""
	
	def __init__(self, numThreads, timeout=None):

		"""Initialize the thread pool with numThreads workers."""
		self.__timeout = timeout
		self.__abort_event = threading.Event()
		self.__threads = []
		self.__resizeLock = threading.Condition(threading.Lock())
		self.__taskLock = threading.Condition(threading.Lock())
		self.__tasks = MyPriorityQueue()
		self.__isJoining = False
		self.setThreadCount(numThreads)

	def setThreadCount(self, newNumThreads):

		""" External method to set the current pool size.  Acquires
		the resizing lock, then calls the internal version to do real
		work."""
		
		# Can't change the thread count if we're shutting down the pool!
		if self.__isJoining:
			return False
		
		self.__resizeLock.acquire()
		try:
			self.__setThreadCountNolock(newNumThreads)
		finally:
			self.__resizeLock.release()
		return True

	def __setThreadCountNolock(self, newNumThreads):
		
		"""Set the current pool size, spawning or terminating threads
		if necessary.  Internal use only; assumes the resizing lock is
		held."""
		
		# If we need to grow the pool, do so
		while newNumThreads > len(self.__threads):
			newThread = ThreadPoolThread(self)
			self.__threads.append(newThread)
			newThread.start()
		# If we need to shrink the pool, do so
		while newNumThreads < len(self.__threads):
			self.__threads[0].goAway()
			del self.__threads[0]

	def emptyQueue(self):
		self.__resizeLock.acquire()
		self.__tasks = MyPriorityQueue()
		self.__resizeLock.release()

	def getThreadCount(self):

		"""Return the number of threads in the pool."""
		
		self.__resizeLock.acquire()
		try:
			return len(self.__threads)
		finally:
			self.__resizeLock.release()

	def queueTask(self, task, priority=None, args=None, taskCallback=None):

		"""Insert a task into the queue.  task must be callable;
		args and taskCallback can be None."""
		
		if self.__isJoining == True:
			return False
		if not callable(task):
			return False
		
		self.__taskLock.acquire()
		try:
			self.__tasks.put((task, args, taskCallback), priority)
			return True
		finally:
			self.__taskLock.release()

	def getNextTask(self):

		""" Retrieve the next task from the task queue.  For use
		only by ThreadPoolThread objects contained in the pool."""
		
		self.__taskLock.acquire()
		try:
			if self.__tasks.empty():
				return (None, None, None)
			else:
				return self.__tasks.get()
		finally:
			self.__taskLock.release()
	
	def joinAll(self, waitForTasks = True, waitForThreads = True):

		""" Clear the task queue and terminate all pooled threads,
		optionally allowing the tasks and threads to finish."""

		# Mark the pool as joining to prevent any more task queueing
		self.__isJoining = True

		# Wait for tasks to finish
		if waitForTasks:
			while not self.__tasks.empty() and self.__abort_event.isSet() is False:
				sleep(0.1)

		# Tell all the threads to quit
		self.__resizeLock.acquire()
		try:
			# Wait until all threads have exited
			if waitForThreads:
				for t in self.__threads:
					t.goAway()
				for t in self.__threads:
					t.join(self.__timeout)
					# print t,"joined"
					del t
			self.__setThreadCountNolock(0)
			self.__isJoining = True

			# Reset the pool for potential reuse
			self.__isJoining = False
		finally:
			self.__resizeLock.release()


		
class ThreadPoolThread(threading.Thread):

	""" Pooled thread class. """
	
	threadSleepTime = 0.1

	def __init__(self, pool):

		""" Initialize the thread and remember the pool. """
		
		threading.Thread.__init__(self)
		self.__pool = pool
		self.__isDying = False
		
	def run(self):

		""" Until told to quit, retrieve the next task and execute
		it, calling the callback if any.  """
		
		while self.__isDying == False:
			cmd, args, callback = self.__pool.getNextTask()
			# If there's nothing to do, just sleep a bit
			if cmd is None:
				sleep(ThreadPoolThread.threadSleepTime)
			elif callback is None:
				cmd(args)
			else:
				callback(cmd(args))
	
	def goAway(self):

		""" Exit the run loop next time through."""
		
		self.__isDying = True

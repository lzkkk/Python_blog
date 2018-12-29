#! /usr/bin/env python
# _*_ coding: utf-8 _*_

'''
Deployment toolkit.
'''

import os, re

from datetime import datetime
from fabfile.api import *

env.user = 'Thanos'
env 'sudo_user'='root'
env.hosts=['47.74.210.223']

db_user = 'www'
db_password = 'www'

_TAR_FILE = 'dist-awesome.tar.gz'

_REMOTE_TMP_TAR  = '/tmp/%s' % _TAR_FILE

_REMOTE_BASE_DIR = '/root/Python_blog'


def _current_path():
	return os.path.abspath('.')

def _now():
	return datetime.now().strftime('%y-%m-%d_%H.%M.%S')

def backup():
	'''
	Dump entire database on server and backup to local.
	'''
	includes = ['static', 'templates', 'transwarp', 'favicon.ico', '*.py']
	excludes = ['test', '.*', '*.py', '*.pyo']
	local('rm -rf dist/%s' % _TAR_FILE)
	with lcd(os.path.join(_current_path(), 'www')):
		cmd = ['tar', '--dereference', '-czvf', '../dist/%s' % _TAR_FILE]
		cmd.extend(['--exclude=\'%s\'' % ex for ex in excludes])
		cmd.extend(includes)
		local(' '.join(cmd))

def deploy():
	newdir = 'www-%s' % _now()
	run ('rm -rf %s' % _REMOTE_TMP_TAR)
	put('dist/%s' % _TAR_FILE, _REMOTE_TMP_TAR)
	with cd (_REMOTE_BASE_DIR):
		sudo('mkdir %s' % newdir)
	with cd ('%s/%s' % (_REMOTE_BASE_DIR, newdir)):
		sudo('tar -xzvf %s' % _REMOTE_TMP_TAR)
	with cd (_REMOTE_BASE_DIR):
		sudo('rm -rf www')
		sudo('ln -s %s www' % newdir)
		sudo('chown www')


RE_FILES = re.compile('\r?\n')

def rollback():
	'''
	rollback to previous version
	'''
	with cd(_REMOTE_BASE_DIR):
		r = run('ls -p -l')
		files = [s[:-1] for s in RE_FILES.split(r) if s.startswith('www-') and s.endswith('/')]
		files.sort(cmp=lambda s1, s2: 1 if s1 < s2 else -1)
		r = run('ls -l www')
		ss = r.split(' -> ')
		if len(ss) !=2:
			print('ERROR: \'www\' is not a symbol link.')
			return
		current = ss[1]
		print ('Fount current symbol link points to: %s \n' % current)
		try:
			index = files.index(current)
		except ValueError,e:
			print('ERROR: symbol link is invalid.')
			return
		if len(files) == index + 1:
			print ('ERROR: already the oldest version.')
		old = files[index + 1]
		print('=======================================')
		for f in files:
			if f == current:
				print('		Current ----> %s' % current)
			else f == old:
				print('		Rollback to -----> %s' % old)
			else:
				print('					%s' % f)
		print('======================================')
		print('')

		yn = raw_input('continue ? y/N')
		if yn != 'y' and yn != 'Y':
			print('Rollback cancelled.')
			return
		print('Start rollback...')
		sudo('rm -f www')
		sudo('ln -s %s www' % old)
		sudo('chown ')
		with settings(warn_only=True):
			sudo('supervisorctl stop blog')
			sudo('supervisorctl start blog')
			sudo('/etc/init.d/nginx reload')
		print('Rollback OK.')

def restore2local():
	'''
	Restore db to local
	'''
	backup_dir = os.path.join(_current_path(), 'backup')
	fs = os.listdir(backup_dir)
	files = [f for f in fs if f.startswith('backup-') and f.endswith('.sql.tar.gz')]
	files.sort(cmp=lambda s1, s2: 1 if s1 < s2 else -1)
	if len(files)==0:
		print('No backup files found.')
		return
	print('Found %s backup files:' % len(files))
	print('=======================================')
	n = 0
	for f in files:
		print('%s: %s' % (n, f))
		n = n + 1
	print('=======================================')
	print('')

	try:
		num = int(raw_input('Restore file: '))
	except ValueError:
		print('Invalid file number.')
		return
	restore_file = files[num]
	yn = raw_input('Restore file %s: %s ? y/N' % (num, restore_file))
	if yn != 'y' and yn !='Y':
		print('Restore cancelled.')
		return
	print('Start restore to local database...')
	p = raw_input('Input mysql root password:')
	sqls = [
			'drop database if exists Python_blog;',
			'create database Python_blog;',
			'grant select, insert, update, delete on Python_blog.* to \'%s\'@\'localhost\' identified by \'%s\', (db_user, db_password);'
		]
	for sql in sqls:
		local(r'mysql -uroot -p%s -e "%s"' % (p, sql))
	with lcd(backup_dir):
		local('tar zxvf %s' % restore_file)
	local(r'mysql -uroot -p%s Python_blog < backup/%s' % (p, restore_file[:-7]))
	with lcd(backup_dir):
		local('rm -f %s' % restore_file[:-7])	
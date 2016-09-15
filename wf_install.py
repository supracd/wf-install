import xmlrpclib, ConfigParser, logging
from pprint import pprint

WF_SERVER_PROXY = 'https://api.webfaction.com/'

ENV_TEMPLATE = '''DJANGO_SETTINGS_MODULE={app_proj_folder}.settings.prod
DATABASE_URL=postgres://{db_user}:{db_pass}@localhost/{db_name}'''


APP_TYPES = {
"Django 1.4.22": "django1422_mw4421_27",
"Django 1.7.11": "django1711_mw4421_27",
"Django 1.8.9": "django189_mw4421_27",
"Django 1.9.2": "django192_mw4421_27",
"Django 1.9.8": "django198_mw452_27",
}





def get_server_connection(username, password):
	conn = xmlrpclib.ServerProxy(WF_SERVER_PROXY)
	session_id, account = conn.login(username, password)
	return conn, session_id


def list_ips(server, session_id):
	return conn.list_ips(session_id)

def get_server_ip(conn, session_id):
	for ip in list_ips(conn, session_id):
		if ip['is_main']:
			return ip['ip']

def do_site_setup(conn, session_id, app_name, root_domain, sub_domain, db_name, db_user, db_pass, django_version="Django 1.9.8", https=False):
	try:
		logging.info('Creating Domain: {}.{}'.format(sub_domain, root_domain))
		conn.create_domain(session_id, root_domain, sub_domain)
	except Exception as e:
		logging.exception('There was a problem creating the domain')
		raise
	try:
		logging.info('Creating App: {} - {}'.format(app_name, django_version))
		conn.create_app(session_id, app_name, APP_TYPES[django_version])
	except Exception as e:
		logging.exception('There was a problem creating the app')
		raise
	try:
		logging.info('Creating Database: {}'.format(db_name))
		conn.create_db(session_id, db_name, 'postgresql', db_pass, db_user)
	except Exception as e:
		logging.exception('There was a problem creating the database')
		raise
	try:
		logging.info('Creating Website: {}, {}'.format(app_name, '.'.join((sub_domain, root_domain))))
		conn.create_website(session_id,
						  app_name,
						  get_server_ip(conn, session_id),
						  https,
						  ['.'.join((sub_domain, root_domain))],
						  [app_name, '/'])
	except Exception as e:
		logging.exception('There was a problem creating the website')
		raise


if __name__ == '__main__':
	config = ConfigParser.SafeConfigParser()
	logging.basicConfig(format='%(asctime)s|%(levelname)s:%(message)s', filename='wf_install.log', level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')
	try:
		config.read('wf_install.cfg')
		app_name = config.get('DEFAULT', 'app_name')
		wf_user = config.get('webfaction', 'user')
		wf_pass = config.get('webfaction', 'password')
		wf_domain = config.get('webfaction', 'domain')
		wf_root_domain = config.get('webfaction', 'root_domain')
		db_name = config.get('database', 'name')
		db_user = config.get('database', 'user')
		db_pass = config.get('database', 'password')
	except ConfigParser.Error as e:
		print 'There was an error with your configuration, check wf_install.cfg and try again'
		raise

	conn, session_id = get_server_connection(wf_user, wf_pass)

	print ENV_TEMPLATE.format(**{'app_proj_folder': app_name, 'db_user': db_user, 'db_pass': db_pass, 'db_name': db_name})
	do_site_setup(conn, session_id, app_name, wf_root_domain, wf_domain, db_name, db_user, db_pass)

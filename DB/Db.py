from sqlalchemy import *
from sqlalchemy.orm import sessionmaker, relationship, backref, join, scoped_session
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base

from misc import MAX_LOGIN_LENGTH, STAGE_PROJECT_NOT_STARTED, STAGE_PROJECT_STARTED , \
	STAGE_PROJECT_FINISHED, ACTIVITY_CONTRACT_NOT_MADE, ACTIVITY_CONTRACT_MADE, \
	ACTIVITY_CONTRACT_TERMINATED, ACTIVITY_CONTRACT_FINISHED, ROLE_DEVELOPER, ROLE_MANAGER

from dbExceptions import DBException
	
Base = declarative_base()

string = lambda len: Column(String(len))
uniqString = lambda len: Column(String(len), unique=True, nullable=False)
pkey = lambda: Column(Integer, primary_key=True)
fkey = lambda name: Column(Integer, ForeignKey(name, onupdate='CASCADE', ondelete='CASCADE'))
pkeyIndex = lambda: Column(Integer, primary_key=True, index = True)
fkeyIndex = lambda name: Column(Integer, ForeignKey(name, onupdate='CASCADE', ondelete='CASCADE'), index = True)

DATABASE_HOST = "localhost"
DATABASE_USER = "admin"
DATABASE_NAME = "companydb"
DATABASE_PASSWD = "12345"
DATABASE_PORT = 3306

DB_STRING = """mysql+mysqldb://%s:%s@%s:%d/%s""" % \
(DATABASE_USER, DATABASE_PASSWD, DATABASE_HOST, DATABASE_PORT, DATABASE_NAME)


class Company(Base):
	__tablename__ = 'Companies'
	__table_args__ = {'mysql_engine':'InnoDB'}

	id = pkeyIndex()
	name = Column(Text, nullable = False)
	details = Column(Text, nullable = False)

	def __init__(self, name, details):
		self.name = name
		self.details = details

class User(Base):
	__tablename__ = 'Users'
	__table_args__ = {'mysql_engine':'InnoDB'}

	login = Column(String(MAX_LOGIN_LENGTH), primary_key = True)
	password = Column(Text, nullable = False)
	admin = Column(Boolean, default = False)

	def __init__(self, login, password, admin = False):
		self.login = login
		self.password = password
		self.admin = admin

class Employee(Base):
	__tablename__ = 'Employees'
	__table_args__ = {'mysql_engine':'InnoDB'}

	id = pkeyIndex()
	name = Column(Text, nullable = False)
	companyId = fkeyIndex('Companies.id')
	login = Column(String(MAX_LOGIN_LENGTH), 
		ForeignKey('Users.login', onupdate='CASCADE', ondelete='CASCADE'))

	company = relationship(Company, backref=backref('Employees', cascade = "all,delete"))
	user = relationship(User, backref=backref('employee', uselist = False, 
		cascade = "all,delete"))
	
	def __init__(self, name, companyId, login):
		self.name = name
		self.companyId = companyId
		self.login = login

class Project(Base):
	__tablename__ = 'Projects'
	__table_args__ = {'mysql_engine':'InnoDB'}

	id = pkeyIndex()
	name = Column(Text, nullable = False)
	startDate = Column(DateTime, nullable = False)
	stage = Column(Integer, nullable = False, default = STAGE_PROJECT_NOT_STARTED)
	
	def __init__(self, name, startDate, stage = STAGE_PROJECT_NOT_STARTED):
		self.name = name
		self.startDate = startDate
		self.stage = stage

class Contract(Base):
	__tablename__ = 'Contracts'
	__table_args__ = {'mysql_engine':'InnoDB'}

	id = pkeyIndex()
	companyId = fkeyIndex('Companies.id')
	projectId = fkeyIndex('Projects.id')
	activity = Column(Integer, default = ACTIVITY_CONTRACT_NOT_MADE)

	company = relationship(Company, backref=backref('Contracts', cascade = "all,delete"))
	project = relationship(Project, backref=backref('Contracts', cascade = "all,delete"))
	
	def __init__(self, companyId, projectId, stage = ACTIVITY_CONTRACT_NOT_MADE):
		self.companyId = companyId
		self.projectId = projectId
		self.activity = activity

class ProjectEmployee(Base):
	__tablename__ = 'ProjectEmployees'
	__table_args__ = {'mysql_engine':'InnoDB'}


	employeeId = Column(Integer, ForeignKey('Employees.id'), primary_key=True,
		index = True)
	projectId = Column(Integer, ForeignKey('Projects.id'), primary_key=True,
		index = True)
	role = Column(Integer, default = ROLE_DEVELOPER)

	employee = relationship(Employee, backref=backref('Projects', cascade = "all,delete"))
	project = relationship(Project, backref=backref('Employees', cascade = "all,delete"))
	
	def __init__(self, employeeId, projectId, role = ROLE_DEVELOPER):
		self.employeeId = employeeId
		self.projectId = projectId
		self.role = role

class Task(Base):
	__tablename__ = 'Tasks'
	__table_args__ = {'mysql_engine':'InnoDB'}

	id = pkeyIndex()
	name = Column(Text, nullable = False)
	projectId = fkeyIndex('Projects.id')
	plannedTime = Column(Integer, nullable = False)
	completionDate = Column(DateTime)

	project = relationship(Project, backref=backref('Tasks', cascade = "all,delete"))
	
	def __init__(self, name, projectId, plannedTime):
		self.name = name
		self.projectId = projectId
		self.plannedTime = plannedTime

class Job(Base):
	__tablename__ = 'Jobs'
	__table_args__ = {'mysql_engine':'InnoDB'}

	employeeId = Column(Integer, ForeignKey('Employees.id'), primary_key=True, 
		index = True)
	taskId = Column(Integer, ForeignKey('Tasks.id'), primary_key=True, 
		index = True)
	startDate = Column(DateTime)
	completionDate = Column(DateTime)
	description = Column(Text)

	employee = relationship(Employee, backref=backref('Jobs', cascade = "all,delete"))
	task = relationship(Task, backref=backref('Jobs', cascade = "all,delete"))

	def __init__(self, employeeId, projectId, startDate, completionDate, description):
		self.employeeId = employeeId
		self.projectId = projectId
		self.startDate = startDate
		self.completionDate = completionDate
		self.description = description


class TasksDependency(Base):
	__tablename__ = 'TasksDependencies'
	__table_args__ = {'mysql_engine':'InnoDB'}
	
	masterId = Column(Integer, ForeignKey('Tasks.id'), primary_key=True, 
		index = True)
	slaveId = Column(Integer, ForeignKey('Tasks.id'), primary_key=True,
		index = True)

	def __init__(self, masterId, slaveId):
		self.masterId = masterId
		self.slaveId = slaveId


tableClasses = {
	'Companies': Company, 
	'Users': User, 
	'Employees': Employee, 
	'Projects': Project, 
	'Contracts': Contract,
	'ProjectEmployees': ProjectEmployee,
	'Tasks': Task,
	'Jobs': Job,
	'TasksDependencies': TasksDependency}

class Database:
	instance = None
	engine = create_engine(DB_STRING, convert_unicode=True, echo = False,
		encoding="utf-8")
	adminInstance = None
	
	def __init__(self):
		Base.metadata.create_all(self.engine)
		self.Session = scoped_session(sessionmaker(bind=self.engine))
		self.session = self.Session()
		self.metadata = Base.metadata

	def commit(self):
		self.session.commit()

	def rollback(self):
		self.session.rollback()

	def add(self, obj):
		self.session.add(obj)

	def addAll(self, objs):
		self.session.add_all(objs)

	def delete(self, *args, **kwargs):
		self.session.delete(*args, **kwargs)
		
	def query(self, *args, **kwargs):
		return self.session.query(*args, **kwargs)

	def clear(self):
		meta = MetaData()
		meta.reflect(bind=self.engine)
		for table in reversed(meta.sorted_tables):
			self.engine.drop(table)
		Base.metadata.create_all(self.engine)

	
	def getXbyY(self, x, y, value):
		try:
			cls = globals()[x]
			return self.query(cls).filter(getattr(cls, y) == value).one()
		except NoResultFound:
			raise DBException("NoResultFound")
			return None

	def addUnique(self, obj):
		try:
			self.add(obj)
		except IntegrityError:
			raise DBException("IntegrityError")

def getDbInstance():
	if Database.instance is None:
		Database.instance = Database()
	return Database.instance

dbi = getDbInstance()

#def getAdminInstance():
#	if Database.adminInstance is None:
#		newUser = User('admin', 'admin', True)
#		dbi.addUnique(newUser)
#		Database.adminInstance = newUser
#	return Database.adminInstance

#admin = getAdminInstance()
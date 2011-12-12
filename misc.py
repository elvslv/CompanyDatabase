MAX_LOGIN_LENGTH = 20

MIN_LOGIN_LENGTH = 5
MIN_PASSWORD_LENGTH = 5

STAGE_PROJECT_NOT_STARTED = 0
STAGE_PROJECT_STARTED = 1
STAGE_PROJECT_FINISHED = 2

ACTIVITY_CONTRACT_MADE = 0
ACTIVITY_CONTRACT_TERMINATED = 1

STAGE_TASK_NOT_STARTED = 0
STAGE_TASK_IN_PROGRESS = 1
STAGE_TASK_FINISHED = 2

ROLE_DEVELOPER = 0
ROLE_MANAGER = 1

activity = ["Contract is made", "Contract is terminated"]
role = ["Developer", "Manager"]
state = ["Task isn't started", "Task is in progerss", "Task is finished"]

convertTableNameToColumnName = {
	'companies': 'company', 
	'users': 'user', 
	'employees': 'employee', 
	'projects': 'project', 
	'contracts': 'contract',
	'projectEmployees': 'employee on project',
	'tasks': 'task',
	'jobs': 'job',
	'tasksDependencies': 'task dependency'
}
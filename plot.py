import datetime
import math
from DB.Db import *

colors = ['blue', 'red', 'green']

def addPlannedTime(startDate, plannedTime):
	newDate = startDate
	pt = plannedTime
	while pt:
		if newDate.weekday() in (5, 6):
			newDate += datetime.timedelta(days = 2)
		if newDate.hour > 16:
			newDate += datetime.timedelta(hours = min(24 - newDate.hour, pt))
			pt -= min(24 - newDate.hour, pt)
		elif pt > 8:
			newDate += datetime.timedelta(hours = 24)
			pt -= 8
		else:
			newDate += datetime.timedelta(hours = pt)
			pt = 0
	return newDate

def createTask(task):
	dependsOn = dbi.query(Task).filter(TasksDependency.slaveId == 
		task.id).filter(Task.id == TasksDependency.masterId).all()
	return GanttTask(task.name, task.state, task, dependsOn, task.jobs, task.project)

def minDate():
	return datetime.datetime(year = datetime.MINYEAR, month = 1, day = 1)

def maxDate():
	return datetime.datetime(year = datetime.MAXYEAR, month = 12, day = 31)

class GanttTask():
	def __init__(self, name, state, task, dependsOn, jobs, project, beginDate = None, endDate = None):
		self.name = name
		self.state = state
		self.jobs = jobs
		self.task = task
		self.project = project
		self.dependsOn = dependsOn
		self.beginDate = beginDate if beginDate else None 
		self.beginDate = self.getStartDate()
		self.endDate = endDate if endDate else None 
		self.endDate = self.getEndDate()

	def getStartDate(self):
		if not self.beginDate:
			if self.state == STAGE_TASK_NOT_STARTED:
				if not len(self.dependsOn):
					self.beginDate = self.project.startDate
				else:
					time = minDate()
					for t in self.dependsOn:
						if t.endDate > time:
							time = t.getEndDate()
					self.beginDate = time
			else:
				time = maxDate()
				for j in self.jobs:
					if j.startDate < time:
						time = j.startDate
				self.beginDate = time
		self.beginDate = self.beginDate.replace(minute = 0, second = 0, microsecond = 0)
		return self.beginDate

	def getEndDate(self):
		if not self.endDate:
			if self.state == STAGE_TASK_FINISHED:
				time = minDate()
				for j in self.jobs:
					if j.completionDate > time:
						time = j.completionDate
				self.endDate = time
			elif self.state == STAGE_TASK_IN_PROGRESS:
				time = minDate()
				for j in self.jobs:
					time = max(time, j.completionDate, 
						addPlannedTime(j.startDate, self.task.plannedTime))
				self.endDate = time
			else:
				self.endDate = datetime.datetime.today()
		self.endDate = self.endDate.replace(minute = 0, second = 0, microsecond = 0)
		return self.endDate

def getHours(d1, d2):
	td = d2 - d1
	return math.trunc(td.total_seconds() / 3600)
	
class GanttChart():
	def __init__(self, tasks):
		self.tasks = []
		for task in tasks:
			self.tasks.append(createTask(task))

	def getLastDate(self):
		time = minDate()
		for task in self.tasks:
			time = max(task.beginDate, task.endDate, time)
		return time

	def getFirstDate(self):
		time = maxDate()
		for task in self.tasks:
			time = min(time, task.beginDate)
		return time

	def generateDiagram(self):
		firstDate = self.getFirstDate()
		lastDate = self.getLastDate()
		allHours = getHours(firstDate, lastDate)
		result = '<html><body><table width = "100%" border = "1">'
		for task in self.tasks:
			result += '<tr>'
			result += '<td>%s</td>' % task.name
			h = getHours(firstDate, task.beginDate)
			if h:
				result += '<td colspan = "%d">&nbsp</td>' % h
			result += '<td colspan = "%d" style = "background-color: %s">&nbsp</td>' % (
				getHours(task.beginDate, task.endDate), colors[task.state])
			h = getHours(task.endDate, lastDate)
			if h:
				result += '<td colspan = "%d">&nbsp</td>' % h
			result += '</tr>'
			
		result += '<tr>'
		result += '<td>Date</td>'
		result += '<td colspan = "%d">%s</td>' % (24 - firstDate.hour, firstDate.date())
		newDate = firstDate + datetime.timedelta(hours = (24 - firstDate.hour))
		h = 0
		hours = allHours - (24 - firstDate.hour)
		while hours > 0:
			newDate +=  datetime.timedelta(hours = 24 * h)
			result += '<td colspan = "24">%s</td>' % newDate.date()
			h += 1
			hours -= 24
		result += '</tr>'
		
		result += '<tr>'
		result += '<td>Hour</td>'
		for h in range(allHours):
			newDate = (firstDate + datetime.timedelta(hours = h))
			result += '<td style = "font-size: 6;">%s</td>' % newDate.hour
		result += '</tr>'
		
		result += '</table></body></html>'
		diagram = open('diagram.html', 'w')
		diagram.write(result)
		return result
		
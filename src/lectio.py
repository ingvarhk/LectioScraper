import re
import requests
from lxml import html
from bs4 import BeautifulSoup

#Packages
import schedule, schools

class Lectio:

	def __init__(self, Username, Password, SchoolId):
		self.Username = Username
		self.Password = Password
		self.SchoolId = SchoolId

		LOGIN_URL = "https://www.lectio.dk/lectio/{}/login.aspx".format(self.SchoolId)

		# Start requests session and get eventvalidation key
		session = requests.Session()
		result = session.get(LOGIN_URL)
		# print(result.text)
		tree = html.fromstring(result.text)
		authenticity_token = list(set(tree.xpath("//input[@name='__EVENTVALIDATION']/@value")))[0]

		# Create payload
		payload = {
			"m$Content$username": self.Username,
			"m$Content$password": self.Password,
			"m$Content$passwordHidden": self.Password,
			"__EVENTVALIDATION": authenticity_token,
			"__EVENTTARGET": "m$Content$submitbtn2",
			"__EVENTARGUMENT": "",
			"masterfootervalue": "X1!ÆØÅ",
			"LectioPostbackId": ""
		}

		# Perform login
		result = session.post(LOGIN_URL, data=payload, headers=dict(referer=LOGIN_URL))

		# Getting student id
		dashboard = session.get("https://www.lectio.dk/lectio/" + self.SchoolId + "/forside.aspx")
		soup = BeautifulSoup(dashboard.text, features="html.parser")
		studentIdFind = soup.find("a", {"id": "s_m_HeaderContent_subnavigator_ctl05"}, href=True)

		if (studentIdFind == None):
			raise Exception("Forkerte login detaljer")
			exit()
		else:
			self.studentId = (studentIdFind['href']).replace("/lectio/" + self.SchoolId + "/OpgaverElev.aspx?elevid=", '')
			self.Session = session

	def getSchools(self):
		result = schools.schools(self)
		return result
	
	def getSchedule(self, week):
		result = schedule.schedule(self, self.Session, self.SchoolId, self.studentId, week)
		return result

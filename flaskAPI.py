from flask import Flask, jsonify
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
import GLOBALS

def list_instances(compute, project, zone):

	result = compute.instances().list(project=project, zone=zone).execute()
	return result.get('items')


app = Flask(__name__)

@app.route('/api/instances',methods=['GET'])
def GET_instances():

	#VARS
	JSON={}
	INSTANCES=[]
	itemCount=0


	#Obtain Credentials and Scope
	credentials = GoogleCredentials.get_application_default()
	
	#Compute API initialization
	compute = discovery.build('compute', 'v1', credentials=credentials)

	#Read through all zones to pull the instances in the zone
	for zone in GLOBALS.ZONES:
		instances = list_instances(compute,GLOBALS.PROJECT,zone)	
		if(instances == None):
			continue

		for instance in instances:
		    INSTANCES.append({itemCount:str(instance['name'])})
		    itemCount+=1
		

	JSON['max_index']=itemCount-1
	JSON['instances']=INSTANCES

	returned_json = jsonify(JSON)

	
	
	return returned_json

if __name__ == '__main__':
	app.run(host='127.0.0.1', port=8080, debug=True)

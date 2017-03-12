from flask import Flask, jsonify
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
import GLOBALS

def list_instances(compute, project, zone):

	result = compute.instances().list(project=project, zone=zone).execute()
	return result.get('items')


app = Flask(__name__)

#Take the URL supplied by the GCP API for zone and extract the 
def zone_explode(zoneURL):

	if(zoneURL==None):
		return ""

	splitURL=zoneURL.split('/')
	
	return splitURL[len(splitURL)-1]


#Build Instances JSON
#If no zone is specified then all zones will be investigated
#If zone is supplied then only the instances in that zone will be returned
def build_instances_json(zone=None):

	#VARS
	JSON={}
	INSTANCES=[]
	itemCount=0
	ZONES=[zone]
	
	print(ZONES)

	if(ZONES==[None]):
		ZONES=GLOBALS.ZONES

	#Obtain Credentials and Scope
	credentials = GoogleCredentials.get_application_default()
	
	#Compute API initialization
	compute = discovery.build('compute', 'v1', credentials=credentials)

	#Read through all zones to pull the instances in the zone
	for zone in ZONES:
		instances = list_instances(compute,GLOBALS.PROJECT,zone)	
		if(instances == None):
			continue

		
		for instance in instances:
	            zone=zone_explode(str(instance['zone']))
			
		    if( "quick-instance" not in instance['name']):
			continue

		    INSTANCES.append({"name":str(instance['name']),"zone":zone})
		    itemCount+=1
		

	JSON['object_count']=itemCount
	JSON['instances']=INSTANCES

	return jsonify(JSON)


	

@app.route('/api/instances',methods=['GET'])
def GET_instances():

	return build_instances_json()


@app.route('/api/instances/<string:zone>', methods=['GET'])
def get_instances_zone(zone):

	#TODO - ADD check for actual zone and throw error page if wrong	
	return build_instances_json(zone)

if __name__ == '__main__':
	app.run(host='127.0.0.1', port=8080, debug=True)

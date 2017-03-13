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


#AUTH and SCOPE
def get_authScope(resource):
	

	#Obtain Credentials and Scope
	credentials = GoogleCredentials.get_application_default()
 
	#Compute API initialization
	return discovery.build(resource, 'v1', credentials=credentials)


#Build Instances JSON
#If no zone is specified then all zones will be investigated
#If zone is supplied then only the instances in that zone will be returned
def build_instances_json(compute, zone=None):

	#VARS
	JSON={}
	INSTANCES=[]
	itemCount=0
	ZONES=[zone]
	
	print(ZONES)

	if(ZONES==[None]):
		ZONES=GLOBALS.ZONES

	
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


#Delete Instance in zone
def delete_instance(compute, zone, name):
	project=GLOBALS.PROJECT
	return compute.instances().delete(project=project,zone=zone,instance=name).execute()

	

@app.route('/api/list/instances',methods=['GET'])
def GET_instances():
	
	compute=get_authScope('compute')
	return build_instances_json(compute)


@app.route('/api/list/instances/<string:zone>', methods=['GET'])
def GET_instances_zone(zone):

	#TODO - ADD check for actual zone and throw 404 error if wrong	
	compute=get_authScope('compute')
	return build_instances_json(compute,zone)

@app.route('/api/delete/instances/<string:zone>/<string:name>', methods=['DELETE'])
def DELETE_inst(zone,name):
	compute=get_authScope('compute')
	#if instance exists return 200 with success
	#else thrown 404
	status = delete_instance(compute,zone,name)

	print(status.keys())

	return "Success"
	
if __name__ == '__main__':
	app.run(host='127.0.0.1', port=8080, debug=True)

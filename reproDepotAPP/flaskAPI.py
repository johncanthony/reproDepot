from flask import Flask,jsonify
from flask.ext.api import status
from oauth2client.client import GoogleCredentials
from googleapiclient import discovery
import GLOBALS
import time

#Use googleapiclient to pull list of compute instances from zone
def list_instances(compute, project, zone):

	result = compute.instances().list(project=project, zone=zone).execute()
	return result.get('items')


app = Flask(__name__)


#Check Zone for Validity
def check_zone(zone):
	return(zone in GLOBALS.ZONES)


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
def build_instances_json(compute,project, zone=None):

	#VARS
	JSON={}
	INSTANCES=[]
	itemCount=0
	ZONES=[zone]
	
	print(ZONES)

	if(ZONES==[None]):
		ZONES=GLOBALS.ZONES
	else:	
		if(not check_zone(zone)):
			return "Zone Not Found", status.HTTP_404_NOT_FOUND

	
	#Read through all zones to pull the instances in the zone
	for zone in ZONES:
		instances = list_instances(compute,project,zone)	
		
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


#Create Quick Instance
def create_instance(compute,zone="us-central1-c"):

    	#Genereate Name
	uid=int(time.time()*1000)
	name="quick-instance"+str(uid)
	print("Name:"+str(name))

	# Get the latest Debian Jessie image.
	image_response = compute.images().getFromFamily(project='debian-cloud', family='debian-8').execute()
	source_disk_image = image_response['selfLink']

	# Configure the machine
	machine_type = "zones/%s/machineTypes/n1-standard-1" % zone

	config = {
		'name': name,
		'machineType': machine_type,

		# Specify the boot disk and the image to use as a source.
		'disks': [
			{
				'boot': True,
				'autoDelete': True,
				'initializeParams': {
					'sourceImage': source_disk_image,
				}
			}
		],

		# Specify a network interface with NAT to access the public
		# internet.
		'networkInterfaces': [{
			'network': 'global/networks/default',
			'accessConfigs': [
				{'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}
			]
		}],

		# Allow the instance to access cloud storage and logging.
		'serviceAccounts': [{
			'email': 'default',
			'scopes': [
				'https://www.googleapis.com/auth/devstorage.read_write',
				'https://www.googleapis.com/auth/logging.write'
			]
		}]


	}

	response=compute.instances().insert(project=GLOBALS.PROJECT,zone=zone,body=config).execute()

	return response['status']

#Delete Instance in zone
def delete_instance(compute, zone, name):
	
	project=GLOBALS.PROJECT

	return compute.instances().delete(project=project,zone=zone,instance=name).execute()

	

@app.route('/api/instances',methods=['GET'])
def GET_instances():
	
	compute=get_authScope('compute')
	return build_instances_json(compute,GLOBALS.PROJECT)




@app.route('/api/instances/<string:zone>', methods=['GET'])
def GET_instances_zone(zone):

	#TODO - ADD check for actual zone and throw 404 error if wrong	
	compute=get_authScope('compute')

	return build_instances_json(compute,GLOBALS.PROJECT,zone)



@app.route('/api/instances/<string:zone>/<string:name>', methods=['DELETE'])
def DELETE_inst(zone,name):
	compute=get_authScope('compute')
	
	#Check Zone Validity
	if(not check_zone(zone)):
		return "Zone Not Found", status.HTTP_404_NOT_FOUND
	

	return delete_instance(compute,zone,name)



@app.route('/api/instances/<string:zone>',methods=['POST'])
def POST_create_instances_zone(zone="us-central1-c"):

	compute=get_authScope('compute')
	print(zone)
	#Check Zone Validity
	if(not check_zone(zone)):
		return "Zone Not Found", status.HTTP_404_NOT_FOUND

	create_instance(compute,zone)	

	return "Created"

@app.route('/api/instances',methods=['POST'])
def POST_create_instances():

	zone="us-central1-c"
	compute=get_authScope('compute')
	#Check Zone Validity
	if(not check_zone(zone)):
		return "Zone Not Found", status.HTTP_404_NOT_FOUND

	x=create_instance(compute)	
	print(x)
	
	return "Created"

	
if __name__ == '__main__':
	app.run(host='127.0.0.1', port=8080, debug=True)

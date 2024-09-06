from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import boto3
import os

app = Flask(__name__)
CORS(app)

stop_allocation = False
allocated_ips = []
desired_ips = [
    '44.219.200','43.204.22','43.204.25'
]

def get_first_three_parts(ip_address):
    return '.'.join(ip_address.split('.')[:3])

def create_elastic_ip_generator(ec2_client):
    global stop_allocation
    
    try:
        while not stop_allocation:

            try:
                
                response = ec2_client.allocate_address(Domain='vpc')
                ip_address = response['PublicIp']
                allocation_id = response['AllocationId']
                release = 0
                print(f"Allocated IP address: {ip_address}")
                yield f"Suggested {ip_address}"
                for desired_ip in desired_ips:
                    print("DESIRED IP ADDRESS",desired_ip )
                    
                    if get_first_three_parts(ip_address) == get_first_three_parts(desired_ip):
                        allocated_ips.append({'ip_address': ip_address, 'status': 'success'})
                        yield f"Allocated {ip_address}"
                        desired_ips.remove(desired_ip)
                        release = 1
                         
                if release == 0:
                    ec2_client.release_address(AllocationId=allocation_id)
                    print(f"Released IP address: {ip_address}")
            except Exception as e:
                yield f"Error: {str(e)}\n"
        return {'allocated_ips': allocated_ips}
    except Exception as e:
        yield f"Error: {str(e)}\n"

    

@app.route('/allocate-ip', methods=['POST'])
def allocate_ip():
    global stop_allocation
    stop_allocation = False

    data = request.json
    aws_access_key_id = data['aws_access_key_id']
    aws_secret_access_key = data['aws_secret_access_key']
    region = 'us-east-1'  # You can make this dynamic if needed

    ec2_client = boto3.client(
        'ec2',
        region_name=region,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

    # Return the generator that streams IP allocations
    return Response(create_elastic_ip_generator(ec2_client), content_type='text/plain')

@app.route('/stop', methods=['POST'])
def stop_allocation_route():
    global stop_allocation
    stop_allocation = True
    return jsonify({'status': 'PROCESS STOPPED'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'HOME PAGE'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

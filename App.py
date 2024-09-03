from flask import Flask, request, jsonify
from flask_cors import CORS
import boto3
import time
import os
app = Flask(__name__)
CORS(app)  

stop_allocation = False


desired_ips = [
    '43.204.22','43.204.25', '43.204.24', '43.204.23', '43.204.28', '43.204.30',  
    '43.205.232', '43.205.113', '43.205.207', '43.205.178', '43.205.126', '43.205.124', '43.205.113', 
    '43.205.208', '43.205.191', '43.205.94', '43.205.228', '43.205.210', '43.205.191', '43.205.120', '43.205.238', '43.205.207', '43.205.110', '43.205.121', 
    '43.205.107', '43.205.123', '43.205.92', '43.205.213', '43.205.217', '43.205.130', '43.205.220', '43.205.194', '43.205.178', 
    '43.205.210', '43.205.111', '43.205.215', '43.205.253', '43.205.49', '43.205.52', '43.205.153', '43.205.50', 
    '43.205.94', '43.205.208', '43.205.217', '43.205.142', '43.205.146'
]

def get_first_three_parts(ip_address):
    print('.'.join(ip_address.split('.')[:3]))
    return '.'.join(ip_address.split('.')[:3])

def create_elastic_ip(ec2_client):
    global stop_allocation
    allocated_ips = []

    try:
        while not stop_allocation and desired_ips:
            for desired_ip in desired_ips:
                if stop_allocation:
                    break

                try:
                    response = ec2_client.allocate_address(Domain='vpc')
                    ip_address = response['PublicIp']
                    allocation_id = response['AllocationId']

                    print(f"Allocated IP address: {ip_address}")

                    # Compare the first three parts of the IP addresses
                    if get_first_three_parts(ip_address) == get_first_three_parts(desired_ip):
                        allocated_ips.append({'ip_address': ip_address, 'status': 'success'})
                        desired_ips.remove(desired_ip)  # Remove allocated IP from list
                        print(f"Desired IP address {desired_ip} has been allocated!")
                    else:
                        ec2_client.release_address(AllocationId=allocation_id)
                        print(f"Released IP address: {ip_address}")

                except Exception as e:
                    return {'status': 'error', 'message': str(e)}

                time.sleep(2)

        return {'status': 'completed' if not desired_ips else 'stopped', 'allocated_ips': allocated_ips}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
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

    result = create_elastic_ip(ec2_client)
    return jsonify(result)

@app.route('/stop', methods=['POST'])
def stop_allocation_route():
    global stop_allocation
    stop_allocation = True
    return jsonify({'status': 'stopping process'})

@app.route('/', methods=['GET'])
def home():
    return jsonify({'status': 'HOME PAGE'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

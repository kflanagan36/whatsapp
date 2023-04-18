from flask import Flask, request, jsonify
import openai
import vonage
import json

app = Flask(__name__)

def openai_call(prompt):
    openai.api_key = '<API_KEY>'
    prompt = (prompt.lower()).strip()
    model_engine = openai.Completion.create(
        engine='text-davinci-002',
        prompt=prompt,
        max_tokens=60,
        n=1,
        stop=None,
        temperature=0.5,
    )
    response = model_engine.choices[0].text
    output = response.rstrip().replace('\n', '')
    return output

def send_sms(to_number, message):
    sms_key = '<API KEY>'
    sms_secret = '<SECRET KEY>'
    sms_api = vonage.Client(key=sms_key, secret=sms_secret)
    try:
        userData = sms_api.send_message({'from': 'Vonage APIs', 'to': str(to_number), 'text': message})
        return userData
    except Exception as e:
        print(e)
        return None

@app.route('/answer', methods=['POST'])
def answer():
    if request.method != 'POST':
        return jsonify({'error': 'Invalid HTTP method'})
        
    # Run a Dialogflow detection query on the message given
    data = request.json
    message = data['message']
    to_number = int(data['from'])
    phone_number = data['phoneNumber']
    platform = data['platform']

    response = send_sms(to_number, message)
    
    if response is None:
        return jsonify({'error': 'Failed to send message'})

    json_data = json.loads(response)
    response_msgs = []
    slots = []
    message_ids = []
    
    for msg in json_data['messages']:
        slot = msg['message-id']
        if platform == 'whatsapp':
            message_id = msg['client-ref']
        else:
            message_id = msg['message-id']
        message_ids.append(message_id)
        response_msgs.append(msg['status-text'])
        slots.append(slot)

    response = {} 
    prompt = "What is your question?"
    response['msg'] = openai_call(prompt)
    response['messages'] = response_msgs
    response['platform'] = platform
    response['phone_number'] = phone_number
    response['slots'] = slots
    response['message_ids'] = message_ids
    return jsonify(response)

if __name__ == "__main__":
   app.run(debug=True)

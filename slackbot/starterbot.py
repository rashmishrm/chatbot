import os, sys, subprocess
import time
from slackclient import SlackClient

parent = os.path.dirname(os.path.realpath(__file__))

sys.path.append(parent + '/MITIE/mitielib')

from mitie import *

slack_client = SlackClient('xoxb-279929363731-AbxTTfZmDUIqPq1MuwjvhwX4')
BOT_NAME = 'jarvis'

def get_bot_id():
    api_call = slack_client.api_call("users.list")
    if api_call.get('ok'):
        # retrieve all users so we can find our bot
        users = api_call.get('members')
        for user in users:
            if 'name' in user and user.get('name') == BOT_NAME:
                print("Bot ID for '" + user['name'] + "' is " + user.get('id'))
                return str(user.get('id'))
    else:
        print("could not find bot user with the name " + BOT_NAME)


# starterbot's ID as an environment variable
BOT_ID = get_bot_id()

print(' BOT ID  ', BOT_ID)
# constants
AT_BOT = "<@" + BOT_ID + ">"
EXAMPLE_COMMAND = "jarvis"
ner = None

def handle_command(command, channel):
    """
        Receives commands directed at the bot and determines if they
        are valid commands. If so, then acts on the commands. If not,
        returns back what it needs for clarification.
    """
    response = "Not sure what you mean. Use the *" + EXAMPLE_COMMAND + \
               "* command with numbers, delimited by spaces."
    if command.startswith(EXAMPLE_COMMAND):
        command = ' '.join(command.split(' ')[1:])
        entities = entity_extraction(command)
        label = predict(command )
        if label is None:
            print ' Prediction failed !!!!!!'

        response = ' ' + label + ' is predicted '

        if len(entities) > 0 :
            response += " It's a " + str(entities[0][1]).lower()

        slack_client.api_call("chat.postMessage", channel=channel,
                          text=response, as_user=True)

def predict(input):
    os.environ['TEST_X'] = input
    os.environ['TRAINED_RESULTS'] = os.environ.get('PRED_LABEL', '/home/rentala/PycharmProjects/chatbot/cnn/trained_results_1512259834')
    #print os.path.abspath(__file__)
    #try and get cnn from here ?
    slackbot_dir = os.path.dirname(sys.modules['__main__'].__file__)
    predict_loc = '/home/rentala/PycharmProjects/chatbot/cnn/predict.py'

    p = subprocess.Popen([sys.executable, predict_loc], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, err = p.communicate()

    label = os.environ.get('PRED_LABEL', None)
    return output

def entity_extraction(command):
    tokens = tokenize(command)
    entities = ner.extract_entities(tokens)
    print("\nEntities found:", entities)
    print("\nNumber of entities detected:", len(entities))
    return entities

def parse_slack_output(slack_rtm_output):
    """
        The Slack Real Time Messaging API is an events firehose.
        this parsing function returns None unless a message is
        directed at the Bot, based on its ID.
    """
    output_list = slack_rtm_output
    if output_list and len(output_list) > 0:
        for output in output_list:
            if output and 'text' in output and AT_BOT in output['text']:
                # return text after the @ mention, whitespace removed
                return output['text'].split(AT_BOT)[1].strip().lower(), \
                       output['channel']
    return None, None



if __name__ == "__main__":
    READ_WEBSOCKET_DELAY = 1 # 1 second delay between reading from firehose
    if slack_client.rtm_connect():
        print("\n ---  \n StarterBot connected and running! \n --- \n ---")

        print("loading NER model...")
        ner = named_entity_extractor('ner_model.dat')

        print("\nTags output by this NER model:", ner.get_possible_ner_tags())

        print("\n Waiting for message \n \n")

        while True:
            command, channel = parse_slack_output(slack_client.rtm_read())
            if command and channel:
                handle_command(command, channel)
            time.sleep(READ_WEBSOCKET_DELAY)
    else:
        print("Connection failed. Invalid Slack token or bot ID?")



from audioop import reverse
from flask import Flask, render_template
import os
import atexit
import autoquester

from apscheduler.schedulers.background import BackgroundScheduler
from quests.quest_core_v2 import complete_quest, start_quest

app = Flask(__name__)

def autoquest():
    print("Autoquesting")
    autoquester.complete_quests()
    autoquester.start_quests()

scheduler = BackgroundScheduler()
# scheduler.add_job(autoquest, 'cron', second=10)
scheduler.add_job(func=autoquest, trigger="interval", seconds=1200)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())



@app.route("/")
def landing():
    return render_template('home.html')

@app.route("/autoquesting")
def autoquest():
    autoquester.complete_quests()
    autoquester.start_quests()
    return render_template('home.html')

@app.route("/logs/start_logs")
def start_logs():
    
    files = os.listdir("logs/quests_started")
    
    return render_template('start_logs.html', logfiles = reversed(files))
    
@app.route("/logs/complete_logs")
def complete_logs():
    files = os.listdir("logs/quests_completed")
    
    return render_template('complete_logs.html', logfiles = reversed(files))

@app.route("/logs/error_logs")
def error_logs():
    files = os.listdir("logs/errors")
    
    return render_template('error_logs.html', logfiles = reversed(files))

@app.route("/logs/<type>/<file>")
def show_log(file, type=None):
    
    start_path = 'logs/quests_started'
    
    paths = {
        'start': 'logs/quests_started',
        'complete': 'logs/quests_completed',
        'error': 'logs/errors',
    }
    
    
    start_path = paths[type]
    path = f"{start_path}/{file}"


    with open(path, "r") as f:
        return render_template('log.html', logfiles = reversed(f.readlines()))

if __name__ == '__main__':
      
    # run() method of Flask class runs the application 
    # on the local development server.

    app.run()
import os, json, time
from flask import Flask, render_template_string, request, url_for, send_from_directory, redirect

app = Flask(__name__)

DATA_FILE = "data.json"
LOG_FILE = "logs.txt"
AUDIO_DIR = "audio"
SYSTEM_PIN = "3136"

RULES = [
    "No hitting or touching in any way that might hurt somebody else mentally or for real.",
    "Do NOT disrespect babysitters, parents, your siblings, or anybody in general.",
    "Do not under any circumstance, even if you are asked, throw ANYTHING, especially when you are told not to.",
    "When someone tells you to do something, DO IT without arguments.",
    "Stay in timeout when told!",
    "Follow all directions and rules from adults or whoever is watching you.",
    "Be safe. If something you are doing you don't think is safe, then DON'T do it!",
    "Other (not on this list)"
]

# Initialize data
if not os.path.exists(DATA_FILE):
    data = {"points":0, "days":[]}
    with open(DATA_FILE,"w") as f:
        json.dump(data,f)
else:
    with open(DATA_FILE) as f:
        try:
            data = json.load(f)
        except:
            data = {"points":0, "days":[]}

def log(msg):
    timestamp = time.strftime("[%Y-%m-%d %H:%M:%S]")
    with open(LOG_FILE,"a") as f:
        f.write(f"{timestamp} {msg}\n")

def current_day():
    if not data["days"]:
        data["days"].append({"id":1, "strikes":[]})
    return data["days"][-1]

def save_data():
    with open(DATA_FILE,"w") as f:
        json.dump(data,f)

HTML = """
<!DOCTYPE html>
<html>
<head>
<title>Kids Rewards System</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
body{margin:0;font-family:Arial,sans-serif;background:#ececec;}
header{background:#4CAF50;color:white;padding:20px;text-align:center;font-size:24px;}
.container{padding:20px;display:flex;flex-wrap:wrap;gap:20px;justify-content:center;}
.card{background:white;padding:15px;border-radius:10px;box-shadow:0 2px 5px rgba(0,0,0,0.2);min-width:200px;flex:1;}
button{padding:10px 15px;margin-top:5px;font-size:16px;border:none;border-radius:8px;cursor:pointer;background:#4CAF50;color:white;}
button:hover{background:#45a049;}
select{width:100%;padding:8px;margin-top:5px;border-radius:5px;border:1px solid #ccc;font-size:16px;}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);justify-content:center;align-items:center;}
.modal-content{background:white;padding:20px;border-radius:10px;max-width:500px;}
audio{margin-top:10px;display:block;width:100%;}
</style>
</head>
<body>
<header>
Day {{ day['id'] }} | Strikes today: {{ strikes }} | Total Points: {{ points }}
</header>

<div class="container">

<div class="card">
<h3>Add Strike</h3>
<form method="post" action="/strike">
<select name="rule">
{% for r in rules %}
<option value="{{r}}">{{r}}</option>
{% endfor %}
</select>
<button type="submit">Add Strike</button>
</form>
</div>

<div class="card">
<h3>End Day</h3>
<form method="post" action="/end_day">
<button type="submit">End Day</button>
</form>
</div>

<div class="card">
<h3>Exchange</h3>
<form method="post" action="/exchange">
<select name="reward">
<option value="toy">Toy (5 points)</option>
<option value="hockey_game">Hockey Game (10 points)</option>
</select>
<button type="submit">Exchange</button>
</form>
</div>

<div class="card">
<h3>Tutorial</h3>
<button onclick="showTutorial()">View Tutorial</button>
</div>

<div class="card">
<h3>System Menu</h3>
<button onclick="showSystem()">Enter PIN</button>
</div>

</div>

{% if audio %}
<audio controls autoplay>
<source src="{{ audio }}" type="audio/mpeg">
</audio>
{% endif %}

<div id="tutorialModal" class="modal">
<div class="modal-content">
<h2>Tutorial</h2>
<p>Welcome to the Kids Rewards System!<br>
1. Add Strike: Select a rule and click 'Add Strike'.<br>
2. End Day: Ends the day and calculates points.<br>
3. Exchange: Redeem points for rewards.<br>
4. Tutorial: Shows these instructions.<br>
All actions are logged automatically.</p>
<button onclick="closeTutorial()">Close</button>
</div>
</div>

<div id="systemModal" class="modal">
<div class="modal-content">
<h2>System Menu</h2>
<form method="post" action="/system_access">
<input type="password" name="pin" placeholder="Enter PIN" required>
<button type="submit">Enter</button>
</form>
<div id="systemContent" style="display:none;">
<h3>Logs</h3>
<pre>{{ logs }}</pre>
<h3>Adjust Points</h3>
<form method="post" action="/manual_point">
<input type="number" name="points_change" placeholder="Add/Subtract points" required>
<button type="submit">Apply</button>
</form>
<form method="post" action="/reset_system">
<button type="submit">Reset System</button>
</form>
<button onclick="closeSystem()">Close</button>
</div>
</div>
</div>

<script>
function showTutorial(){document.getElementById('tutorialModal').style.display='flex';}
function closeTutorial(){document.getElementById('tutorialModal').style.display='none';}

function showSystem(){document.getElementById('systemModal').style.display='flex';}
function closeSystem(){document.getElementById('systemModal').style.display='none';document.getElementById('systemContent').style.display='none';}
</script>
</body>
</html>
"""

@app.route("/audio/<filename>")
def serve_audio(filename):
    return send_from_directory(AUDIO_DIR, filename)

@app.route("/", methods=["GET"])
def index():
    day = current_day()
    strikes = len(day["strikes"])
    points = data["points"]
    return render_template_string(HTML, day=day, strikes=strikes, points=points, rules=RULES, logs="", audio=None)

@app.route("/strike", methods=["POST"])
def add_strike():
    day = current_day()
    rule = request.form["rule"]
    day["strikes"].append(rule)
    save_data()
    log(f"Strike added: {rule}")
    audio_file = url_for("serve_audio", filename=f"rule{RULES.index(rule)+1}.mp3")
    return render_template_string(HTML, day=day, strikes=len(day["strikes"]), points=data["points"], rules=RULES, logs="", audio=audio_file)

@app.route("/end_day", methods=["POST"])
def end_day():
    day = current_day()
    strikes = len(day["strikes"])
    if strikes < 3:
        data["points"] += 1
        log(f"Day {day['id']} ended — +1 point")
    else:
        log(f"Day {day['id']} ended — no point (too many strikes)")
    # start new day
    new_id = day["id"] + 1
    data["days"].append({"id": new_id, "strikes":[]})
    save_data()
    return render_template_string(HTML, day=current_day(), strikes=0, points=data["points"], rules=RULES, logs="", audio=None)

@app.route("/exchange", methods=["POST"])
def exchange():
    reward = request.form["reward"]
    if reward=="toy" and data["points"]>=5:
        data["points"]-=5
        log("Exchanged 5 points for a toy")
    elif reward=="hockey_game" and data["points"]>=10:
        data["points"]-=10
        log("Exchanged 10 points for a hockey game")
    else:
        log(f"Exchange failed: not enough points for {reward}")
    save_data()
    return render_template_string(HTML, day=current_day(), strikes=len(current_day()["strikes"]), points=data["points"], rules=RULES, logs="", audio=None)

@app.route("/system_access", methods=["POST"])
def system_access():
    pin = request.form["pin"]
    if pin == SYSTEM_PIN:
        with open(LOG_FILE) as f:
            logs = f.read()
        return render_template_string(HTML, day=current_day(), strikes=len(current_day()["strikes"]), points=data["points"], rules=RULES, logs=logs, audio=None, system_content=True)
    else:
        log("Incorrect PIN attempt")
        return redirect("/")

@app.route("/manual_point", methods=["POST"])
def manual_point():
    change = int(request.form["points_change"])
    data["points"] += change
    save_data()
    log(f"Manual {'+' if change>=0 else ''}{change} points (System Menu)")
    return redirect("/")

@app.route("/reset_system", methods=["POST"])
def reset_system():
    global data
    data = {"points":0,"days":[]}
    save_data()
    log("System reset to default state")
    return redirect("/")

if __name__=="__main__":
    os.makedirs(AUDIO_DIR, exist_ok=True)
    app.run(host="0.0.0.0", port=8080)

from flask import Flask, render_template, request
from layer_2_validation.py import main
import webbrowser
from os import getpid, kill
from signal import SIGINT
from time import sleep

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    
    if request.method == "POST":

        print(request.form)

        device_input = request.form.get("device_input", "").strip()
        username = request.form.get("username", "").strip()
        ssh_pass1 = request.form.get("ssh_pass1", "")
        ssh_pass2 = request.form.get("ssh_pass2", "")

        if not device_input:
            return "Error: You must enter the device list or file path."

        lb_even, lb_odd, fw_even, fw_odd = main(
            key1=ssh_pass1,
            key2=ssh_pass2,
            user=username,
            device_input=device_input,
        )

        return render_template("results.html",
                               lb_results = lb_even + lb_odd,
                               fw_results = fw_even + fw_odd)

    return render_template("index.html")

@app.route('/shutdown', methods=['POST'])
def shutdown():
    def delayed_shutdown():
        import time
        sleep(1)
        kill(getpid(), SIGINT)

    import threading
    threading.Thread(target=delayed_shutdown).start()
    return 'Shutting down...'

if __name__ == "__main__":
    # Launch Chrome at localhost
    webbrowser.get(using='windows-default').open_new("http://127.0.0.1:5000")
    app.run(debug=True, use_reloader=False)

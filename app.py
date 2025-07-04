from flask import Flask, render_template, request
# import your cable1 function as needed
from cableTest_v2 import cable1
import webbrowser
from time import sleep

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    
    if request.method == "POST":
        # Print all form data for debugging
        print(request.form)

        device_input = request.form.get("device_input", "").strip()
        port_config = request.form.get("port_config", "").strip()
        username = request.form.get("username", "").strip()
        ssh_pass1 = request.form.get("ssh_pass1", "")
        ssh_pass2 = request.form.get("ssh_pass2", "")

        if not device_input:
            return "Error: You must enter the device list or file path."

        # Determine ports
        if port_config == "standard":
            lb_port, rtr_lb_port, rtr_fw_port = "XX", "1/XX-XX", "1/XX-XX"
        else:
            lb_port = request.form.get("lb_port", "").strip()
            rtr_lb_port = request.form.get("rtr_lb_port", "").strip()
            rtr_fw_port = request.form.get("rtr_fw_port", "").strip()

        # Call your function (you may need to refactor cable1 to accept these args)
        lb1, fw1, lb2, fw2 = cable1(
            key1=ssh_pass1,
            key2=ssh_pass2,
            user=username,
            device_input=device_input,
            lb_port=lb_port,
            rtr_lb_port=rtr_lb_port,
            rtr_fw_port=rtr_fw_port
        )

        return render_template("results.html",
                               lb_results=lb1 + lb2,
                               fw_results=fw1 + fw2)

    return render_template("index.html")


if __name__ == "__main__":
    # Launch Chrome at localhost
    webbrowser.get(using='windows-default').open_new("http://127.0.0.1:5000")
    app.run(debug=True)


""" Details

Script name:
        cable_5.py

Description: 
        Designed to aid the Network Engineer with preliminary cable validation of Layer 2 connections

Usage:  
        Execute files/app_new.py which launches a Web GUI
        Enter devices associated with a single pod; please DO NOT enter a router
        Enter the username and passwords as indicated
        Run Validation
        Observe the backend

Author:
        Deon R. Murray | CCNA | Security+ | Purdue University

Date:
        7/17/2025

Notes:
        Tested on the following models:
            > Redacted
            > Redacted
            > Redacted

        All other supporting scripts (app.py, index.html, results.html) were generated by ChatGPT and modified by the Author.
"""

from time import sleep
from os import path
from paramiko import SSHClient, AutoAddPolicy
from socket import gaierror
from re import findall, search
from getpass import getpass

# Terminal color codes
RED = "\033[31m"
GRN = "\033[32m"
YEL = "\033[33m"
MAG = "\033[35m"
CYN = "\033[36m"
RST = "\033[0m"

# used for results.html output formatting
html_dev = '<span class="device">'
html_int = '<span class="interface">'
html_conn_dev = '<span class="connected-device">'
html_span_end = '</span>'

# a class for storing various port numbers, and interface states across functions
class cable:
    def __init__(self):
        self.lb_state = None
        self.fw_state1 = None
        self.fw_state2 = None
        self.rtr_state = None
        self.lb_port = None
        self.fw_port = None
        self.rtr_port = None

    def store_lb_state(self, updown):
        self.lb_state = updown
    def store_fw_state1(self, updown):
        self.fw_state1 = updown
    def store_fw_state2(self, updown):
        self.fw_state2 = updown
    def store_rtr_state(self, conn_stat):
        self.rtr_state = conn_stat
        
    def store_lb_port(self, port):
        self.lb_port = port
    def store_fw_port(self, port):
        self.fw_port = port
    def store_rtr_port(self, port):
        self.rtr_port = port

    def get_lb_state(self):
        return self.lb_state
    def get_fw_state1(self):
        return self.fw_state1
    def get_fw_state2(self):
        return self.fw_state2
    def get_rtr_state(self):
        return self.rtr_state
    def get_lb_port(self):
        return self.lb_port
    def get_fw_port(self):
        return self.fw_port
    def get_rtr_port(self):
        return self.rtr_port

# a class for storing various devices according to even or odd ending numbers [ devices associated with the same router ]
class devdev:
    def __init__(self):
        self.even_rtr = None
        self.odd_rtr = None
        self.even_fw_list = None
        self.odd_fw_list = None
        self.even_lb_list = None
        self.odd_lb_list = None

    def set_even_rtr(self, rtrs):
        self.even_rtr = rtrs
    def set_odd_rtr(self, rtrs):
        self.odd_rtr = rtrs
    def set_even_fw_list(self, fws):
        self.even_fw_list = fws
    def set_odd_fw_list(self, fws):
        self.odd_fw_list = fws
    def set_even_lb_list(self, lbs):
        self.even_lb_list = lbs
    def set_odd_lb_list(self, lbs):
        self.odd_lb_list = lbs

    def get_even_rtr(self):
        return self.even_rtr
    def get_odd_rtr(self):
        return self.odd_rtr
    def get_even_fw_list(self):
        return self.even_fw_list
    def get_odd_fw_list(self):
        return self.odd_fw_list
    def get_even_lb_list(self):
        return self.even_lb_list
    def get_odd_lb_list(self):
        return self.odd_lb_list

# open ssh connections, returns cli channel and invoked shell
def open_conn(device, user, pass1):
    cli = SSHClient()
    cli.set_missing_host_key_policy(AutoAddPolicy())
    try:
        cli.connect(f"{device}.XXXX", username=user, password=pass1)
        shell = cli.invoke_shell()
        sleep(1)
        shell.recv(1000)
        sleep(1)
    except gaierror as e:
        print(f"\n{CYN}Invalid Host: {RST}{device}. Resolution failed: {e}")
        return f"[ERR] {device}: {e}"
    except Exception as e:
        print(f"\n{CYN}General connection failure:{RST} {e}")
        return f"[ERR] {device}: {e}"
    return cli, shell

# modularized the command function with an argument for receiving output or not
def command(shell, command, output=False):
    shell.send(f"{command}\n")
    sleep(0.5)
    if output == True:
        out = shell.recv(2048).decode()
        return out
    else:
        return "Output flag not set!"
        
# converts input into list
def path_or_manual_input(device_input):
    try:
        if path.exists(device_input):
            with open(device_input, "r") as f:
                fileArr = [line.strip() for line in f if line.strip()]
        else:
            fileArr = device_input.split()
    except Exception as e:
        print(f"Error parsing device input: {e}")
        fileArr = []
    return fileArr

# checks the router for interface status before flip functions are called
def routerCheck(dev, username, password, shell1=""):
    # checks if an existing shell is passed back in
    if not shell1:
        cli, shell = open_conn(device=dev, user=username, pass1=password)
        out1 = command(shell, "show interface status | include notconnected", output=True) 
        return out1, shell, cli
    else:
        out1 = command(shell1, "show interface status | include notconnected", output=True) 
        return out1

# sorts devices into even and odd groupings
def devsort(dev_instObj, app_input):
    raw_devs = path_or_manual_input(app_input)
    print(raw_devs)
    even_LBs = []
    odd_LBs = []
    even_FWs = []
    odd_FWs = []
    # match/sort logic
    for i in raw_devs:
        if findall(r"^LB.*(00|02|04)$", i):
            even_LBs.append(i)
        elif findall(r"^LB.*(01|03|05)$", i):
            odd_LBs.append(i)
        elif findall(r"FW.*(00|02)$", i):
            even_FWs.append(i)
        elif findall(r"FW.*(01|03)$", i):
            odd_FWs.append(i)
        else:
            print("No input provided!")
    dev_instObj.set_even_fw_list(even_FWs)
    dev_instObj.set_odd_fw_list(odd_FWs)
    dev_instObj.set_even_lb_list(even_LBs)
    dev_instObj.set_odd_lb_list(odd_LBs)


# get the router(s) using an LB inputed
def get_rtrs_from_lb(key, user, cableObj, devObj):
    even_check = False
    odd_check = False
    
    if devObj.get_even_lb_list():
        cli, shell = open_conn(devObj.get_even_lb_list()[0], user, key) # first device in even lb list
        out = command(shell, "show interfaces brief | include Up", output=True)

        for i in out.splitlines():
            if findall(r"B\d{2}.*(00)",i): # finds the line of output containing the LB router connection
                cableObj.store_lb_port(i.split()[0]) # assumes all LBs in a POD uses the same port
                for k in i.split():
                    # find the router
                    if findall(r"B\d{2}.*(00)", k):
                        devObj.set_even_rtr(search(r"B\d{2}.*(00)", k).group()) # stores the even router
        even_check = True  
        cli.close()
    else:
        print("Even LB list empty.")
        
    if devObj.get_odd_lb_list():
        cli, shell = open_conn(devObj.get_odd_lb_list()[0], user, key) # first device in even lb list
        out = command(shell, "show interfaces brief | include Up", output=True)

        for i in out.splitlines():
            if findall(r"B\d{2}.*(01)",i): # finds the line of output containing the LB router connection
                cableObj.store_lb_port(i.split()[0]) # assumes all LBs in a POD uses the same port # may need to work around setting this twice
                for k in i.split():
                    # find the router
                    if findall(r"B\d{2}.*(01)", k):
                        devObj.set_odd_rtr(search(r"B\d{2}.*(01)", k).group()) # stores the odd router
        cli.close()
        odd_check = True
    else:
        print("Odd LB list empty.")
    return even_check, odd_check


# get the router(s) using an FW inputed if no LBs provided || Makes some assumtions about the FW
def get_rtrs_from_fw(key, user, devObj, even_check, odd_check):

    if devObj.get_even_fw_list() and even_check == False: # does not get the router from FW if already obtained from the LB
        cli, shell = open_conn(devObj.get_even_fw_list()[0], user, key) # first device in even lb list
        command(shell, "redacted")
        cmd_out = command(shell, "show interface eth1-01 comments", output=True)

        devObj.set_even_rtr("".join(findall(r"comments (B\d{2}.{3}00)", cmd_out))) # stores the even router
        cli.close()
    else:
        print("Even FW list empty.")
        
    if devObj.get_odd_fw_list() and odd_check == False: # does not get the router from FW if already obtained from the LB
        cli, shell = open_conn(devObj.get_odd_fw_list()[0], user, key) # first device in even lb list
        command(shell, "redacted")
        cmd_out = command(shell, "show interface eth1-01 comments", output=True)

        devObj.set_odd_rtr("".join(findall(r"comments (B\d{2}.{3}00)", cmd_out)).replace("00","01")) # stores the odd router <> replaces the even suuffix with 01 | crude fix

        cli.close()
    else:
        print("Odd FW list empty.")


# flip_lb_int turns the interface down if it's up and up if it's down for the LBs
def flip_lb_int(shell, eth_int):
    cmd_output = command(shell, f"show interface ethernet {eth_int}", output=True)
    state = "".join(findall(r"protocol is (up|down)", cmd_output))

    if state == "up":
        command(shell, "config t")
        command(shell, f"interface ethernet {eth_int}")
        command(shell, "disable")

        sleep(3) # allowing time to come up [ FEEL FREE TO EXPLORE SHORTER TIMES || FINAL STATE output displayed will vary]
        cmd_output = command(shell, f"show interface ethernet {eth_int}", output=True)
        state = "".join(findall(r"protocol is (up|down)", cmd_output))

    elif state == "down":
        command(shell, "config t")
        command(shell, f"interface ethernet {eth_int}")
        command(shell, "enable")

        cmd_output = command(shell, f"show interface ethernet {eth_int}", output=True)
        state = "".join(findall(r"protocol is (up|down)", cmd_output))
    else:
        print(f"Unable to change interface — {YEL}Please manually verify state{RST}")
        state = "No output received"
    return state
# flip_lb_int turns the interface down if it's up and up if it's down for the FWs
def flip_fw_int(shell, num):
    cmd_output = command(shell, f"show interface eth{num}", output=True)
    state1 = "".join(findall(r"state (on|off)\r\nredacted", cmd_output))
    state2 = "".join(findall(r"link-state link (up|down)", cmd_output))
    
    if state1 == "on" and state2 == "up":
        command(shell, "redacted")
        command(shell, "redacted")
        command(shell, f"set interface eth{num} state off")

        cmd_output = command(shell, f"show interface eth{num}", output=True)
        state1 = "".join(findall(r"state (on|off)\r\nredacted", cmd_output))
        state2 = "".join(findall(r"link-state link (up|down)", cmd_output))

    elif state1 == "off" and state2 == "down":
        command(shell, "redacted")
        command(shell, "redacted")
        command(shell, f"set interface eth{num} state on")
        sleep(5) # allowing time to come up [ FEEL FREE TO EXPLORE SHORTER TIMES || FINAL STATE output displayed will vary]
        cmd_output = command(shell, f"show interface eth{num}", output=True)
        state1 = "".join(findall(r"state (on|off)\r\nredacted", cmd_output))
        state2 = "".join(findall(r"link-state link (up|down)", cmd_output))

    else:
        print(f"Unable to change interface — {YEL}Please manually verify FW state{RST}")
        state1 = "No output received1"
        state2 = "No output received2"
    return state1, state2

# calls routerCheck and flip functions; compares router outputs to identify interface; extracts port number
def even_rtr_check_lbs(user, key1, key2, devices, cable1):
    lb_even_list = []
    diffs = ""

    for dev in devices.get_even_lb_list():
        cli, shell = open_conn(dev, user, key1) # opens connection to sample odd/even LBs or [not prepared script FWs]
        # gets baseline result of rtr "not connected" interfaces
        router_result1, rtr_shell, rtr_cli = routerCheck(dev=devices.get_even_rtr(), username=user, password=key2)
        flip_lb_int(shell, cable1.get_lb_port()) # intended to flip down
         # passes the opened shell from the first rtrCheck call
        router_result2 = routerCheck(dev=devices.get_even_rtr(), username=user, password=key2, shell1=rtr_shell)
        state = flip_lb_int(shell, cable1.get_lb_port()) # intended to flip up
        print(f"*** {YEL}{dev}{RST} Eth{GRN}{cable1.get_lb_port()}{RST} Final state: {RED}{state}{RST}")
        # store difference between lists of the two outputs from routerCheck calls
        diffs = "".join(set(router_result2.splitlines()) - set(router_result1.splitlines()))
        cable1.store_rtr_port("".join(findall(r"Eth1/(\d{2}).*notconnected.*", diffs))) ### stores router port

        lb_even_result = f">> {devices.get_even_rtr()} Eth {cable1.get_rtr_port()} is connected to {dev} at Eth {cable1.get_lb_port()}"
        lb_even_html_result = f">> {html_dev}{devices.get_even_rtr()}{html_span_end} Eth {html_int}{cable1.get_rtr_port()}{html_span_end} is connected to {html_conn_dev}{dev}{html_span_end} at Eth {html_int}{cable1.get_lb_port()}{html_span_end}"
        lb_even_list.append(lb_even_html_result)
        print(lb_even_result)
        # close connection
        cli.close()
    return rtr_cli, lb_even_list

# calls routerCheck and flip functions; compares router outputs to identify interface; extracts port number
def odd_rtr_check_lbs(user, key1, key2, devices, cable1):
    lb_odd_list = []
    diffs = ""

    for dev in devices.get_odd_lb_list():
        cli, shell = open_conn(dev, user, key1) # opens connection to sample odd/even LBs or [not prepared script FWs]
        # gets baseline result of rtr "not connected" interfaces
        router_result1, rtr_shell, rtr_cli = routerCheck(dev=devices.get_odd_rtr(), username=user, password=key2)
        flip_lb_int(shell, cable1.get_lb_port()) # intended to flip down
         # passes the opened shell from the first rtrCheck call
        router_result2 = routerCheck(dev=devices.get_odd_rtr(), username=user, password=key2, shell1=rtr_shell)
        state = flip_lb_int(shell, cable1.get_lb_port()) # intended to flip up
        print(f"*** {YEL}{dev}{RST} Eth{GRN}{cable1.get_lb_port()}{RST} Final state: {RED}{state}{RST}")
        # store difference between lists of the two outputs from routerCheck calls
        diffs = "".join(set(router_result2.splitlines()) - set(router_result1.splitlines()))
        cable1.store_rtr_port("".join(findall(r"Eth1/(\d{2}).*notconnected.*", diffs))) ### stores router port


        lb_odd_result = f">> {devices.get_odd_rtr()} Eth {cable1.get_rtr_port()} is connected to {dev} at Eth {cable1.get_lb_port()}"
        lb_even_html_result = f">> {html_dev}{devices.get_odd_rtr()}{html_span_end} Eth {html_int}{cable1.get_rtr_port()}{html_span_end} is connected to {html_conn_dev}{dev}{html_span_end} at Eth {html_int}{cable1.get_lb_port()}{html_span_end}"
        lb_odd_list.append(lb_even_html_result)
        print(lb_odd_result)
        # close connection
        cli.close()
    return rtr_cli, lb_odd_list

# calls routerCheck and flip functions; compares router outputs to identify interface; extracts port number
def even_rtr_check_fws(user, key1, key2, devices, cable1):
    fw_even_list = []
    diffs = ""

    for dev in devices.get_even_fw_list():
        x = 1 # used for incrementing FW ports. Assumes only Eth 1-01 and Eth1-02 exist 
        for i in range(2):
            fw_port = f"1-0{x}"
            cli, shell = open_conn(dev, user, key1) # opens connection to sample odd/even LBs or [not prepared script FWs]
            command(shell, "redacted")
            # gets baseline result of rtr "not connected" interfaces
            router_result1, rtr_shell, rtr_cli = routerCheck(dev=devices.get_even_rtr(), username=user, password=key2)
            flip_fw_int(shell, num=f"{fw_port}") # intended to flip down

            # passes the opened shell from the first rtrCheck call
            router_result2 = routerCheck(dev=devices.get_even_rtr(), username=user, password=key2, shell1=rtr_shell)
            final_state1, final_state2 = flip_fw_int(shell, num=f"{fw_port}") # intended to flip up
            print(f"*** {YEL}{dev}{RST} Eth{GRN}1-0{x}{RST} Final state: {RED}{final_state1}{RST} and {RED}{final_state2}{RST}")
            # store difference between lists of the two outputs from routerCheck calls
            diffs = "".join(set(router_result2.splitlines()) - set(router_result1.splitlines()))
            cable1.store_rtr_port("".join(findall(r"Eth1/(\d{2}).*notconnected.*", diffs))) ### stores router port

            fw_even_result = f">> {devices.get_even_rtr()} Eth {cable1.get_rtr_port()} is connected to {dev} at Eth {fw_port}"
            fw_even_html_result = f">> {html_dev}{devices.get_even_rtr()}{html_span_end} Eth {html_int}{cable1.get_rtr_port()}{html_span_end} is connected to {html_conn_dev}{dev}{html_span_end} at Eth {html_int}{fw_port}{html_span_end}"
            fw_even_list.append(fw_even_html_result)
            print(fw_even_result)
            x += 1
    # close connection
    cli.close()
    return rtr_cli, fw_even_list

# calls routerCheck and flip functions; compares router outputs to identify interface; extracts port number
def odd_rtr_check_fws(user, key1, key2, devices, cable1):
    fw_odd_list = []
    diffs = ""
    
    for dev in devices.get_odd_fw_list():
        x = 1 # used for incrementing FW ports. Assumes only Eth 1-01 and Eth1-02 exist 
        for i in range(2):
            fw_port = f"1-0{x}"
            cli, shell = open_conn(dev, user, key1) # opens connection to sample odd/even LBs or [not prepared script FWs]
            command(shell, "redacted")
            # gets baseline result of rtr "not connected" interfaces
            router_result1, rtr_shell, rtr_cli = routerCheck(dev=devices.get_odd_rtr(), username=user, password=key2)
            flip_fw_int(shell, num=f"{fw_port}") # intended to flip down

            # passes the opened shell from the first rtrCheck call
            router_result2 = routerCheck(dev=devices.get_odd_rtr(), username=user, password=key2, shell1=rtr_shell)
            final_state1, final_state2 = flip_fw_int(shell, num=f"{fw_port}") # intended to flip up
            print(f"*** {YEL}{dev}{RST} Eth{GRN}1-0{x}{RST} Final state: {RED}{final_state1}{RST} and {RED}{final_state2}{RST}")
            # store difference between lists of the two outputs from routerCheck calls
            diffs = "".join(set(router_result2.splitlines()) - set(router_result1.splitlines()))
            cable1.store_rtr_port("".join(findall(r"Eth1/(\d{2}).*notconnected.*", diffs))) ### stores router port

            fw_odd_result = f">> {devices.get_odd_rtr()} Eth {cable1.get_rtr_port()} is connected to {dev} at Eth {fw_port}"
            fw_odd_html_result = f">> {html_dev}{devices.get_odd_rtr()}{html_span_end} Eth {html_int}{cable1.get_rtr_port()}{html_span_end} is connected to {html_conn_dev}{dev}{html_span_end} at Eth {html_int}{fw_port}{html_span_end}"
            fw_odd_list.append(fw_odd_html_result)
            print(fw_odd_result)
            x += 1
    # close connection
    cli.close()
    return rtr_cli, fw_odd_list



# main function
def main(key1, key2, user, device_input):
    devices = devdev()
    devsort(devices, app_input=device_input) # sorting into odd and even list atrributes
    cableObj0 = cable()
     # passes the devices Obj into dev sort for sorting
    even_check1, odd_check1 = get_rtrs_from_lb(key1, user, cableObj0, devices) # even and odd router store in cable1.get_even/odd_rtr
    # passing these Booleans into this function to check if an even and/or router was stored from the get_rtrs_from_lb()
    get_rtrs_from_fw(key1, user, devices, even_check1, odd_check1)
    


    if devices.get_even_lb_list():
        rtr_cli, lb_even = even_rtr_check_lbs(user, key1, key2, devices, cableObj0)
        rtr_cli.close()
    else:
        lb_even = []
    if devices.get_odd_lb_list():
        rtr_cli, lb_odd = odd_rtr_check_lbs(user, key1, key2, devices, cableObj0)
        rtr_cli.close()
    else:
        lb_odd = []
    if devices.get_even_fw_list():
        rtr_cli, fw_even = even_rtr_check_fws(user, key1, key2, devices, cableObj0)
        rtr_cli.close()
    else:
        fw_even = []
    if devices.get_odd_fw_list():
        rtr_cli, fw_odd = odd_rtr_check_fws(user, key1, key2, devices, cableObj0)
        rtr_cli.close()
    else:
        fw_odd = []

    return lb_even, lb_odd, fw_even, fw_odd # passes to app_new.py (GPT generated script; Author edited)

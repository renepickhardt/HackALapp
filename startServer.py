'''
Created on 20.08.2018

@author: rpickhardt

derived from: https://daanlenaerts.com/blog/2015/06/03/create-a-simple-http-server-with-python-3/

'''
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import hashlib
from lightning.lightning import LightningRpc
import time
import json

class HackALappHTTPServer_RequestHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        f = open("topics.txt")
        message = """<form method="post"><fieldset><legend>Which Videos would you like to have on my 
        <a href="https://www.youtube.com/channel/UCWmagvXbbOAS29CcLRP0FWg">Youtube Channel</a> and on
         <a href="https://en.wikiversity.org/wiki/Lightning_Network">Wikiversity</a>?</legend>"""
        # shuffle lines
        for line in f:
            hash_id = hashlib.sha256(line.encode()).hexdigest()
            message += """<div> <input type="checkbox" id=\"""" + hash_id + """\" name="votes"
               value=\"""" + hash_id + """\" /> <label for=\"""" + hash_id + """\"">""" + line + "</label></div>"
        message += """</fieldset><div><button type="submit">Vote now!</button></div></form>"""
        self.wfile.write(bytes(message, "utf8"))
        return
    
    def do_POST(self):
        self.send_response(200)
        
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        length = int(self.headers.get('content-length'))
        field_data = self.rfile.read(length)
        fields = parse_qs(field_data)
        votes = [s.decode('ascii') for s in fields[b"votes"]]
        
        message = "received your " + str(len(votes)) + "votes! You have voted for the following questions: </p>"
        message += "<ul>"
        f = open("topics.txt")
        for line in f:
            hash_id = hashlib.sha256(line.encode()).hexdigest()
            if hash_id in votes:
                message += "<li>" + line + "</li>"
        message += "</ul>"
        
        amount = 250 * len(votes) * 1000
        
        l = LightningRpc("/path/to/your/.lightning/lightning-rpc")
        now = time.time()
        invoice = l.invoice(amount,"lbl{}".format(now),"rene-pickhardts-lightning-video-votes-{}".format(now))
        
        message += "Each vote costs 250 Satoshi pleas pay: " + str(amount/1000) + " via the following invoice: <br>"
        
        message += invoice["bolt11"]
        
        dict = {"v":votes, "i":invoice}
        with open("potentialVotes/"+invoice["payment_hash"]+".json","w") as outfile:
            json.dump(dict,outfile)
        
        self.wfile.write(bytes(message, "utf8"))
        return
 
def run():
    server_address = ('127.0.0.1', 8080)
    httpd = HTTPServer(server_address, HackALappHTTPServer_RequestHandler)
    print('Server online. Waiting for requests')
    httpd.serve_forever()
run()

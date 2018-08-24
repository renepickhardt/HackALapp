'''
Created on 20.08.2018

@author: rpickhardt

derived from: https://daanlenaerts.com/blog/2015/06/03/create-a-simple-http-server-with-python-3/

#FIXME add dependancies to setup.py
pip3.6 install qrcode[pil]
pip3.6 install pylightning

'''
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs
import hashlib
from lightning.lightning import LightningRpc
import time
import json


import qrcode
import base64
from io import BytesIO

class HackALappHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    global rpc_interface
    global topic_dict
    
    rpc_interface = LightningRpc("/Users/rpickhardt/.lightning/lightning-rpc") 
    
    f = open("topics.txt")
    topic_dict= {}
    for line in f:
        hash_id = hashlib.sha256(line.encode()).hexdigest()
        topic_dict[hash_id] = line[:-1]
    
    def __footer(self):
        return """<p>Want to learn more about this LAPP?  
        Check out <a href="https://youtu.be/HXVDwRnU7_I">my youtube video about Hack A Lapp</a> <br><br>
        You can also fund a payment channel with my <a href="https://youtu.be/HXVDwRnU7_I">lightning node</a> or 
         or <a href="https://twitter.com/renepickhardt">follow me on twitter</a>
                 or visit my <a href="https://www.rene-pickhardt.de">my personal Website</a></p>"""
        
    def __make_base64_qr_code(self,bolt11):
        qr = qrcode.QRCode(
            version = 1,
            error_correction = qrcode.constants.ERROR_CORRECT_H,
            box_size = 4,
            border = 4,
        )
        
        qr.add_data(bolt11)
        qr.make(fit=True)
        img = qr.make_image()
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")        
        return img_str
    
    def __add__invoice_payment_string(self,invoice):
        #FIXME: check for expired incoices and generate a new

        message ="""<h2>Look up <a href="/"""+invoice["payment_hash"]+"""\">the results </a> (only possible after you paid the invoice)</h2>"""
        
        message += "<p>Each vote costs 250 Satoshi. Please pay " + str(int(invoice["msatoshi"])/1000) + " via the following invoice: </p>"
                        
        message += invoice["bolt11"]
        message +="<br><br><img src=\"data:image/png;base64," + self.__make_base64_qr_code(invoice["bolt11"]) + "\">"

        return message
    
    def __count_votes(self):
        invoices = rpc_interface.listinvoices()["invoices"]        
        count_votes = {}
        
        for invoice in invoices: 
            status = invoice["status"]
            payment_hash = invoice["payment_hash"]
            #if status != "paid":
            #    continue
            try: 
                with open("potentialVotes/"+payment_hash+".json","r") as outfile:
                    voting_dict = json.load(outfile)
                    votes = voting_dict["v"]
                    for vote in votes:
                        if vote in count_votes:
                            count_votes[vote]+=1
                        else:
                            count_votes[vote] = 1
            except:
                pass
        return count_votes
    
    def __show_start_page(self):
        message = """<form method="post"><fieldset><legend>Which Videos would you like to have on my 
        <a href="https://www.youtube.com/channel/UCWmagvXbbOAS29CcLRP0FWg">Youtube Channel</a> and on
         <a href="https://en.wikiversity.org/wiki/Lightning_Network">Wikiversity</a>?</legend>"""
        # shuffle lines
        for hash_id, topic in topic_dict.items():
            message += """<div> <input type="checkbox" id=\"""" + hash_id + """\" name="votes"
               value=\"""" + hash_id + """\" /> <label for=\"""" + hash_id + """\"">""" + topic + "</label></div>"
        message += """</fieldset><div><button type="submit">Vote now!</button></div></form>"""
        return message
    
    def __show_rankings_page(self,payment_hash):
        message = ""
        num_votes = 0
        try:
            f = open("potentialVotes/"+payment_hash+".json", "r")
            data = json.load(f)
            votes = data["v"]
            message += "<h1>You have voted for:</h1>"
            for vote in votes: 
                message = message + topic_dict[vote] + "<br>"
        except:
            message = "Payment hash unknown. Please go to the <a href='/'>home page and vote for future videos</a>"
            pass
            
        invoices = rpc_interface.listinvoices()["invoices"]
        for invoice in invoices: 
            if invoice["payment_hash"] == payment_hash: #self.path[1:]:
                if invoice["status"]=="paid":
                    message +="<h2>The current rankings of the poll are: </h2>"
                    message+="great you paid your fair share! The ranking will be impolemented soon"
                    message+="<ul>"
                    for key, count in self.__count_votes().items():
                        message+="<li>"+str(count)+": "+topic_dict[key]+"</li>"
                    message+="</ul>"

                else:
                    message += self.__add__invoice_payment_string(invoice)
        
        return message

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        message = ""
        if self.path == "/":
            message = self.__show_start_page()
        else:
            if self.path != "/favicon.ico":
                message = self.__show_rankings_page(self.path[1:])
        
        message += self.__footer()
           
        self.wfile.write(bytes(message, "utf8"))
        return
    
    def do_POST(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        length = int(self.headers.get('content-length'))
        field_data = self.rfile.read(length)
        fields = parse_qs(field_data)
        
        message =""
        if b"votes" not in fields:
            message = "malformed post request"
        else: 
            votes = [s.decode('ascii') for s in fields[b"votes"]]            
            amount = 250 * len(votes) * 1000
            now = time.time()
            
            invoice = rpc_interface.invoice(amount,"lbl{}".format(now),"rene-pickhardts-lightning-video-votes-{}".format(now))

            data_dict = {"v":votes, "i":invoice}
            with open("potentialVotes/"+invoice["payment_hash"]+".json","w") as outfile:
                json.dump(data_dict,outfile)

            message += self.__show_rankings_page(invoice["payment_hash"])
        message += self.__footer()
        
        self.wfile.write(bytes(message, "utf8"))
        return
 
def run():
    server_address = ('127.0.0.1', 8080)
    httpd = HTTPServer(server_address, HackALappHTTPServer_RequestHandler)
    print('Server online. Waiting for requests')
    httpd.serve_forever()
run()

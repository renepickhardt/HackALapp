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

#FIXME: move this to the __init__  call and remove global statements
rpc_interface = None

class HackALappHTTPServer_RequestHandler(BaseHTTPRequestHandler):
    def __count_votes(self):
        global rpc_interface
        if rpc_interface == None:
            rpc_interface = LightningRpc("/Users/rpickhardt/.lightning/lightning-rpc") 

        invoices = rpc_interface.listinvoices()["invoices"]
        
        #FIXME: move this to a class property and away from this function
        f = open("topics.txt")
        topic_dict= {}
        for line in f:
            hash_id = hashlib.sha256(line.encode()).hexdigest()
            topic_dict[hash_id] = line[:-1]
        
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
        return message
    
    def __show_rankings_page(self):
        global rpc_interface
        if self.path == "/favicon.ico":
            return ""
        
        f = open("topics.txt")
        topic_dict= {}
        for line in f:
            hash_id = hashlib.sha256(line.encode()).hexdigest()
            topic_dict[hash_id] = line[:-1]
        message = ""
        #pay attention the self.path variable might have to be escaped
        try:
            f = open("potentialVotes"+self.path+".json", "r")
            data = json.load(f)
            votes = data["v"]
            message += "<h1>You have voted for:</h1>"
            for vote in votes: 
                message = message + topic_dict[vote] + "<br>"
        except:
            message = "Payment hash unknown. Please go to the <a href='/'>home page and vote for future videos</a>"
            pass
            
        invoices = rpc_interface.listinvoices()["invoices"]
        message +="<h2>The current rankings of the poll are: </h2>"
        for invoice in invoices: 
            if invoice["payment_hash"] == self.path[1:]:
                if invoice["status"]=="paid":
                    message+="great you paid your fair share! The ranking will be impolemented soon"
                    message+="<ul>"
                    for key, count in self.__count_votes().items():
                        message+="<li>"+str(count)+": "+topic_dict[key]+"</li>"
                    message+="</ul>"

                else:
                    #FIXME: check for expired incoices and generate a new
                    message+="Please pay your invoice first! The invoice is: <br><br>"
                    message+=invoice["bolt11"]
        
        return message

    def do_GET(self):
        global rpc_interface
        if rpc_interface == None:
            rpc_interface = LightningRpc("/Users/rpickhardt/.lightning/lightning-rpc") 
        self.send_response(200)
        
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        message = ""
        if self.path == "/":
            message = self.__show_start_page()
        else:
            message = self.__show_rankings_page()
                    
        self.wfile.write(bytes(message, "utf8"))
        return
    
    def do_POST(self):
        global rpc_interface
        if rpc_interface == None:
            rpc_interface = LightningRpc("/Users/rpickhardt/.lightning/lightning-rpc") 
        self.send_response(200)
        
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        length = int(self.headers.get('content-length'))
        field_data = self.rfile.read(length)
        if self.path=="/payment_requests":
            amount = json.loads(field_data.decode("utf-8"))["amount"]
            label = "satoshis-tennis-{}".format(time.time())
            message = rpc_interface.invoice(amount*1000, label , label, fallbacks=["3MXqbMwf457U4Jaw35WnJdnL99mq7Q8oQQ"])["bolt11"]
            rpc_interface.waitinvoice(label)
            self.wfile.write(bytes(message, "utf8"))
            return
        fields = parse_qs(field_data)
        print(fields)
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
        
        #l = LightningRpc("/Users/rpickhardt/.lightning/lightning-rpc")
        now = time.time()
        invoice = rpc_interface.invoice(amount,"lbl{}".format(now),"rene-pickhardts-lightning-video-votes-{}".format(now))
        
        message += "Each vote costs 250 Satoshi please pay: " + str(amount/1000) + " via the following invoice: <br>"
        message +="<h1>You need to pay the invoice in order to look up the results</h1>"
        message +=""" Look up <a href="/"""+invoice["payment_hash"]+"""\">the results </a> (only possible after you paid your invoice) """
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
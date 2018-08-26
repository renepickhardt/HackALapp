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
        #FIXME: check for expired invoices and generate a new

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
            payment_hash= invoice["payment_hash"]
            if status != "paid":
                continue
            
            try: 
                with open("potentialVotes/"+payment_hash+".json","r") as infile:
                    voting_dict = json.load(infile)
                    votes = voting_dict["v"]
                    
                    for vote in votes:
                        if vote in count_votes:
                            count_votes[vote] +=1
                        else:
                            count_votes[vote] = 1
            except:
                pass
        
        res = list(sorted(count_votes.items(), key=lambda x: x[1],reverse=True))
        return res
        
                        
    
    def __show_start_page(self):
        message = """<form method="post"><fieldset><legend>Which Videos would you like to have on my 
        <a href="https://www.youtube.com/channel/UCWmagvXbbOAS29CcLRP0FWg">Youtube Channel</a> and on
         <a href="https://en.wikiversity.org/wiki/Lightning_Network">Wikiversity</a>?</legend>"""
        #FIXME shuffle lines
        for hash_id, topic in topic_dict.items():
            message += """<div> <input type="checkbox" id=\"""" + hash_id + """\" name="votes"
               value=\"""" + hash_id + """\" /> <label for=\"""" + hash_id + """\"">""" + topic + "</label></div>"
        message += """</fieldset><div><button type="submit">Vote now!</button></div></form>"""
        return message
    
    def __show_rankings_page(self,payment_hash):
        message = ""
        try: 
            f = open("potentialVotes/"+payment_hash+".json","r")
            data = json.load(f)
            votes = data["v"]
            message = "<h1>You have voted for:</h1>"
            for vote in votes:
                message += topic_dict[vote] + "<br>"
        except:
            message = "Payment hash unknown. Please go to the <a href='/'>home page and cast your votes</a>"
            pass
        
        invoices = rpc_interface.listinvoices()["invoices"]
        for invoice in invoices:
            if invoice["payment_hash"] == payment_hash:
                if invoice["status"] == "paid":
                    message +="great you paid your fair share!"
                    message +="<h2>The current rankings of the poll are:</h2>"
                    message +="<ul>"
                    for key, count in self.__count_votes():
                        message += "<li>"+str(count)+":"+topic_dict[key]+"</li>"
                    message +="</ul>"
            
            else:
                message += self.__add__invoice_payment_string(invoice)
                
        return message

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        message = """<head><link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAEg0lEQVRYhbWWe2wURRzHv7O3e9u97e1dW/uAFmttSoqJsfioL4xtjbZNIJAKkmA0giJYTQSLqYoJIUq0kYImpgFRMTEQCWBAEttqbGssGFGEhKZoS9OcpfZFH/fY27vbvRn/aGsfcnd79Jx/9zfz+czMb36/JeXbViJRgwGwcgxVi9X71mSrBwkgvtWRWnZVFYa4CHP4RMJ5wvBUjlq2folvr5Ww5RM6d5bnoEeblxABBkCyMMvabN/a9UvU9wTC8kAQ+mUs6fBVHz8WafcJEaAMuM1mJG3N92y50xHaKRCWDgAenfutadB2xqAEHPmfBCgDcmXD+VrBRG2hor8ChmQAAEHg59GkQ3/6hOFo8AUJUAB5spG9rcC9p1DRnwabWcurk/bGQdspgyLq7hcksHKRuuzJbP/ebMmoBMMMhkA7N5r0WZdXmIgFj1uAAeAArFrkX7Exz1svWVgx2KwAAnh17mzjoNysM8CSSAEKQOEp90SmtvqZXG+dxLGCOXAAYQb1+yHpky6fMG4GblqAMiBDDIuvFrifuzsluNsCZN4ozqUKLcf7k5vCDDDJjy0QZkCmSO3bl7q335MSfP3fTJ8fB/iah6RPR4Oc18zdmxYoTg1mrctRdxU5g5vAYI0U51L51p+uS61xsKMLMABl6VrB1nxPnUOgq8EQsaBRYLx5UG4YCXJes3cfUYABYAwoy9CKX8r31CsCXTE/2eYPApAH0gKbC5XQsyb4gW8GbPsuu60dFjJPgDLAIVA8lqFVbLjVV68I9I5Y8CkB5/KUYFXsSAYAoXOj4kkGdACzBCgAh0CF6nzPhpJ07V0C5JiBz107VggZ/3FEev+SW2ybvip+eq5ToHL17Z6XH03X3iBAShxos37X2kaktxt6lKNug9OnE4oHJp9akSNYUpLhfweA1dQrNns6BPDoXOfRv5JrfhiWmtw6N6c/8FMxuB6yuNqGbUcAJMXiOgUqFjmDZQRwmoC3N/QoNS3D0nlC/tuceGCyZnd6rB2dHuumWBsKM6Bqsb/iLmewNOo5EVC3zp0+0KPUto5I3ZGKU3zNiAHpIrWXZ6nVXLQ8IQhdmhA/P35N3n1hXByMJhp3N3zkFq00VzZKo8B9F8bFD/Z3OfcPmShMpgUYgDSR2ssztRcsiNgPhn4fE3d91O34YjjIBRPaji0EWJftq8iV9bIbfdco6f7SZa/9bkg67TE4arYhmRIIM6DQrqc8nqm9aCGQ5/+EaGFy/nCvUnNmwNZOgchN42YFBAJUZqnldoE+PA/O+jW+8WS/bce3A7YrUz5xjZgClAGFiu58KC3wPBikWXDjisd65MNux85eP98fz67jEuA5oDLLv8YusJmuSOD7wyN8vK/bUedSeVM/nzclQBmwzK5nPJgW2Aw2WSF1RkYuT1j3HOhRDrr8fGAh8JgCPMdQkeVfpQj0XjBAZ6T3WJ/85on+5BNamIQXCo8qQAEsTTZS708NbASDNcTIxWN9yTu+6pNbDEbiTra4BQDAoBAApIzr3MVT/fKWr/+Wf00kHAD+AaHgvxZun7ynAAAAAElFTkSuQmCC" rel="icon" type="image/png"/></head>"""
        if self.path == "/":
            message += self.__show_start_page()
        else:
            if self.path != "/favicon.ico":
                message += self.__show_rankings_page(self.path[1:])
        
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
        
        message = """<head><link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAACXBIWXMAAAsTAAALEwEAmpwYAAAEg0lEQVRYhbWWe2wURRzHv7O3e9u97e1dW/uAFmttSoqJsfioL4xtjbZNIJAKkmA0giJYTQSLqYoJIUq0kYImpgFRMTEQCWBAEttqbGssGFGEhKZoS9OcpfZFH/fY27vbvRn/aGsfcnd79Jx/9zfz+czMb36/JeXbViJRgwGwcgxVi9X71mSrBwkgvtWRWnZVFYa4CHP4RMJ5wvBUjlq2folvr5Ww5RM6d5bnoEeblxABBkCyMMvabN/a9UvU9wTC8kAQ+mUs6fBVHz8WafcJEaAMuM1mJG3N92y50xHaKRCWDgAenfutadB2xqAEHPmfBCgDcmXD+VrBRG2hor8ChmQAAEHg59GkQ3/6hOFo8AUJUAB5spG9rcC9p1DRnwabWcurk/bGQdspgyLq7hcksHKRuuzJbP/ebMmoBMMMhkA7N5r0WZdXmIgFj1uAAeAArFrkX7Exz1svWVgx2KwAAnh17mzjoNysM8CSSAEKQOEp90SmtvqZXG+dxLGCOXAAYQb1+yHpky6fMG4GblqAMiBDDIuvFrifuzsluNsCZN4ozqUKLcf7k5vCDDDJjy0QZkCmSO3bl7q335MSfP3fTJ8fB/iah6RPR4Oc18zdmxYoTg1mrctRdxU5g5vAYI0U51L51p+uS61xsKMLMABl6VrB1nxPnUOgq8EQsaBRYLx5UG4YCXJes3cfUYABYAwoy9CKX8r31CsCXTE/2eYPApAH0gKbC5XQsyb4gW8GbPsuu60dFjJPgDLAIVA8lqFVbLjVV68I9I5Y8CkB5/KUYFXsSAYAoXOj4kkGdACzBCgAh0CF6nzPhpJ07V0C5JiBz107VggZ/3FEev+SW2ybvip+eq5ToHL17Z6XH03X3iBAShxos37X2kaktxt6lKNug9OnE4oHJp9akSNYUpLhfweA1dQrNns6BPDoXOfRv5JrfhiWmtw6N6c/8FMxuB6yuNqGbUcAJMXiOgUqFjmDZQRwmoC3N/QoNS3D0nlC/tuceGCyZnd6rB2dHuumWBsKM6Bqsb/iLmewNOo5EVC3zp0+0KPUto5I3ZGKU3zNiAHpIrWXZ6nVXLQ8IQhdmhA/P35N3n1hXByMJhp3N3zkFq00VzZKo8B9F8bFD/Z3OfcPmShMpgUYgDSR2ssztRcsiNgPhn4fE3d91O34YjjIBRPaji0EWJftq8iV9bIbfdco6f7SZa/9bkg67TE4arYhmRIIM6DQrqc8nqm9aCGQ5/+EaGFy/nCvUnNmwNZOgchN42YFBAJUZqnldoE+PA/O+jW+8WS/bce3A7YrUz5xjZgClAGFiu58KC3wPBikWXDjisd65MNux85eP98fz67jEuA5oDLLv8YusJmuSOD7wyN8vK/bUedSeVM/nzclQBmwzK5nPJgW2Aw2WSF1RkYuT1j3HOhRDrr8fGAh8JgCPMdQkeVfpQj0XjBAZ6T3WJ/85on+5BNamIQXCo8qQAEsTTZS708NbASDNcTIxWN9yTu+6pNbDEbiTra4BQDAoBAApIzr3MVT/fKWr/+Wf00kHAD+AaHgvxZun7ynAAAAAElFTkSuQmCC" rel="icon" type="image/png"/></head>"""
        if b"votes" not in fields:
            message += "malformed post request"
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

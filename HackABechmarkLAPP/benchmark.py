'''
Created on 24.09.2018

@author: rpickhardt

https://www.rene-pickhardt.de

License APCHE2

'''
import time

from lightning.lightning import LightningRpc
from matplotlib import pyplot as plt
rpc_path_node1 = "PATH_TO_FIRST/lightning-rpc"
rpc_path_node2 = "PATH_TO_SECOND/lightning-rpc"

if __name__ == '__main__':
    ln1 = LightningRpc(rpc_path_node1)
    ln2 = LightningRpc(rpc_path_node2)
    
    rounds = 1000
    start = time.time()
    times = []
    for i in range(rounds):
        s = time.time()
        invoice = ln1.invoice(500000000, str(time.time()), "description")
        bolt11 = invoice["bolt11"]
        ln2.pay(bolt11)
        
        invoice = ln2.invoice(500000000, str(time.time()), "description")
        bolt11 = invoice["bolt11"]
        ln1.pay(bolt11)
        e = time.time()
        times.append(e-s)
        print("\n\n\n\ncompleted pay round", i+1,
               "transfered BTC: {:4.2f}".format((i+1)*2*500000/100000000.),
               "tx per second: {:4.2f}".format((i+1)*2/(e-start)))
    end = time.time()
    diff = end-start
    
    label = ["       pay API","sendpay API"]
    fig, ax = plt.subplots()
    plt.title("Times for complete round trip payments on the lightning network using two local c-lightning clients")
    plt.hist(times,40, label=label[0]+" - {:4.2f} payments per second".format(2*len(times)/sum(times)))
    ax.legend()
    plt.xlabel("seconds")
    plt.ylabel("frequency")
    ax.grid()
    fig.text(0.90, 0.75, 'by Rene Pickhardt https://www.rene-pickhardt.de',
         fontsize=15, color='gray',
         ha='right', va='bottom', alpha=0.5)
    plt.show()
    plt.close() 
    
    node1_id = res = ln1.getinfo()["id"]
    node2_id = res = ln2.getinfo()["id"]
    route_to_ln1 = ln2.getroute(node1_id, "500000000", 1, 10)["route"]
    route_to_ln2 = ln1.getroute(node2_id, "500000000", 1, 10)["route"]
    start = time.time()
    times2= []
    for i in range(rounds):
        s = time.time()
        invoice = ln1.invoice(500000000, str(time.time()), "description")
        payment_hash = invoice["payment_hash"]        
        ln2.sendpay(route_to_ln1, payment_hash)
        
        invoice = ln2.invoice(500000000, str(time.time()), "description")
        payment_hash = invoice["payment_hash"]        
        ln1.sendpay(route_to_ln2, payment_hash)
        e = time.time()
        times2.append(e-s)
        print("\n\n\n\ncompleted sendpay round", i+1,
               "transfered BTC: {:4.2f}".format((i+1)*2*500000/100000000.),
               "tx per second: {:4.2f}".format((i+1)*2/(e-start)))
    end = time.time()
    print("pay api:",diff, 1000 // diff)
    print("sendpay api:", end-start, 1000// (end-start))
    
    label = ["       pay API","sendpay API"]
    fig, ax = plt.subplots()
    plt.title("Times for complete round trip payments on the lightning network using two local c-lightning clients")
    plt.hist(times,40, label=label[0]+" - {:4.2f} payments per second".format(2*len(times)/sum(times)))
    plt.hist(times2,40, label=label[1]+" - {:4.2f} payments per second".format(2*len(times2)/sum(times2)))
    ax.legend()
    plt.xlabel("seconds")
    plt.ylabel("frequency")
    ax.grid()
    fig.text(0.90, 0.7, 'by Rene Pickhardt https://www.rene-pickhardt.de',
         fontsize=15, color='gray',
         ha='right', va='bottom', alpha=0.5)
    plt.show()
    plt.close() 
    
    label = ["       pay API","sendpay API"]
    fig, ax = plt.subplots()
    plt.title("90-percentile of times for complete round trip payments on the lightning network using two local c-lightning clients")
    values = sorted(times)
    values = values[:int(rounds*0.9)]
    plt.hist(values,40, label=label[0]+" - {:4.2f} payments per second".format(2*len(values)/sum(values)))
    values = sorted(times2)
    values = values[:int(rounds*0.9)]
    plt.hist(values,40, label=label[1]+" - {:4.2f} payments per second".format(2*len(values)/sum(values)))
    ax.legend()
    plt.xlabel("seconds")
    plt.ylabel("frequency")
    ax.grid()
    fig.text(0.90, 0.7, 'by Rene Pickhardt https://www.rene-pickhardt.de',
         fontsize=15, color='gray',
         ha='right', va='bottom', alpha=0.5)
    plt.show()
    plt.close()
    
    print(times)
    print(times2)

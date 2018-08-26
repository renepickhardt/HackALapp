This is a short tutorial to create your own LAPP in Python on top of c-lightning

you will need `pip3 install pylightning qrcode[pil]` and then run: `python3.6 startServer.py`

Of course you need a [running c-lightning node](https://github.com/ElementsProject/lightning)

Also you find a [tutorial to create this LAPP on Youtube.](https://youtu.be/HXVDwRnU7_I)

My goal is to use this and other videos to create [teachning materials about the lightnign network on Wikiversity](https://en.wikiversity.org/wiki/Lightning_Network). Join me if you like!

Check the free class on wikiversity: https://en.wikiversity.org/wiki/Hack_A_Lapp:_Introduction_to_Bitcoins_Lightning_Network_App_Development/C-Lightning_with_python

Don't forget to change `rpc_interface = LightningRpc("/path/to/your/.lightning/lightning-rpc")` with the path in which your c-lighting node stores its state.

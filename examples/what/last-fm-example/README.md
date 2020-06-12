# Ink music stats

This repositary uses my [lastfm-user-data-api](https://github.com/hankhank10/lastfm-user-data-api) to pull the last played track and some music stats from last.fm and print them to an e-ink display, specifically the [Pimoroni inky what](https://shop.pimoroni.com/products/inky-what?variant=21214020436051) which has a github [here](https://github.com/pimoroni/inky)

![Example of what it looks like](https://user-images.githubusercontent.com/25515609/84536452-c6bd3b80-ace5-11ea-82b6-4c9f22ed3a6a.jpg)

## Installation

Purchase and install the Pimoroni inky wHAT on your Raspberry Pi.  Ensure that you have enabled I2C in ```raspi-config```

Install inky library with:

``` sudo pip install inky ```

Clone the ink-music-stats repo to your Raspberry Pi.

Edit the go_ink.py to set your preferences (or not - the defaults are fine).

Test the module works by entering ``` python3 go_ink.py ``` at the command line in the directory.

## Running at startup

Once you have it running right you can set it up to run at startup without your intervention.

There are a variety of ways to do this.  I like PM2 (which is really built for node.js but can also automate python):

``` sudo apt install npm
sudo npm install -g pm2
pm2 start ink-music-stats/go_ink.py --interpreter=python3 -- LASTFMUSERNAMETOCHECK
pm2 startup systemd
```

This will generate something which looks like
```sudo env PATH=$PATH:/usr/bin /usr/local/lib/node_modules/pm2/bin/pm2 startup systemd -u pi --hp /home/pi
```

Put this (or, rather, whatever your system generates) into the command line followed by

```
pm2 save
sudo reboot
```



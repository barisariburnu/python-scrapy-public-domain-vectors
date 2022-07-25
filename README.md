# Python Scrapy Public Domain Vectors

It has been developed using scrapy package for downloading content from publicdomainvectors.org in Python.

### Install 

1. Clone repository
    - `cd /home/ubuntu`
    - `git clone https://github.com/barisariburnu/python-scrapy-public-domain-vectors.git`

2. Change current directory
    - `cd /home/ubuntu/python-scrapy-public-domain-vectors`

3. Create virtual environment and install requirements into it
    - `python3 -m venv venv3`
    - `source venv3/bin/activate`
    - `pip install --upgrade pip`
    - `pip install -r requirements.txt`

4. Run
    - `python main.py`

5. Run alternatives
    - `scrapy crawl publicdomainvectors`

### Configuration for Send Message Services

1. Install and enable cron
    - `sudo apt install cron`
    - `sudo systemctl enable cron`

2. Edit crontab
    - `crontab -e`

3. Add to bottom line 
    - `* * 1 * * /home/ubuntu/python-scrapy-public-domain-vectors/main.py`

4. Save and exit.

### Note

At the moment, the `requirements.txt` is not necessary. The project doesn't
use any packages outside of the Python standard library. Eventually, I plan
to show some more advanced features that will use packages from PyPI.
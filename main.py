#!/usr/bin/env python
import sys

from src.client.client import Client

if __name__ == '__main__':
    client = Client()
    client.run()
    sys.exit()
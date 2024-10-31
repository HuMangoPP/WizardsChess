#!/usr/bin/env python
from src.client import Client


if __name__ == '__main__':
    client = Client(use_mgl=False)
    client.run()
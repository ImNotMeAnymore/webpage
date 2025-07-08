#!/usr/bin/env python3

import hashlib
import getpass
import secrets


def makenv(path:str=".env"):
	print("Creating new admin credentials!")
	print("="*30)
	with open(path,"w")as f:
		f.write("ME="+input("Enter admin username: ").strip())
		f.write("\nPWH="+hashlib.sha256(getpass.getpass("Enter admin password: ").encode()).hexdigest())
		f.write("KEY="+secrets.token_hex(32))

# ↓ all this bullshit for just this ↑

# [170 lines of AI generated bullshit were here once]
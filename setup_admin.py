#!/usr/bin/env python3

import hashlib
import getpass
import secrets


def makenv(path:str=".env"):
	print("Creating new admin credentials!")
	print("="*30)
	with open(path,"w")as f:
		print("ME="+input("Enter admin username: ").strip(),file=f)
		print("PWH="+hashlib.sha256(getpass.getpass("Enter admin password: ").encode()).hexdigest(), file=f)
		print("KEY="+secrets.token_hex(128), file=f)
		print("PORT="+str(15498), file=f)

if __name__ == "__main__": makenv()

# ↓ all this bullshit for just this ↑

# [170 lines of AI generated bullshit were here once]
# app/db/session.py
from prisma import Prisma

# Initialize Prisma client
db = Prisma(auto_register=True)


TOKEN = None

with open("token.txt") as f:
    TOKEN = f.read().strip()

if __name__ == '__main__':
   print(TOKEN)


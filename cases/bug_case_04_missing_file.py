profile_name = open("username.txt", "r", encoding="utf-8").read().strip()
print(profile_name or "Guest")
